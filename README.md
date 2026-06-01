# HandyCode

AI-ассистент для командной строки, аналог Claude Code. Создавайте проекты, пишите код и управляйте файлами с помощью AI.

## Быстрая установка одной командой

### Linux/MacOS
```bash
curl -sSL https://raw.githubusercontent.com/yourusername/handycode/main/install.sh | bash
```
### Windows
```bash
irm https://raw.githubusercontent.com/yourusername/handycode/main/install.bat | iex
```
### Через pip
```bash
pip install handycode
```
### Использование
```bash
hc                              # Запуск в текущей директории
hc -p /путь/к/проекту           # Запуск в конкретной папке
hc -c "Создай React приложение" # Быстрое создание проекта
hc -m gpt4                      # Выбор модели
hc -y -c "Создай Python API"    # Авто-подтверждение
handycode --help                # Справка
```
### Команды внутри программы
```bash
/help, /помощь - Справка

/scan, /сканировать - Показать структуру проекта

/models, /модели - Список моделей

/model, /модель - Переключить модель

/clear, /очистить - Очистить историю

/save, /сохранить - Сохранить сессию

/stats, /статистика - Статистика

/exit, /выход - Выйти
```
### Настройка API ключа

Получите ключ на https://openrouter.ai/keys

Создайте файл ~/.handycode/.env:

```bash
OPENROUTER_API_KEY=ваш_ключ
```

### Безопасность
Все операции подтверждаются пользователем

Создаются резервные копии перед изменениями

Проверка путей на безопасность

Запрет выхода за пределы проекта

Блокировка опасных команд

### Лицензия
MIT
