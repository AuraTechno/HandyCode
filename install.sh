#!/bin/bash

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

LOG_FILE="/tmp/handycode_install_log.txt"

# Функция логирования
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Функция ошибки
error_exit() {
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              ❌ УСТАНОВКА ПРЕРВАНА                            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}При установке произошла ошибка!${NC}"
    echo ""
    echo "Содержимое лог-файла:"
    echo "========================================"
    cat "$LOG_FILE"
    echo "========================================"
    echo ""
    echo "Лог сохранён в: $LOG_FILE"
    echo ""
    echo "Попробуйте установить вручную:"
    echo "  pip install git+https://github.com/AuraTechno/HandyCode.git"
    echo ""
    read -p "Нажмите Enter для выхода..."
    exit 1
}

# Инициализация лога
echo "========================================" > "$LOG_FILE"
echo "HandyCode Install Log" >> "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "Version: 2.1.0" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Логотип
clear
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         HANDYCODE - УСТАНОВЩИК ДЛЯ LINUX/MAC                ║"
echo "║                      v2.1.0                                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Лог: $LOG_FILE"
echo ""

# [1/6] Проверка Python
log "[1/6] Проверка Python..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log "[ERROR] Python не найден!"
    error_exit
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log "[OK] $PYTHON_VERSION"

# [2/6] Проверка pip
log "[2/6] Проверка pip..."

if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    log "[*] Устанавливаю pip..."
    $PYTHON_CMD -m ensurepip --upgrade >> "$LOG_FILE" 2>&1 || {
        log "[ERROR] Не удалось установить pip"
        error_exit
    }
fi

PIP_VERSION=$($PYTHON_CMD -m pip --version 2>&1 | head -1)
log "[OK] pip работает"

# [3/6] Проверка requests
log "[3/6] Проверка requests..."

if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    log "[*] Устанавливаю requests..."
    $PYTHON_CMD -m pip install requests --user >> "$LOG_FILE" 2>&1 || {
        log "[ERROR] Не удалось установить requests"
        error_exit
    }
fi
log "[OK] requests готов"

# [4/6] Создание директорий
log "[4/6] Создание директорий..."

HANDYCODE_DIR="$HOME/.handycode"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$HANDYCODE_DIR" "$BIN_DIR"
log "[OK] Директории созданы"

# [5/6] Установка HandyCode
log "[5/6] Установка HandyCode..."

INSTALL_OK=0

# Способ 1: pip из GitHub
log "  [*] Способ 1: pip install из GitHub..."
$PYTHON_CMD -m pip install --user git+https://github.com/AuraTechno/HandyCode.git >> "$LOG_FILE" 2>&1 && {
    log "  [OK] Установлено из GitHub"
    INSTALL_OK=1
} || log "  [--] Не удалось"

# Способ 2: pip из PyPI
if [ $INSTALL_OK -eq 0 ]; then
    log "  [*] Способ 2: pip install из PyPI..."
    $PYTHON_CMD -m pip install --user handycode >> "$LOG_FILE" 2>&1 && {
        log "  [OK] Установлено из PyPI"
        INSTALL_OK=1
    } || log "  [--] Не удалось"
fi

# Способ 3: git clone
if [ $INSTALL_OK -eq 0 ] && command -v git &> /dev/null; then
    log "  [*] Способ 3: git clone..."
    TEMP_DIR="/tmp/handycode_install"
    rm -rf "$TEMP_DIR"
    git clone https://github.com/AuraTechno/HandyCode.git "$TEMP_DIR" >> "$LOG_FILE" 2>&1

    if [ -f "$TEMP_DIR/setup.py" ]; then
        cd "$TEMP_DIR"
        $PYTHON_CMD -m pip install --user -e . >> "$LOG_FILE" 2>&1 && {
            log "  [OK] Установлено через git clone"
            INSTALL_OK=1
        } || log "  [--] Не удалось"
        cd - > /dev/null
    fi
fi

# Способ 4: Ручная установка
if [ $INSTALL_OK -eq 0 ]; then
    log "  [*] Способ 4: Ручная установка..."

    MODULE_DIR="$HANDYCODE_DIR/modules/handycode"
    mkdir -p "$MODULE_DIR"

    BASE_URL="https://raw.githubusercontent.com/AuraTechno/HandyCode/main/handycode"
    FILES="__init__.py __main__.py main.py cli.py assistant.py models.py file_manager.py security.py config.py utils.py logo.py project_templates.py"

    for file in $FILES; do
        if command -v curl &> /dev/null; then
            curl -sS -L -o "$MODULE_DIR/$file" "$BASE_URL/$file" >> "$LOG_FILE" 2>&1
        else
            wget -q -O "$MODULE_DIR/$file" "$BASE_URL/$file" >> "$LOG_FILE" 2>&1
        fi
        log "    [OK] $file"
    done

    SITE_PACKAGES=$($PYTHON_CMD -c "import site; print(site.getusersitepackages())" 2>/dev/null)
    if [ -d "$SITE_PACKAGES" ]; then
        mkdir -p "$SITE_PACKAGES/handycode"
        cp "$MODULE_DIR"/*.py "$SITE_PACKAGES/handycode/"
        log "  [OK] Файлы скопированы в site-packages"
        INSTALL_OK=1
    else
        log "  [ERROR] site-packages не найден"
        error_exit
    fi
fi

if [ $INSTALL_OK -eq 0 ]; then
    log "[ERROR] Все способы установки не сработали!"
    error_exit
fi

# Проверка установки
log "  [*] Проверка установки..."
HC_VERSION=$($PYTHON_CMD -c "import handycode; print(handycode.__version__)" 2>&1) || {
    log "[ERROR] HandyCode не работает"
    error_exit
}
log "  [OK] HandyCode v$HC_VERSION установлен!"

# [6/6] Настройка
log "[6/6] Настройка..."

# API ключ
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  API ключ OpenRouter (бесплатно)${NC}"
echo -e "${BLUE}  Получите: https://openrouter.ai/keys${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo ""
read -p "  Введите API ключ (Enter - пропустить): " API_KEY

if [ -z "$API_KEY" ]; then
    log "  [!] API ключ не введён"
else
    log "  [OK] API ключ получен"
fi

# Сохранение .env
cat > "$HANDYCODE_DIR/.env" << EOF
# HandyCode Configuration
# Get key: https://openrouter.ai/keys
OPENROUTER_API_KEY=$API_KEY

# Default settings
# HANDYCODE_DEFAULT_MODEL=deepseek
# HANDYCODE_AUTO_APPROVE=false
EOF

chmod 600 "$HANDYCODE_DIR/.env"
log "  [OK] Конфигурация сохранена"

# Сохранение config.json
cat > "$HANDYCODE_DIR/config.json" << EOF
{
    "default_model": "deepseek",
    "auto_approve": false,
    "language": "ru",
    "installed_version": "$HC_VERSION",
    "install_date": "$(date '+%Y-%m-%d %H:%M:%S')",
    "api_key_verified": false
}
EOF

log "  [OK] Настройки сохранены"

# Создание скриптов запуска
cat > "$BIN_DIR/hc" << EOF
#!/bin/bash
$PYTHON_CMD -m handycode "\$@"
EOF
chmod +x "$BIN_DIR/hc"

cat > "$BIN_DIR/handycode" << EOF
#!/bin/bash
$PYTHON_CMD -m handycode "\$@"
EOF
chmod +x "$BIN_DIR/handycode"

log "  [OK] Скрипты запуска созданы"

# Добавление в PATH
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile"; do
    if [ -f "$rc" ]; then
        if ! grep -q "$BIN_DIR" "$rc"; then
            echo "" >> "$rc"
            echo "# HandyCode" >> "$rc"
            echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$rc"
        fi
    fi
done

export PATH="$BIN_DIR:$PATH"
log "  [OK] PATH обновлён"

# Финальное сообщение
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              ✅ HANDYCODE УСТАНОВЛЕН!                         ║"
echo "║                 v$HC_VERSION                                         ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$API_KEY" ]; then
    echo -e "${GREEN}[V] API ключ настроен${NC}"
else
    echo -e "${YELLOW}[!] API ключ не настроен${NC}"
    echo -e "   Добавьте в: $HANDYCODE_DIR/.env"
fi

echo ""
echo -e "${WHITE}Для начала работы:${NC}"
echo "  1. Перезапустите терминал (или: source ~/.bashrc)"
echo "  2. Введите: hc"
echo ""
echo -e "${WHITE}Примеры:${NC}"
echo "  hc                              Интерактивный режим"
echo "  hc -c \"Создай React приложение\"  Быстрая команда"
echo "  hc --help                       Справка"
echo ""
echo -e "${WHITE}Для удаления:${NC} ./uninstall.sh"
echo ""
echo -e "${WHITE}Лог установки:${NC} $LOG_FILE"
echo ""
read -p "Нажмите Enter для выхода..."
exit 0