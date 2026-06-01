"""
Вспомогательные функции для HandyCode
"""

import sys
import os


class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'


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
    print(colorize(text, Colors.CYAN + Colors.BOLD))


def print_success(text):
    print(colorize(f"  ✓ {text}", Colors.GREEN))


def print_error(text):
    print(colorize(f"  ✗ {text}", Colors.RED))
    return text


def print_warning(text):
    print(colorize(f"  ⚠ {text}", Colors.YELLOW))


def print_info(text):
    print(colorize(f"  ℹ {text}", Colors.BLUE))


def print_logo():
    from .logo import get_small_logo
    print(get_small_logo())


def truncate(text, max_length=100):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_box(text, color=Colors.CYAN):
    """Рисует рамку вокруг текста"""
    lines = text.strip().split('\n')
    width = max(len(line) for line in lines) + 4
    print(colorize(f"╭{'─' * (width - 2)}╮", color))
    for line in lines:
        print(colorize(f"│ {line.ljust(width - 4)} │", color))
    print(colorize(f"╰{'─' * (width - 2)}╯", color))


def print_divider(char="─", width=60, color=Colors.BRIGHT_BLACK):
    """Рисует разделитель"""
    print(colorize(char * width, color))


def print_file_action(action_type, path, details=""):
    """Красиво показывает действие с файлом"""
    icons = {
        'create': '📄',
        'modify': '✏️',
        'delete': '🗑️',
        'read': '📖',
    }
    colors_map = {
        'create': Colors.GREEN,
        'modify': Colors.YELLOW,
        'delete': Colors.RED,
        'read': Colors.BLUE,
    }

    icon = icons.get(action_type, '•')
    color = colors_map.get(action_type, Colors.WHITE)

    if details:
        print(colorize(f"  {icon} {path} {Colors.BRIGHT_BLACK}{details}{Colors.RESET}", color))
    else:
        print(colorize(f"  {icon} {path}", color))


def print_command(cmd, index=1):
    """Красиво показывает команду"""
    print(colorize(f"  {index}. ⚡ {cmd}", Colors.YELLOW))


def print_status(msg):
    """Показывает статус"""
    print(colorize(f"  ● {msg}", Colors.CYAN))