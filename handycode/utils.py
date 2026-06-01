"""
Вспомогательные функции для HandyCode
"""

import sys
import os
import time
import threading

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

class Theme:
    PRIMARY = Colors.CYAN
    SECONDARY = Colors.BLUE
    ACCENT = Colors.MAGENTA
    SUCCESS = Colors.GREEN
    WARNING = Colors.YELLOW
    ERROR = Colors.RED
    TEXT = Colors.WHITE
    MUTED = Colors.BRIGHT_BLACK
    HIGHLIGHT = Colors.BRIGHT_WHITE

def supports_color():
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def colorize(text, color):
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text

def print_colored(text, color):
    print(colorize(text, color))

def print_header(text):
    print(colorize(text, Theme.PRIMARY + Colors.BOLD))

def print_success(text):
    print(colorize(f"  ✔ {text}", Theme.SUCCESS))

def print_error(text):
    print(colorize(f"  ✘ {text}", Theme.ERROR))
    return text

def print_warning(text):
    print(colorize(f"  ⚠ {text}", Theme.WARNING))

def print_info(text):
    print(colorize(f"  ℹ {text}", Theme.SECONDARY))

def print_logo():
    from .logo import get_logo
    print(get_logo())

def print_divider(char="─", width=60, color=Theme.MUTED):
    print(colorize(char * width, color))

def print_box(lines, color=Theme.PRIMARY):
    max_len = max((len(line) for line in lines), default=0) + 2
    top = "┌" + "─" * max_len + "┐"
    bottom = "└" + "─" * max_len + "┘"
    print(colorize(top, color))
    for line in lines:
        print(colorize(f"│ {line.ljust(max_len-1)}│", color))
    print(colorize(bottom, color))

def print_section(title, content_lines):
    print_divider("─", 50, Theme.MUTED)
    print(colorize(f"  {title}", Theme.HIGHLIGHT + Colors.BOLD))
    for line in content_lines:
        print(colorize(f"    {line}", Theme.TEXT))
    print()

def print_status(text):
    print(colorize(f"  ● {text}", Theme.PRIMARY))

def print_file_action(action, path, details=""):
    icons = {'create': '📄', 'modify': '✎', 'delete': '🗑', 'read': '📖'}
    colors_map = {
        'create': Theme.SUCCESS,
        'modify': Theme.WARNING,
        'delete': Theme.ERROR,
        'read': Theme.SECONDARY,
    }
    icon = icons.get(action, '•')
    color = colors_map.get(action, Theme.TEXT)
    msg = f"  {icon} {path}"
    if details:
        msg += f" {colorize(details, Theme.MUTED)}"
    print(colorize(msg, color))

class Spinner:
    """Анимированный спиннер"""
    def __init__(self, message="Загрузка"):
        self.message = message
        self.running = False
        self.thread = None
        self.chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self, final_message=None):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
        if final_message:
            print(final_message)

    def _spin(self):
        i = 0
        while self.running:
            char = self.chars[i % len(self.chars)]
            sys.stdout.write(f'\r  {char} {self.message}...')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

def print_package_status(package, action, success=True):
    """Красивое отображение установки пакета"""
    icon = '✔' if success else '✘'
    color = Theme.SUCCESS if success else Theme.ERROR
    print(colorize(f"    {icon} {package}", color))

def print_command_result(command, success, output=None):
    """Отображение результата команды"""
    icon = '✔' if success else '✘'
    color = Theme.SUCCESS if success else Theme.ERROR
    print(colorize(f"  {icon} {command[:60]}", color))
    if output and not success:
        for line in output.strip().split('\n')[:5]:
            print(colorize(f"    {line}", Theme.MUTED))