"""
Управление файлами для HandyCode
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from handycode.utils import (
    print_success, print_error, print_warning, print_info,
    print_status, print_package_status, print_command_result, Spinner
)


class FileManager:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.allowed_extensions = {
            '.html', '.css', '.scss', '.sass', '.less',
            '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
            '.vue', '.svelte', '.astro',
            '.py', '.pyi', '.pyx', '.pxd',
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.xml', '.env', '.gitignore', '.dockerignore',
            '.md', '.mdx', '.rst', '.txt', '.log',
            '.sql', '.sh', '.bash', '.zsh', '.bat', '.ps1',
            '.java', '.kt', '.scala',
            '.cpp', '.c', '.h', '.hpp', '.cs',
            '.rs', '.go', '.rb', '.php', '.swift',
            '.dart', '.r', '.jl', '.lua',
            '.dockerfile', '.makefile', '.cmake',
        }
        self.excluded_dirs = {
            'node_modules', '__pycache__', '.git', '.svn',
            'venv', '.venv', 'env', '.env',
            'dist', 'build', '.next', '.nuxt',
            'target', 'out', '.idea', '.vscode',
            '.DS_Store', 'Thumbs.db',
        }

    def scan_project(self) -> str:
        if not self.project_root.exists():
            return ""
        try:
            lines = [f"📁 Проект: {self.project_root.name}"]
            all_files = []
            for ext in self.allowed_extensions:
                all_files.extend(self.project_root.rglob(f"*{ext}"))
            all_files.extend(self.project_root.rglob("*"))
            seen = set()
            files = []
            for f in sorted(all_files):
                if f.is_file() and f not in seen:
                    rel = str(f.relative_to(self.project_root))
                    if not any(ex in f.parts for ex in self.excluded_dirs):
                        if not any(rel.startswith(ex) for ex in self.excluded_dirs):
                            files.append(f)
                            seen.add(f)
            lines.append(f"📄 Файлов: {len(files)}")
            if files:
                lines.append("\n📂 Структура:")
                for file in files:
                    try:
                        rel_path = file.relative_to(self.project_root)
                        size = file.stat().st_size
                        lines.append(f"  {rel_path} ({self._format_size(size)})")
                    except:
                        pass
            return '\n'.join(lines)
        except Exception as e:
            return f"Ошибка: {e}"

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def create_file(self, path: str, content: str) -> bool:
        try:
            full_path = self.project_root / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if full_path.exists():
                backup = full_path.with_suffix(full_path.suffix + '.bak')
                shutil.copy2(full_path, backup)
            full_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print_error(f"Ошибка создания {path}: {e}")
            return False

    def modify_file(self, path: str, content: str) -> bool:
        try:
            full_path = self.project_root / path
            if not full_path.exists():
                return self.create_file(path, content)
            backup = full_path.with_suffix(full_path.suffix + '.bak')
            shutil.copy2(full_path, backup)
            full_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print_error(f"Ошибка изменения {path}: {e}")
            return False

    def delete_file(self, path: str) -> bool:
        try:
            full_path = self.project_root / path
            if not full_path.exists():
                return False
            backup = full_path.with_suffix(full_path.suffix + '.bak')
            shutil.copy2(full_path, backup)
            full_path.unlink()
            print_success(f"Удалён: {path}")
            return True
        except Exception as e:
            print_error(f"Ошибка удаления {path}: {e}")
            return False

    def read_file(self, path: str) -> bool:
        try:
            full_path = self.project_root / path
            if not full_path.exists():
                return False
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            print(f"\n=== {path} ===\n{content}")
            return True
        except Exception as e:
            print_error(f"Ошибка чтения {path}: {e}")
            return False

    def list_directory(self, path: str = ".") -> bool:
        try:
            full_path = self.project_root / path
            if not full_path.exists():
                return False
            items = list(full_path.iterdir())
            print(f"\n=== {path or '.'} ({len(items)} элементов) ===")
            for item in sorted(items):
                if item.is_dir():
                    print(f"  📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    print(f"  📄 {item.name} ({self._format_size(size)})")
            return True
        except Exception as e:
            print_error(f"Ошибка: {e}")
            return False

    def execute_command(self, command: str, timeout: int = 300) -> tuple[bool, str]:
        """Выполняет команду и возвращает (успех, вывод)"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            print_command_result(command, success, output if not success else None)
            return success, output
        except subprocess.TimeoutExpired:
            print_command_result(command, False, "Таймаут выполнения")
            return False, "Таймаут выполнения"
        except Exception as e:
            print_command_result(command, False, str(e))
            return False, str(e)

    def install_package(self, package: str) -> bool:
        """Устанавливает пакет через pip"""
        spinner = Spinner(f"Установка {package}")
        spinner.start()
        try:
            result = subprocess.run(
                f"pip install {package}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            spinner.stop()
            success = result.returncode == 0
            print_package_status(package, "установлен", success)
            if not success:
                print_error(result.stderr[:200])
            return success
        except:
            spinner.stop()
            print_package_status(package, "ошибка", False)
            return False

    def get_installed_packages(self) -> List[str]:
        """Получает список установленных pip-пакетов"""
        try:
            result = subprocess.run(
                "pip list --format=freeze",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return [line.split('==')[0].lower() for line in result.stdout.strip().split('\n') if '==' in line]
        except:
            pass
        return []

    def save_session(self, history: List[Dict], model: str, stats: Dict) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"handycode_session_{timestamp}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# HandyCode Session\n\n")
                f.write(f"Date: {datetime.now()}\n")
                f.write(f"Model: {model}\n\n---\n\n")
                for msg in history[1:]:
                    if msg['role'] == 'user':
                        f.write(f"## User\n\n{msg['content']}\n\n")
                    else:
                        f.write(f"## Assistant\n\n{msg['content']}\n\n---\n\n")
            return print_success(f"Сессия сохранена: {filename}")
        except Exception as e:
            return print_error(f"Ошибка сохранения: {e}")