"""
Вспомогательные функции для HandyCode
"""

import sys
import os

class Colors:
    # Базовые
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'

    # Стандартные мягкие тона (не яркие)
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Яркие (для акцентов)
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

# Тема HandyCode (премиальная пастель)
class Theme:
    PRIMARY = Colors.CYAN          # мягкий циан
    SECONDARY = Colors.BLUE        # спокойный синий
    ACCENT = Colors.MAGENTA        # акцент
    SUCCESS = Colors.GREEN
    WARNING = Colors.YELLOW
    ERROR = Colors.RED
    TEXT = Colors.WHITE
    MUTED = Colors.BRIGHT_BLACK    # серый для подписей
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

def print_install_logo():
    from .logo import get_install_logo
    print(get_install_logo())

def truncate(text, max_length=100):
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def print_divider(char="─", width=60, color=Theme.MUTED):
    print(colorize(char * width, color))

def print_box(lines, color=Theme.PRIMARY):
    """Рамка вокруг списка строк"""
    max_len = max((len(line) for line in lines), default=0) + 2
    top = "┌" + "─" * max_len + "┐"
    bottom = "└" + "─" * max_len + "┘"
    print(colorize(top, color))
    for line in lines:
        print(colorize(f"│ {line.ljust(max_len-1)}│", color))
    print(colorize(bottom, color))

def print_section(title, content_lines):
    """Секция с заголовком и содержимым"""
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