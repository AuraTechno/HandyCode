"""
Основной класс ассистента HandyCode
"""

import os
import re
import json
import sys
import atexit
import signal
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    import readline

    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error
    import ssl

from handycode.config import Config
from handycode.models import MODELS, get_model_settings
from handycode.file_manager import FileManager
from handycode.security import SecurityChecker
from handycode.utils import (
    Colors, print_colored, print_header, print_success,
    print_error, print_warning, print_info, print_logo,
    print_divider, print_file_action, print_command, print_status
)


class HandyCode:
    def __init__(self, project_path, model="deepseek", auto_approve=False, config=None):
        self.project_path = project_path
        self.auto_approve = auto_approve
        self.config = config or Config()

        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError("API key not found")

        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.current_model = MODELS.get(model, MODELS["deepseek"])
        self.model_settings = get_model_settings(self.current_model)

        self.file_manager = FileManager(self.project_path)
        self.security = SecurityChecker(self.project_path)

        project_context = self._build_project_context()

        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt() + project_context}
        ]

        self.stats = {
            "messages_sent": 0,
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "files_read": [],
            "commands_executed": [],
            "start_time": datetime.now()
        }

        self.stream_buffer = ""
        self.pending_commands = []

        self._setup_readline()
        signal.signal(signal.SIGINT, self._signal_handler)
        self._interrupt_count = 0

    def _build_project_context(self):
        context = f"\n\n=== CURRENT PROJECT ===\n"
        context += f"Directory: {self.project_path}\n"
        try:
            all_files = []
            for ext in self.file_manager.allowed_extensions:
                all_files.extend(self.project_path.rglob(f"*{ext}"))
            all_files.extend(self.project_path.rglob("*"))

            seen = set()
            files = []
            for f in sorted(all_files):
                if f.is_file() and f not in seen:
                    rel = str(f.relative_to(self.project_path))
                    if not any(ex in f.parts for ex in self.file_manager.excluded_dirs):
                        if not any(rel.startswith(ex) for ex in self.file_manager.excluded_dirs):
                            files.append(f)
                            seen.add(f)

            context += f"\nFiles ({len(files)}):\n"
            for file in files:
                try:
                    rel_path = file.relative_to(self.project_path)
                    size = file.stat().st_size
                    context += f"  {rel_path} ({self._format_size(size)})\n"
                except:
                    pass
        except:
            pass
        return context

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _get_system_prompt(self):
        return """You are HandyCode - AI coding assistant. Create/modify/delete files and run commands.

    FORMAT:
    [[CREATE:path/file]]
    code here
    [[END]]

    [[MODIFY:path/file]]
    new code here
    [[END]]

    [[EXEC:command]]

    RULES:
    1. CREATE + EXEC in ONE response
    2. Use [[END]] after file content
    3. NO comments inside [[CREATE]]...[[END]]
    4. Explanations BEFORE [[CREATE]] blocks
    5. Files create automatically, commands need confirmation

    Speak Russian. Write code in English."""

    def _setup_readline(self):
        if not HAS_READLINE:
            return
        try:
            histfile = os.path.join(os.path.expanduser("~"), ".handycode", "history")
            os.makedirs(os.path.dirname(histfile), exist_ok=True)
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
            atexit.register(readline.write_history_file, histfile)
        except:
            pass

    def _signal_handler(self, sig, frame):
        self._interrupt_count += 1
        if self._interrupt_count == 1:
            print("\n\n  ⚠ Press Ctrl+C again to exit")
        else:
            os._exit(0)

    def reset_interrupt(self):
        self._interrupt_count = 0

    def _process_stream_chunk(self, chunk):
        self.stream_buffer += chunk

        # CREATE файлы в реальном времени
        while True:
            match = re.search(r'\[\[CREATE:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if match:
                path = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)

                if content and self.security.is_safe_path(path):
                    self.file_manager.create_file(path, content)
                    self.stats["files_created"].append(path)
                    lines = content.count('\n') + 1
                    print_file_action('create', path, f"({lines} lines)")

                self.stream_buffer = self.stream_buffer[match.end():]
            else:
                break

        # MODIFY файлы
        while True:
            match = re.search(r'\[\[MODIFY:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if match:
                path = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)

                if content and self.security.is_safe_path(path):
                    self.file_manager.modify_file(path, content)
                    self.stats["files_modified"].append(path)
                    lines = content.count('\n') + 1
                    print_file_action('modify', path, f"({lines} lines)")

                self.stream_buffer = self.stream_buffer[match.end():]
            else:
                break

        # EXEC команды
        while True:
            match = re.search(r'\[\[EXEC:(.+?)\]\]', self.stream_buffer)
            if match:
                self.pending_commands.append(match.group(1).strip())
                self.stream_buffer = self.stream_buffer[match.end():]
            else:
                break

    def _make_request_streaming(self, data):
        self.stream_buffer = ""
        self.pending_commands = []

        if HAS_REQUESTS:
            return self._stream_requests(data)
        else:
            return self._stream_urllib(data)

    def _stream_requests(self, data):
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={**data, "stream": True},
                timeout=120,
                stream=True
            )
            response.raise_for_status()

            full_response = ""
            in_code = False

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content

                                    if '[[CREATE:' in content or '[[MODIFY:' in content:
                                        in_code = True
                                    if '[[END]]' in content:
                                        in_code = False

                                    if not in_code:
                                        clean = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace(
                                            '[[END]]', '').replace('[[EXEC:', '').replace(']]', '')
                                        if clean.strip():
                                            print(clean, end="", flush=True)

                                    self._process_stream_chunk(content)
                        except:
                            continue

            print()
            return full_response
        except Exception as e:
            print_error(f"API Error: {e}")
            return ""

    def _stream_urllib(self, data):
        try:
            json_data = json.dumps({**data, "stream": True}).encode('utf-8')
            req = urllib.request.Request(
                self.api_url,
                data=json_data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                method='POST'
            )
            ctx = ssl.create_default_context()

            full_response = ""
            in_code = False

            with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content

                                    if '[[CREATE:' in content or '[[MODIFY:' in content:
                                        in_code = True
                                    if '[[END]]' in content:
                                        in_code = False

                                    if not in_code:
                                        clean = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace(
                                            '[[END]]', '').replace('[[EXEC:', '').replace(']]', '')
                                        if clean.strip():
                                            print(clean, end="", flush=True)

                                    self._process_stream_chunk(content)
                        except:
                            continue
                print()
                return full_response
        except Exception as e:
            print_error(f"Request error: {e}")
            return ""

    def send_message(self, user_input):
        if user_input.startswith('/'):
            return self._handle_command(user_input)

        self.conversation_history.append({"role": "user", "content": user_input})

        if len(self.conversation_history) > 20:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-19:]

        payload = {
            "model": self.current_model,
            "messages": self.conversation_history,
            "temperature": self.model_settings.get("temperature", 0.3),
            "max_tokens": self.model_settings.get("max_tokens", 8000),
        }

        try:
            print_divider("─", 60, Colors.BRIGHT_BLACK)
            print(colorize("  HandyCode", Colors.BRIGHT_CYAN + Colors.BOLD))
            print_divider("─", 60, Colors.BRIGHT_BLACK)

            response = self._make_request_streaming(payload)

            if response:
                self.conversation_history.append({"role": "assistant", "content": response})

                if self.pending_commands:
                    print()
                    print_divider("─", 60, Colors.BRIGHT_BLACK)
                    print(colorize("  ⚡ Commands (confirmation required):", Colors.YELLOW))
                    for i, cmd in enumerate(self.pending_commands, 1):
                        print_command(cmd, i)

                    if self.auto_approve:
                        choice = 'A'
                    else:
                        print()
                        print(colorize(f"  {Colors.BRIGHT_BLACK}[A] Execute all  [S] Skip  [C] Cancel{Colors.RESET}",
                                       Colors.BRIGHT_BLACK))
                        choice = input(colorize("  > ", Colors.WHITE)).strip().upper()

                    if choice == 'A':
                        print()
                        for cmd in self.pending_commands:
                            if self.security.is_safe_command(cmd):
                                print_status(f"Running: {cmd}")
                                self.file_manager.execute_command(cmd)
                                self.stats["commands_executed"].append(cmd)

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _handle_command(self, user_input):
        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd in ['/help', '/h']:
            print()
            print(colorize("  Commands:", Colors.BRIGHT_CYAN + Colors.BOLD))
            print_divider("─", 40, Colors.BRIGHT_BLACK)
            print(colorize("  /help          Show this help", Colors.WHITE))
            print(colorize("  /scan          Scan project files", Colors.WHITE))
            print(colorize("  /models        List AI models", Colors.WHITE))
            print(colorize("  /model NAME    Switch model", Colors.WHITE))
            print(colorize("  /clear         Clear chat history", Colors.WHITE))
            print(colorize("  /save          Save session to file", Colors.WHITE))
            print(colorize("  /stats         Show statistics", Colors.WHITE))
            print(colorize("  /exit          Exit program", Colors.WHITE))
            print()
        elif cmd in ['/scan', '/s']:
            print()
            print(colorize("  Project Files:", Colors.BRIGHT_CYAN + Colors.BOLD))
            print_divider("─", 40, Colors.BRIGHT_BLACK)
            print(self.file_manager.scan_project())
        elif cmd in ['/models', '/m']:
            print()
            print(colorize("  Available Models:", Colors.BRIGHT_CYAN + Colors.BOLD))
            print_divider("─", 40, Colors.BRIGHT_BLACK)
            for name in MODELS:
                marker = colorize(" (current)", Colors.GREEN) if MODELS[name] == self.current_model else ""
                print(f"  • {name}{marker}")
        elif cmd in ['/model'] and len(parts) > 1:
            model_name = parts[1]
            if model_name in MODELS:
                self.current_model = MODELS[model_name]
                self.model_settings = get_model_settings(self.current_model)
                print_success(f"Switched to {model_name}")
        elif cmd in ['/clear', '/c']:
            self.conversation_history = [self.conversation_history[0]]
            print_success("Chat history cleared")
        elif cmd in ['/stats']:
            print()
            print(colorize("  Session Stats:", Colors.BRIGHT_CYAN + Colors.BOLD))
            print_divider("─", 40, Colors.BRIGHT_BLACK)
            print(colorize(f"  Messages: {self.stats['messages_sent']}", Colors.WHITE))
            print(colorize(f"  Created: {len(self.stats['files_created'])} files", Colors.GREEN))
            print(colorize(f"  Modified: {len(self.stats['files_modified'])} files", Colors.YELLOW))
            print(colorize(f"  Deleted: {len(self.stats['files_deleted'])} files", Colors.RED))
            print(colorize(f"  Commands: {len(self.stats['commands_executed'])}", Colors.CYAN))
        elif cmd in ['/exit', '/q']:
            print_success("Goodbye!")
            os._exit(0)
        return ""

    def execute_command(self, command):
        self.send_message(command)

    def run(self):
        print_logo()
        print_divider("─", 60, Colors.BRIGHT_BLACK)
        print(colorize(f"  📁 Project: {self.project_path}", Colors.WHITE))
        print(colorize(f"  🤖 Model: {self.current_model}", Colors.WHITE))
        print(colorize(f"  {Colors.BRIGHT_BLACK}/help for commands{Colors.RESET}", Colors.BRIGHT_BLACK))
        print_divider("─", 60, Colors.BRIGHT_BLACK)
        print()

        while True:
            try:
                self.reset_interrupt()
                user_input = input(colorize("  ❯ ", Colors.BRIGHT_CYAN + Colors.BOLD)).strip()
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break


# Добавляем colorize как глобальную функцию для удобства
def colorize(text, color):
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def supports_color():
    from handycode.utils import supports_color as sc
    return sc()