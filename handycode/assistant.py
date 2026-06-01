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
        return """You are HandyCode - a powerful AI assistant for file operations and coding.

FILE OPERATIONS - USE EXACT FORMAT:
To create a file, use [[CREATE:path/to/file]] followed by the complete file content on the next lines, then [[END]] to mark end of file:
[[CREATE:path/to/file.py]]
import os

def main():
    print("Hello World")

if __name__ == "__main__":
    main()
[[END]]

To modify a file, use [[MODIFY:path/to/file]] followed by the complete new content, then [[END]]:
[[MODIFY:path/to/file.py]]
new complete content here
[[END]]

To delete a file:
[[DELETE:path/to/file.py]]

To read a file:
[[READ:path/to/file.py]]

To list directory:
[[LIST:path/]]

To run a command (requires confirmation):
[[EXEC:python script.py]]

CRITICAL RULES:
1. ALWAYS put [[END]] after file content for CREATE and MODIFY
2. Show COMPLETE file content between [[CREATE/MODIFY:...]] and [[END]]
3. NEVER include comments or explanations INSIDE the file content
4. Only the actual code goes between [[CREATE:...]] and [[END]]
5. Explain what you're doing BEFORE the [[CREATE:...]] block
6. Do NOT put your explanations inside [[CREATE:...]] [[END]] blocks
7. Files are created/modified automatically without asking
8. Commands (EXEC) require user confirmation

Example of CORRECT format:
I'll create a Python script for you.

[[CREATE:hello.py]]
print("Hello World")
[[END]]

Now you can run it with: python hello.py

Example of WRONG format (DON'T DO THIS):
[[CREATE:hello.py]]
Here's your file:
print("Hello World")
This file prints hello
[[END]]

Respond in Russian. Write code in English."""

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

    def _make_request_streaming(self, data):
        if HAS_REQUESTS:
            return self._make_request_streaming_requests(data)
        else:
            return self._make_request_urllib(data)

    def _make_request_streaming_requests(self, data):
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
                                    # Показываем только если это не внутри кодового блока
                                    print(content, end="", flush=True)
                                    full_response += content
                        except:
                            continue
            print()
            return full_response
        except Exception as e:
            print_error(f"API Error: {e}")
            return ""

    def _make_request_urllib(self, data):
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
                                    print(content, end="", flush=True)
                                    full_response += content
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

                actions = self._parse_actions(response)
                if actions:
                    self._execute_actions(actions)

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _parse_actions(self, response):
        actions = []

        # CREATE с [[END]]
        create_pattern = r'\[\[CREATE:(.+?)\]\](.*?)\[\[END\]\]'
        for match in re.finditer(create_pattern, response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            # Убираем маркеры кода если есть
            content = re.sub(r'^```[\w]*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            if content:
                actions.append({'type': 'create', 'path': path, 'content': content})

        # CREATE без [[END]] (старый формат, берём до следующего [[ или конца)
        if not any(a['type'] == 'create' for a in actions):
            old_create = r'\[\[CREATE:(.+?)\]\](.*?)(?=\[\[|$)'
            for match in re.finditer(old_create, response, re.DOTALL):
                path = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
                # Убираем явно не-кодовые строки
                lines = content.split('\n')
                clean_lines = []
                for line in lines:
                    if not line.startswith('Here') and not line.startswith('This file') and not line.startswith('Now you'):
                        clean_lines.append(line)
                content = '\n'.join(clean_lines).strip()
                if content:
                    actions.append({'type': 'create', 'path': path, 'content': content})

        # MODIFY с [[END]]
        modify_pattern = r'\[\[MODIFY:(.+?)\]\](.*?)\[\[END\]\]'
        for match in re.finditer(modify_pattern, response, re.DOTALL):
            path = match.group(1).strip()
            content = match.group(2).strip()
            content = re.sub(r'^```[\w]*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            if content:
                actions.append({'type': 'modify', 'path': path, 'content': content})

        # DELETE
        for match in re.finditer(r'\[\[DELETE:(.+?)\]\]', response):
            actions.append({'type': 'delete', 'path': match.group(1).strip()})

        # READ
        for match in re.finditer(r'\[\[READ:(.+?)\]\]', response):
            actions.append({'type': 'read', 'path': match.group(1).strip()})

        # LIST
        for match in re.finditer(r'\[\[LIST:(.+?)\]\]', response):
            actions.append({'type': 'list', 'path': match.group(1).strip()})

        # EXEC
        for match in re.finditer(r'\[\[EXEC:(.+?)\]\]', response):
            actions.append({'type': 'exec', 'command': match.group(1).strip()})

        return actions

    def _execute_actions(self, actions):
        if not actions:
            return

        file_actions = [a for a in actions if a['type'] in ['create', 'modify', 'delete', 'read', 'list']]
        exec_actions = [a for a in actions if a['type'] == 'exec']

        # Файловые операции - автоматически, показываем только информацию
        if file_actions:
            print_header("\nFILE OPERATIONS")
            for i, action in enumerate(file_actions, 1):
                if action['type'] == 'create':
                    lines = action['content'].count('\n') + 1
                    print(f"  {i}. Created: {action['path']} ({lines} lines)")
                elif action['type'] == 'modify':
                    lines = action['content'].count('\n') + 1
                    print(f"  {i}. Modified: {action['path']} ({lines} lines)")
                elif action['type'] == 'delete':
                    print(f"  {i}. Deleted: {action['path']}")
                elif action['type'] == 'read':
                    print(f"  {i}. Read: {action['path']}")
                elif action['type'] == 'list':
                    print(f"  {i}. Listed: {action['path']}")

            for action in file_actions:
                self._execute_action(action)

        # Команды - требуют подтверждения
        if exec_actions:
            print_header("\nCOMMANDS (confirmation required)")
            for i, action in enumerate(exec_actions, 1):
                print(f"  {i}. {action['command']}")

            if self.auto_approve:
                choice = 'A'
            else:
                print("\n[A] Execute all  [S] Skip  [C] Cancel")
                choice = input("> ").strip().upper()

            if choice == 'A':
                for action in exec_actions:
                    self._execute_action(action)
            elif choice == 'S':
                print_warning("Skipped")
            elif choice == 'C':
                print_warning("Cancelled")

    def _execute_action(self, action):
        try:
            if action['type'] == 'create':
                if self.security.is_safe_path(action['path']):
                    self.file_manager.create_file(action['path'], action['content'])
                    self.stats["files_created"].append(action['path'])

            elif action['type'] == 'modify':
                if self.security.is_safe_path(action['path']):
                    self.file_manager.modify_file(action['path'], action['content'])
                    self.stats["files_modified"].append(action['path'])

            elif action['type'] == 'delete':
                if self.security.is_safe_path(action['path']):
                    self.file_manager.delete_file(action['path'])
                    self.stats["files_deleted"].append(action['path'])

            elif action['type'] == 'read':
                if self.security.is_safe_path(action['path']):
                    self.file_manager.read_file(action['path'])
                    self.stats["files_read"].append(action['path'])

            elif action['type'] == 'list':
                self.file_manager.list_directory(action['path'])

            elif action['type'] == 'exec':
                if self.security.is_safe_command(action['command']):
                    self.file_manager.execute_command(action['command'])
                    self.stats["commands_executed"].append(action['command'])

        except Exception as e:
            print_error(f"Action failed: {e}")

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
        print_info("Files: auto | Commands: confirmation required")
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