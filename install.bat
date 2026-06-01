@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set LOG_FILE=%TEMP%\handycode_install_log.txt
echo ======================================== > "%LOG_FILE%"
echo HandyCode Install Log >> "%LOG_FILE%"
echo Date: %DATE% %TIME% >> "%LOG_FILE%"
echo Version: 2.1.0 >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: Функция для логирования
set LOG_FILE=%TEMP%\handycode_install_log.txt

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║         HANDYCODE - УСТАНОВЩИК ДЛЯ WINDOWS          ║
echo ║                  v2.1.0                              ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo Лог: %LOG_FILE%
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Для глобальной установки запустите от имени администратора
    echo [!] Running without admin rights >> "%LOG_FILE%"
    echo.
)

:: [1/6] Проверка Python
echo [1/6] Проверка Python...
echo [1/6] Checking Python... >> "%LOG_FILE%"

where python >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python & goto :python_found
where python3 >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python3 & goto :python_found
where py >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=py & goto :python_found

echo [ERROR] Python не найден
echo [ERROR] Python not found >> "%LOG_FILE%"
echo.
echo Установите Python 3.8+ с https://python.org
echo При установке отметьте галочку "Add Python to PATH"
echo.
echo ========================================
echo Содержимое лог-файла:
echo ========================================
type "%LOG_FILE%"
echo ========================================
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
exit /b 1

:python_found
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do (
    echo [OK] Python %%i
    echo [OK] Python %%i >> "%LOG_FILE%"
)

:: [2/6] Проверка и установка pip
echo [2/6] Проверка pip...
echo [2/6] Checking pip... >> "%LOG_FILE%"

%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Устанавливаю pip...
    echo [*] Installing pip... >> "%LOG_FILE%"
    %PYTHON_CMD% -m ensurepip --default-pip >> "%LOG_FILE%" 2>&1
    if %errorlevel% equ 0 (
        echo [OK] pip установлен
        echo [OK] pip installed >> "%LOG_FILE%"
    ) else (
        echo [ERROR] Не удалось установить pip
        echo [ERROR] Failed to install pip >> "%LOG_FILE%"
        goto :error_exit
    )
) else (
    for /f "tokens=1,2" %%i in ('%PYTHON_CMD% -m pip --version 2^>^&1') do (
        echo [OK] %%i %%j
        echo [OK] %%i %%j >> "%LOG_FILE%"
    )
)

:: [3/6] Установка requests
echo [3/6] Установка requests...
echo [3/6] Installing requests... >> "%LOG_FILE%"

%PYTHON_CMD% -c "import requests" 2>nul
if %errorlevel% equ 0 (
    echo [OK] requests уже установлен
    echo [OK] requests already installed >> "%LOG_FILE%"
    goto :skip_requests
)

echo [*] Устанавливаю requests...
%PYTHON_CMD% -m pip install requests --user >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] requests установлен
    echo [OK] requests installed >> "%LOG_FILE%"
) else (
    echo [*] Пробую альтернативный способ...
    %PYTHON_CMD% -m ensurepip --upgrade >> "%LOG_FILE%" 2>&1
    %PYTHON_CMD% -m pip install requests >> "%LOG_FILE%" 2>&1
    if %errorlevel% equ 0 (
        echo [OK] requests установлен
        echo [OK] requests installed >> "%LOG_FILE%"
    ) else (
        echo [ERROR] Не удалось установить requests
        echo [ERROR] Failed to install requests >> "%LOG_FILE%"
        goto :error_exit
    )
)

:skip_requests

:: [4/6] Установка HandyCode
echo [4/6] Установка HandyCode...
echo [4/6] Installing HandyCode... >> "%LOG_FILE%"

set HANDYCODE_DIR=%USERPROFILE%\.handycode
set BIN_DIR=%USERPROFILE%\.local\bin

if not exist "%HANDYCODE_DIR%" mkdir "%HANDYCODE_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

set INSTALL_OK=0

:: Способ 1: pip install из GitHub
echo [*] Способ 1: pip install из GitHub...
echo [*] Method 1: pip install from GitHub >> "%LOG_FILE%"
%PYTHON_CMD% -m pip install --user git+https://github.com/AuraTechno/HandyCode.git >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] Установлено из GitHub
    echo [OK] Installed from GitHub >> "%LOG_FILE%"
    set INSTALL_OK=1
    goto :verify_install
)
echo [--] Не удалось установить из GitHub
echo [--] GitHub method failed >> "%LOG_FILE%"

:: Способ 2: pip install из PyPI
echo [*] Способ 2: pip install из PyPI...
echo [*] Method 2: pip install from PyPI >> "%LOG_FILE%"
%PYTHON_CMD% -m pip install --user handycode >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] Установлено из PyPI
    echo [OK] Installed from PyPI >> "%LOG_FILE%"
    set INSTALL_OK=1
    goto :verify_install
)
echo [--] Не удалось установить из PyPI
echo [--] PyPI method failed >> "%LOG_FILE%"

:: Способ 3: git clone
where git >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] Способ 3: git clone...
    echo [*] Method 3: git clone >> "%LOG_FILE%"

    set TEMP_DIR=%TEMP%\handycode_install
    if exist "!TEMP_DIR!" rmdir /s /q "!TEMP_DIR!"

    git clone https://github.com/AuraTechno/HandyCode.git "!TEMP_DIR!" >> "%LOG_FILE%" 2>&1

    if exist "!TEMP_DIR!\setup.py" (
        cd /d "!TEMP_DIR!"
        %PYTHON_CMD% -m pip install --user -e . >> "%LOG_FILE%" 2>&1
        cd /d %USERPROFILE%
        if !errorlevel! equ 0 (
            echo [OK] Установлено через git clone
            echo [OK] Installed via git clone >> "%LOG_FILE%"
            set INSTALL_OK=1
            goto :verify_install
        )
    )
    echo [--] Не удалось установить через git clone
    echo [--] Git clone method failed >> "%LOG_FILE%"
)

:: Способ 4: Ручная установка
echo [*] Способ 4: Ручная установка...
echo [*] Method 4: Manual install >> "%LOG_FILE%"

set BASE_URL=https://raw.githubusercontent.com/AuraTechno/HandyCode/main
set MODULE_DIR=%HANDYCODE_DIR%\modules\handycode

if not exist "%MODULE_DIR%" mkdir "%MODULE_DIR%"

set FILES=__init__.py __main__.py main.py cli.py assistant.py models.py file_manager.py security.py config.py utils.py logo.py project_templates.py

for %%f in (%FILES%) do (
    echo [*] Скачиваю handycode/%%f...
    echo [*] Downloading handycode/%%f >> "%LOG_FILE%"
    curl -s -L -o "%MODULE_DIR%\%%f" "%BASE_URL%/handycode/%%f" >> "%LOG_FILE%" 2>&1
    if exist "%MODULE_DIR%\%%f" (
        echo   [OK] %%f
        echo   [OK] %%f >> "%LOG_FILE%"
    ) else (
        echo   [--] %%f не скачан
        echo   [--] %%f failed >> "%LOG_FILE%"
    )
)

:: Копируем в site-packages
for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import site; print(site.getusersitepackages())" 2^>^&1') do set SITE_PACKAGES=%%i

if exist "%SITE_PACKAGES%" (
    if not exist "%SITE_PACKAGES%\handycode" mkdir "%SITE_PACKAGES%\handycode"
    copy /Y "%MODULE_DIR%\*.py" "%SITE_PACKAGES%\handycode\" >nul 2>&1
    echo [OK] Файлы скопированы в site-packages
    echo [OK] Files copied to site-packages >> "%LOG_FILE%"
    set INSTALL_OK=1
) else (
    echo [ERROR] site-packages не найден
    echo [ERROR] site-packages not found >> "%LOG_FILE%"
    goto :error_exit
)

:verify_install
if %INSTALL_OK%==0 (
    echo [ERROR] Все способы установки не сработали!
    echo [ERROR] All install methods failed >> "%LOG_FILE%"
    goto :error_exit
)

:: [5/6] Проверка установки
echo [5/6] Проверка установки...
echo [5/6] Verifying installation... >> "%LOG_FILE%"

%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2>nul
if %errorlevel% equ 0 (
    for /f %%i in ('%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2^>^&1') do (
        echo [OK] HandyCode v%%i работает!
        echo [OK] HandyCode v%%i works >> "%LOG_FILE%"
        set HC_VERSION=%%i
    )
) else (
    echo [ERROR] HandyCode не работает
    echo [ERROR] HandyCode not working >> "%LOG_FILE%"
    goto :error_exit
)

:: [6/6] Настройка
echo [6/6] Настройка...
echo [6/6] Configuration... >> "%LOG_FILE%"

:: API ключ
echo.
echo ═══════════════════════════════════════════════════════════
echo   API ключ OpenRouter (бесплатно)
echo   Получите: https://openrouter.ai/keys
echo ═══════════════════════════════════════════════════════════
echo.
set /p API_KEY="  Введите API ключ (Enter - пропустить): "

if "!API_KEY!"=="" (
    echo [!] API ключ не введён
    echo [!] No API key provided >> "%LOG_FILE%"
) else (
    echo [OK] API ключ получен
    echo [OK] API key provided >> "%LOG_FILE%"
)

:: Сохранение конфигурации
(
echo # HandyCode Configuration
echo # Get key: https://openrouter.ai/keys
echo OPENROUTER_API_KEY=!API_KEY!
echo.
echo # Default settings
echo # HANDYCODE_DEFAULT_MODEL=deepseek
echo # HANDYCODE_AUTO_APPROVE=false
) > "%HANDYCODE_DIR%\.env"

echo [OK] Конфигурация сохранена
echo [OK] Configuration saved >> "%LOG_FILE%"

:: Сохранение config.json
set INSTALL_DATE=%DATE% %TIME%
(
echo {
echo     "default_model": "deepseek",
echo     "auto_approve": false,
echo     "language": "ru",
echo     "installed_version": "!HC_VERSION!",
echo     "install_date": "!INSTALL_DATE!",
echo     "api_key_verified": false
echo }
) > "%HANDYCODE_DIR%\config.json"

echo [OK] Настройки сохранены
echo [OK] Settings saved >> "%LOG_FILE%"

:: Создание скриптов запуска
(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\hc.bat"

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\handycode.bat"

echo [OK] Скрипты запуска созданы
echo [OK] Launch scripts created >> "%LOG_FILE%"

:: Добавление в PATH
setx PATH "%PATH%;%BIN_DIR%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Добавлено в PATH
    echo [OK] Added to PATH >> "%LOG_FILE%"
) else (
    echo [!] Не удалось добавить в PATH
    echo [!] Failed to add to PATH >> "%LOG_FILE%"
    echo     Добавьте вручную: %BIN_DIR%
)

:: Финальное сообщение
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║              ✅ HANDYCODE УСТАНОВЛЕН!                   ║
echo ║                 v%HC_VERSION%                                  ║
echo ║                                                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

if not "!API_KEY!"=="" (
    echo [V] API ключ настроен
) else (
    echo [!] API ключ не настроен
    echo    Добавьте в: %HANDYCODE_DIR%\.env
)

echo.
echo Для начала работы:
echo   1. Закройте это окно
echo   2. Откройте новый терминал (Win+R -^> cmd)
echo   3. Введите: hc
echo.
echo Если hc не работает:
echo   • Перезагрузите компьютер
echo   • Или используйте: %BIN_DIR%\hc.bat
echo.
echo Примеры:
echo   hc                              Интерактивный режим
echo   hc -c "Создай React приложение"  Быстрая команда
echo   hc --help                       Справка
echo.
echo Для удаления: uninstall.bat
echo.
echo Лог установки: %LOG_FILE%
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
exit /b 0

:error_exit
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║              ❌ УСТАНОВКА ПРЕРВАНА                      ║
echo ║                                                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo При установке произошла ошибка!
echo.
echo Содержимое лог-файла:
echo ========================================
type "%LOG_FILE%"
echo ========================================
echo.
echo Лог сохранён в: %LOG_FILE%
echo.
echo Попробуйте установить вручную:
echo   %PYTHON_CMD% -m pip install git+https://github.com/AuraTechno/HandyCode.git
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
exit /b 1