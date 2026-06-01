"""
Управление конфигурацией HandyCode
"""

import os
import json
from pathlib import Path


class Config:
    """Управляет конфигурацией HandyCode"""

    def __init__(self):
        self.config_dir = Path.home() / '.handycode'
        self.config_dir.mkdir(exist_ok=True)

        self.env_file = self.config_dir / '.env'
        self.config_file = self.config_dir / 'config.json'

        self.config = self._load_config()

    def _load_config(self) -> dict:
        default_config = {
            "default_model": "deepseek",
            "auto_approve": False,
            "language": "ru",
            "installed_version": "2.3.0",
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except:
                pass

        return default_config

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_api_key(self) -> str:
        """Получает API ключ из разных источников, запрашивает если нет"""
        api_key = None

        # 1. Переменная окружения
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            return api_key

        # 2. .env файл
        if self.env_file.exists():
            try:
                with open(self.env_file, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('OPENROUTER_API_KEY='):
                            key = line.split('=', 1)[1].strip().strip('"').strip("'")
                            if key and not key.startswith('#'):
                                api_key = key
                                break
            except:
                pass

        if api_key:
            return api_key

        # 3. Файл конфигурации
        if 'api_key' in self.config and self.config['api_key']:
            return self.config['api_key']

        # 4. Запрашиваем у пользователя
        api_key = self._request_api_key()

        return api_key

    def _request_api_key(self) -> str:
        """Запрашивает API ключ у пользователя с красивым оформлением"""
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║              🔑 API КЛЮЧ НЕ НАЙДЕН                            ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print("  Для работы HandyCode требуется API ключ OpenRouter.")
        print("  Получите его бесплатно на сайте:")
        print()
        print("    https://openrouter.ai/keys")
        print()
        print("  Инструкция:")
        print("    1. Зарегистрируйтесь на openrouter.ai")
        print("    2. Перейдите в раздел Keys")
        print("    3. Создайте новый ключ")
        print("    4. Скопируйте ключ и вставьте его ниже")
        print()

        while True:
            api_key = input("  API ключ: ").strip()

            if not api_key:
                print()
                print("  ⚠ Ключ не может быть пустым. Попробуйте снова.")
                print()
                continue

            if len(api_key) < 20:
                print()
                print("  ⚠ Ключ слишком короткий. Проверьте ключ.")
                print()
                continue

            break

        # Сохраняем ключ
        try:
            # В .env файл
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, encoding='utf-8') as f:
                    env_content = f.read()

            if 'OPENROUTER_API_KEY=' in env_content:
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('OPENROUTER_API_KEY='):
                        new_lines.append(f'OPENROUTER_API_KEY={api_key}')
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)
            else:
                if env_content and not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += f'OPENROUTER_API_KEY={api_key}\n'

            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)

            try:
                os.chmod(self.env_file, 0o600)
            except:
                pass

            print()
            print("  ✅ Ключ сохранён в ~/.handycode/.env")
            print()

        except Exception as e:
            print(f"  ⚠ Не удалось сохранить ключ: {e}")
            print(f"  Добавьте вручную в {self.env_file}:")
            print(f"  OPENROUTER_API_KEY={api_key}")

        return api_key

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value
        self.save_config()