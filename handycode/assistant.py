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
    Colors, Theme, colorize, print_colored, print_header, print_success,
    print_error, print_warning, print_info, print_logo,
    print_divider, print_file_action, print_status, print_section, print_box,
    Spinner, print_package_status
)


def interactive_confirm(commands):
    """Интерактивное меню выбора команд"""
    if not commands:
        return []

    if os.name == 'nt':
        import msvcrt
        def get_key():
            key = msvcrt.getch()
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H': return 'up'
                if key == b'P': return 'down'
            if key == b'\r': return 'enter'
            if key == b' ': return 'space'
            if key in [b'a', b'A']: return 'a'
            if key in [b's', b'S']: return 's'
            if key in [b'c', b'C']: return 'c'
            if key == b'\x1b': return 'escape'
            return key.decode('utf-8', errors='ignore')
    else:
        import tty, termios
        def get_key():
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                key = sys.stdin.read(1)
                if key == '\x1b':
                    key += sys.stdin.read(2)
                    if key == '\x1b[A': return 'up'
                    if key == '\x1b[B': return 'down'
                    return 'escape'
                if key == '\r': return 'enter'
                if key == ' ': return 'space'
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    selected = [True] * len(commands)
    current = 0

    def render():
        print(f"\033[{len(commands) + 4}A\033[J", end="")
        print()
        print(colorize("  ⚡ Команды для выполнения:", Theme.HIGHLIGHT + Colors.BOLD))
        print(colorize("  ─────────────────────────────────────────────────", Theme.MUTED))
        for i, cmd in enumerate(commands):
            prefix = colorize("  ›", Theme.PRIMARY + Colors.BOLD) if i == current else "   "
            checkbox = colorize("◉", Theme.SUCCESS) if selected[i] else colorize("○", Theme.MUTED)
            cmd_color = Theme.SUCCESS if selected[i] else Theme.MUTED
            print(f"{prefix} {checkbox} {colorize(cmd, cmd_color)}")
        print()
        print(colorize("  ↑↓ Навигация  ПРОБЕЛ Выбрать  A Все  S Пропустить  ENTER Подтвердить  C Отмена", Theme.MUTED))

    for _ in range(len(commands) + 5):
        print()
    render()

    while True:
        key = get_key()
        if key == 'up':
            current = (current - 1) % len(commands)
            render()
        elif key == 'down':
            current = (current + 1) % len(commands)
            render()
        elif key == 'space':
            selected[current] = not selected[current]
            render()
        elif key in ['a', 'A']:
            selected = [True] * len(commands)
            render()
        elif key in ['s', 'S']:
            selected = [False] * len(commands)
            render()
        elif key in ['c', 'C', 'escape']:
            return []
        elif key == 'enter':
            print()
            return [cmd for cmd, sel in zip(commands, selected) if sel]


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

        # Получаем список установленных пакетов
        self.installed_packages = self.file_manager.get_installed_packages()

        project_context = self._build_project_context()

        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt() + project_context}
        ]
        self.stats = {
            "messages_sent": 0, "files_created": [], "files_modified": [],
            "files_deleted": [], "files_read": [], "commands_executed": [],
            "start_time": datetime.now()
        }
        self.stream_buffer = ""
        self.pending_commands = []
        self.command_results = []  # Результаты выполнения команд
        self._setup_readline()
        signal.signal(signal.SIGINT, self._signal_handler)
        self._interrupt_count = 0

    def _build_project_context(self):
        context = f"\n\n=== CURRENT PROJECT ===\nDirectory: {self.project_path}\n"
        context += f"\n=== INSTALLED PACKAGES ===\n"
        if self.installed_packages:
            context += ", ".join(self.installed_packages[:50])
            if len(self.installed_packages) > 50:
                context += f"\n... and {len(self.installed_packages) - 50} more"
        else:
            context += "No packages detected"

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
            context += f"\n\n=== PROJECT FILES ({len(files)}) ===\n"
            for file in files:
                try:
                    rel_path = file.relative_to(self.project_path)
                    size = file.stat().st_size
                    context += f"  {rel_path} ({self._format_size(size)})\n"
                except: pass

            context += f"\n=== FILE CONTENTS ===\n"
            total = 0
            for file in files:
                if total > 50000: break
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 3000:
                        content = content[:3000] + "\n... (truncated)"
                    rel_path = file.relative_to(self.project_path)
                    context += f"\n=== {rel_path} ===\n{content}\n"
                    total += len(content)
                except: pass
        except: pass
        return context

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _get_system_prompt(self):
        return """You are HandyCode - AI coding assistant.

CAPABILITIES:
- Create, modify, delete files
- Run shell commands
- Install Python packages via pip
- Analyze code and errors
- See installed packages and project files

PACKAGE MANAGEMENT:
- Check INSTALLED PACKAGES section before suggesting imports
- If a package is needed but not installed, use [[INSTALL:package_name]]
- Example: [[INSTALL:fastapi]] [[INSTALL:uvicorn]]

FILE FORMAT:
[[CREATE:path/file.py]]
code here
[[END]]

[[MODIFY:path/file.py]]
new code here
[[END]]

[[DELETE:path/file.py]]
[[READ:path/file.py]]
[[LIST:directory/]]
[[EXEC:command]]
[[INSTALL:package_name]]

CRITICAL RULES:
1. ALWAYS check if required packages are installed before using them
2. Install missing packages with [[INSTALL:...]]
3. CREATE files + INSTALL packages + EXEC commands in ONE response
4. Use [[END]] to close file blocks
5. NO comments or explanations inside [[CREATE]]...[[END]] - ONLY CODE
6. Put ALL explanations BEFORE [[CREATE]] blocks
7. After EXEC, I will show you any errors

ERROR HANDLING:
- After running commands, I'll show you the output
- If there are errors, I'll show them to you
- You can then fix the files and re-run

Speak Russian. Write code in English. Code ONLY inside [[CREATE]]...[[END]]."""

    def _setup_readline(self):
        if not HAS_READLINE: return
        try:
            histfile = os.path.join(os.path.expanduser("~"), ".handycode", "history")
            os.makedirs(os.path.dirname(histfile), exist_ok=True)
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
            atexit.register(readline.write_history_file, histfile)
        except: pass

    def _signal_handler(self, sig, frame):
        self._interrupt_count += 1
        if self._interrupt_count == 1:
            print("\n\n  ⚠ Нажмите Ctrl+C ещё раз для выхода")
        else:
            os._exit(0)

    def reset_interrupt(self): self._interrupt_count = 0

    def _process_stream_chunk(self, chunk):
        self.stream_buffer += chunk

        # CREATE с анимацией
        while True:
            match = re.search(r'\[\[CREATE:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if match:
                path = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
                if content and self.security.is_safe_path(path):
                    spinner = Spinner(f"Создание {path}")
                    spinner.start()
                    self.file_manager.create_file(path, content)
                    spinner.stop(f"  ✔ {path} ({content.count(chr(10))+1} строк)")
                    self.stats["files_created"].append(path)
                self.stream_buffer = self.stream_buffer[match.end():]
            else: break

        # MODIFY
        while True:
            match = re.search(r'\[\[MODIFY:(.+?)\]\](.*?)\[\[END\]\]', self.stream_buffer, re.DOTALL)
            if match:
                path = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
                if content and self.security.is_safe_path(path):
                    spinner = Spinner(f"Изменение {path}")
                    spinner.start()
                    self.file_manager.modify_file(path, content)
                    spinner.stop(f"  ✎ {path} ({content.count(chr(10))+1} строк)")
                    self.stats["files_modified"].append(path)
                self.stream_buffer = self.stream_buffer[match.end():]
            else: break

        # INSTALL
        while True:
            match = re.search(r'\[\[INSTALL:(.+?)\]\]', self.stream_buffer)
            if match:
                package = match.group(1).strip()
                print_status(f"Установка пакета: {package}")
                self.file_manager.install_package(package)
                self.stream_buffer = self.stream_buffer[match.end():]
            else: break

        # EXEC
        while True:
            match = re.search(r'\[\[EXEC:(.+?)\]\]', self.stream_buffer)
            if match:
                self.pending_commands.append(match.group(1).strip())
                self.stream_buffer = self.stream_buffer[match.end():]
            else: break

    def _make_request_streaming(self, data):
        self.stream_buffer = ""
        self.pending_commands = []
        if HAS_REQUESTS:
            return self._stream_requests(data)
        else:
            return self._stream_urllib(data)

    def _stream_requests(self, data):
        try:
            response = requests.post(self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json={**data, "stream": True}, timeout=120, stream=True)
            response.raise_for_status()
            full_response = ""
            in_code = False
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]': break
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
                                        clean = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace('[[END]]', '').replace('[[EXEC:', '').replace('[[INSTALL:', '').replace(']]', '')
                                        if clean.strip():
                                            print(clean, end="", flush=True)
                                    self._process_stream_chunk(content)
                        except: continue
            print()
            return full_response
        except Exception as e:
            print_error(f"API Error: {e}")
            return ""

    def _stream_urllib(self, data):
        try:
            json_data = json.dumps({**data, "stream": True}).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=json_data,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"}, method='POST')
            ctx = ssl.create_default_context()
            full_response = ""
            in_code = False
            with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
                for line in resp:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]': break
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
                                        clean = content.replace('[[CREATE:', '').replace('[[MODIFY:', '').replace('[[END]]', '').replace('[[EXEC:', '').replace('[[INSTALL:', '').replace(']]', '')
                                        if clean.strip():
                                            print(clean, end="", flush=True)
                                    self._process_stream_chunk(content)
                        except: continue
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
            print_divider("─", 60, Theme.MUTED)
            print(colorize("  HandyCode", Theme.PRIMARY + Colors.BOLD), end="")
            print(colorize("  ●  ответ", Theme.MUTED))
            print_divider("─", 60, Theme.MUTED)

            response = self._make_request_streaming(payload)

            if response:
                self.conversation_history.append({"role": "assistant", "content": response})

                if self.pending_commands:
                    if self.auto_approve:
                        selected_commands = self.pending_commands
                    else:
                        selected_commands = interactive_confirm(self.pending_commands)

                    if selected_commands:
                        print()
                        print_section("⚡ Выполнение команд", [])
                        for cmd in selected_commands:
                            if self.security.is_safe_command(cmd):
                                print_status(f"Выполняется: {cmd}")
                                success, output = self.file_manager.execute_command(cmd)
                                self.stats["commands_executed"].append(cmd)
                                self.command_results.append({
                                    "command": cmd,
                                    "success": success,
                                    "output": output
                                })

                        # Показываем ошибки
                        errors = [r for r in self.command_results if not r['success']]
                        if errors:
                            print()
                            print_section("❌ Обнаружены ошибки", [])
                            for err in errors:
                                print(colorize(f"  Команда: {err['command']}", Theme.ERROR))
                                if err['output']:
                                    for line in err['output'].strip().split('\n')[:5]:
                                        print(colorize(f"    {line}", Theme.MUTED))
                            print()
                            print_info("Вы можете попросить меня исправить ошибки")
                    else:
                        print_warning("Команды пропущены")

                self.stats["messages_sent"] += 1
                return response
        except Exception as e:
            return print_error(f"Error: {e}")

    def _handle_command(self, user_input):
        parts = user_input.split()
        cmd = parts[0].lower()
        if cmd in ['/help', '/h']:
            print_box([
                "/help      Справка",
                "/scan      Показать проект",
                "/packages  Показать установленные пакеты",
                "/models    Модели",
                "/model N   Сменить модель",
                "/clear     Очистить историю",
                "/save      Сохранить сессию",
                "/stats     Статистика",
                "/exit      Выход"
            ], Theme.PRIMARY)
        elif cmd in ['/scan', '/s']:
            print(self.file_manager.scan_project())
        elif cmd in ['/packages', '/pkg']:
            packages = self.file_manager.get_installed_packages()
            print_section("📦 Установленные пакеты", packages[:20])
            if len(packages) > 20:
                print(colorize(f"  ... и ещё {len(packages) - 20}", Theme.MUTED))
        elif cmd in ['/models', '/m']:
            lines = []
            for name, mid in MODELS.items():
                mark = " (текущая)" if mid == self.current_model else ""
                lines.append(f"{name}{mark}")
            print_section("🤖 Модели", lines)
        elif cmd in ['/model'] and len(parts) > 1:
            name = parts[1]
            if name in MODELS:
                self.current_model = MODELS[name]
                self.model_settings = get_model_settings(self.current_model)
                print_success(f"Модель изменена на {name}")
        elif cmd in ['/clear', '/c']:
            self.conversation_history = [self.conversation_history[0]]
            self.command_results = []
            print_success("История очищена")
        elif cmd in ['/save']:
            self.file_manager.save_session(self.conversation_history, self.current_model, self.stats)
        elif cmd in ['/stats']:
            print_box([
                f"Сообщений: {self.stats['messages_sent']}",
                f"Создано файлов: {len(self.stats['files_created'])}",
                f"Изменено: {len(self.stats['files_modified'])}",
                f"Удалено: {len(self.stats['files_deleted'])}",
                f"Команд выполнено: {len(self.stats['commands_executed'])}",
                f"Пакетов установлено: {len(self.installed_packages)}"
            ], Theme.SECONDARY)
        elif cmd in ['/exit', '/q']:
            print_success("До свидания!")
            os._exit(0)
        return ""

    def execute_command(self, command):
        self.send_message(command)

    def run(self):
        print_logo()
        print_divider("─", 60, Theme.MUTED)
        print(colorize(f"  📁 Проект: {self.project_path}", Theme.TEXT))
        print(colorize(f"  🤖 Модель: {self.current_model}", Theme.TEXT))
        print(colorize(f"  📦 Пакетов: {len(self.installed_packages)}", Theme.TEXT))
        print(colorize(f"  {Theme.MUTED}/help для команд{Colors.RESET}", Theme.MUTED))
        print_divider("─", 60, Theme.MUTED)
        print()
        while True:
            try:
                self.reset_interrupt()
                user_input = input(colorize("  ❯ ", Theme.PRIMARY + Colors.BOLD)).strip()
                if user_input:
                    self.send_message(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break