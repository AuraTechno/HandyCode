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
    print_colored, print_header, print_success,
    print_error, print_warning, print_info, print_logo
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

        # Буфер для потокового создания файлов
        self.stream_buffer = ""
        self.current_file_action = None

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

            context += f"\nFile contents:\n"
            total = 0
            for file in files:
                if total > 50000:
                    break
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (truncated)"
                    rel_path = file.relative_to(self.project_path)
                    context += f"\n=== {rel_path} ===\n{content}\n"
                    total += len(content)
                except:
                    pass

        except Exception as e:
            context += f"\nError: {e}\n"

        return context

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _get_system_prompt(self):
        return """You are HandyCode - an AI assistant for coding. You can create, modify, delete files and run commands.

CRITICAL: You MUST complete ALL actions in ONE response. If user asks to create AND run a project, do BOTH in the same response.

FILE FORMAT - use EXACTLY:
[[CREATE:filename]]
code here
[[END]]

[[MODIFY:filename]]
new code here
[[END]]

[[DELETE:filename]]
[[READ:filename]]
[[LIST:directory/]]
[[EXEC:command]]

RULES:
1. CREATE and EXEC in SAME response - create files AND run them together
2. Always use [[END]] to close files
3. NEVER put comments inside [[CREATE]]...[[END]] blocks
4. Put explanations BEFORE [[CREATE]] blocks, not inside
5. When user asks to create and run - do both immediately
6. Files create automatically, commands need confirmation

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
            print("\n\nPress Ctrl+C again to exit")
        else:
            os._exit(0)

    def reset_interrupt(self):
        self._interrupt_count = 0

    def _process_stream_chunk(self, chunk):
        """Обрабатывает кусок потокового ответа, создавая файлы на лету"""
        self.stream_buffer += chunk

        # Ищем [[CREATE:...]]...[[END]]
        while True:
            # Ищем начало CREATE
            create_match = re.search(r'\[\[CREATE:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if create_match:
                path = create_match.group(1).strip()
                content = create_match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)

                if content and self.security.is_safe_path(path):
                    self.file_manager.create_file(path, content)
                    self.stats["files_created"].append(path)
                    lines = content.count('\n') + 1
                    print(f"\n  ✅ Created: {path} ({lines} lines)")

                # Удаляем обработанный блок из буфера
                self.stream_buffer = self.stream_buffer[create_match.end():]
            else:
                break

        # Ищем [[MODIFY:...]]...[[END]]
        while True:
            modify_match = re.search(r'\[\[MODIFY:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if modify_match:
                path = modify_match.group(1).strip()
                content = modify_match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)

                if content and self.security.is_safe_path(path):
                    self.file_manager.modify_file(path, content)
                    self.stats["files_modified"].append(path)
                    lines = content.count('\n') + 1
                    print(f"\n  ✏️ Modified: {path} ({lines} lines)")

                self.stream_buffer = self.stream_buffer[modify_match.end():]
            else:
                break

        # Ищем [[EXEC:...]]
        while True:
            exec_match = re.search(r'\[\[EXEC:(.+?)\]\]', self.stream_buffer)
            if exec_match:
                command = exec_match.group(1).strip()
                self.pending_commands.append(command)
                self.stream_buffer = self.stream_buffer[exec_match.end():]
            else:
                break

    def _make_request_streaming(self, data):
        """Потоковый запрос с обработкой файлов в реальном времени"""
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
            in_code_block = False

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

                                    # Определяем, нужно ли показывать
                                    if '[[CREATE:' in full_response[-100:] or '[[MODIFY:' in full_response[-100:]:
                                        in_code_block = True

                                    if '[[END]]' in full_response[-20:]:
                                        in_code_block = False

                                    # Показываем только текст вне кодовых блоков
                                    if not in_code_block:
                                        # Не показываем маркеры
                                        display = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace('[[END]]', '').replace('[[EXEC:', '')
                                        if display.strip():
                                            print(display, end="", flush=True)

                                    # Обрабатываем буфер для создания файлов
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
            in_code_block = False

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

                                    if '[[CREATE:' in full_response[-100:] or '[[MODIFY:' in full_response[-100:]:
                                        in_code_block = True

                                    if '[[END]]' in full_response[-20:]:
                                        in_code_block = False

                                    if not in_code_block:
                                        display = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace('[[END]]', '').replace('[[EXEC:', '')
                                        if display.strip():
                                            print(display, end="", flush=True)

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
            print_info(f"\nDEEPSEEK:")
            response = self._make_request_streaming(payload)

            if response:
                self.conversation_history.append({"role": "assistant", "content": response})

                # Выполняем оставшиеся команды
                if self.pending_commands:
                    print_header("\nCOMMANDS")
                    for i, cmd in enumerate(self.pending_commands, 1):
                        print(f"  {i}. {cmd}")

                    if self.auto_approve:
                        choice = 'A'
                    else:
                        print("\n[A] Execute all  [S] Skip  [C] Cancel")
                        choice = input("> ").strip().upper()

                    if choice == 'A':
                        for cmd in self.pending_commands:
                            if self.security.is_safe_command(cmd):
                                self.file_manager.execute_command(cmd)
                                self.stats["commands_executed"].append(cmd)
                    elif choice == 'S':
                        print_warning("Skipped")

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _handle_command(self, user_input):
        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd in ['/help', '/h']:
            print("""
COMMANDS:
  /help          Show help
  /scan          Scan project
  /models        List models
  /model NAME    Switch model
  /clear         Clear history
  /save          Save session
  /stats         Statistics
  /exit          Exit
            """)
        elif cmd in ['/scan', '/s']:
            print(self.file_manager.scan_project())
        elif cmd in ['/models', '/m']:
            for name in MODELS:
                print(f"  {name}")
        elif cmd in ['/model'] and len(parts) > 1:
            model_name = parts[1]
            if model_name in MODELS:
                self.current_model = MODELS[model_name]
                self.model_settings = get_model_settings(self.current_model)
                print_success(f"Switched to: {model_name}")
        elif cmd in ['/clear', '/c']:
            self.conversation_history = [self.conversation_history[0]]
            print_success("Cleared")
        elif cmd in ['/stats']:
            print(f"Messages: {self.stats['messages_sent']}")
            print(f"Created: {len(self.stats['files_created'])}")
            print(f"Modified: {len(self.stats['files_modified'])}")
            print(f"Deleted: {len(self.stats['files_deleted'])}")
            print(f"Commands: {len(self.stats['commands_executed'])}")
        elif cmd in ['/exit', '/q']:
            os._exit(0)
        return ""

    def execute_command(self, command):
        self.send_message(command)

    def run(self):
        print_logo()
        print()
        print_info(f"Project: {self.project_path}")
        print_info(f"Model: {self.current_model}")
        print_info("Files: auto-create in real-time | Commands: confirmation required")
        print_info("/help for commands\n")

        while True:
            try:
                self.reset_interrupt()
                user_input = input("> ").strip()
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break