@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set LOG_FILE=%TEMP%\handycode_update_log.txt
echo HandyCode Update Log > "%LOG_FILE%"
echo Date: %DATE% %TIME% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║           HANDYCODE - ОБНОВЛЕНИЕ                     ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo Лог: %LOG_FILE%
echo.

:: Проверка Python
echo [1/4] Проверка Python...
echo [1/4] Checking Python... >> "%LOG_FILE%"

where python >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python & goto :python_found
where python3 >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=python3 & goto :python_found
where py >nul 2>nul
if %errorlevel% equ 0 set PYTHON_CMD=py & goto :python_found

echo [ERROR] Python не найден
echo [ERROR] Python not found >> "%LOG_FILE%"
goto :error_exit

:python_found
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do (
    echo [OK] Python %%i
    echo [OK] Python %%i >> "%LOG_FILE%"
)

:: Проверка текущей версии
echo [2/4] Проверка текущей версии...
echo [2/4] Checking current version... >> "%LOG_FILE%"

%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2>nul
if %errorlevel% equ 0 (
    for /f %%i in ('%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2^>^&1') do (
        echo [OK] Текущая версия: %%i
        echo [OK] Current version: %%i >> "%LOG_FILE%"
        set OLD_VERSION=%%i
    )
) else (
    echo [--] HandyCode не установлен
    echo [--] HandyCode not installed >> "%LOG_FILE%"
    echo.
    echo HandyCode не найден. Сначала установите: install.bat
    goto :error_exit
)

:: Обновление
echo [3/4] Обновление HandyCode...
echo [3/4] Updating HandyCode... >> "%LOG_FILE%"

set UPDATE_OK=0

:: Способ 1: pip из GitHub
echo [*] Способ 1: pip install из GitHub...
echo [*] Method 1: pip from GitHub >> "%LOG_FILE%"
%PYTHON_CMD% -m pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/AuraTechno/HandyCode.git >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] Обновлено из GitHub
    echo [OK] Updated from GitHub >> "%LOG_FILE%"
    set UPDATE_OK=1
    goto :verify_update
)
echo [--] Не удалось
echo [--] GitHub method failed >> "%LOG_FILE%"

:: Способ 2: pip из PyPI
echo [*] Способ 2: pip install из PyPI...
echo [*] Method 2: pip from PyPI >> "%LOG_FILE%"
%PYTHON_CMD% -m pip install --upgrade --force-reinstall --no-cache-dir handycode >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] Обновлено из PyPI
    echo [OK] Updated from PyPI >> "%LOG_FILE%"
    set UPDATE_OK=1
    goto :verify_update
)
echo [--] Не удалось
echo [--] PyPI method failed >> "%LOG_FILE%"

:: Способ 3: Очистка кэша и повтор
echo [*] Способ 3: Очистка кэша и повтор...
echo [*] Method 3: Clear cache and retry >> "%LOG_FILE%"
%PYTHON_CMD% -m pip cache purge >> "%LOG_FILE%" 2>&1
%PYTHON_CMD% -m pip install --upgrade --force-reinstall --no-cache-dir handycode >> "%LOG_FILE%" 2>&1
if %errorlevel% equ 0 (
    echo [OK] Обновлено после очистки кэша
    echo [OK] Updated after cache purge >> "%LOG_FILE%"
    set UPDATE_OK=1
    goto :verify_update
)
echo [--] Не удалось
echo [--] Cache purge method failed >> "%LOG_FILE%"

:verify_update
if %UPDATE_OK%==0 (
    echo.
    echo [ERROR] Не удалось обновить HandyCode
    echo [ERROR] Update failed >> "%LOG_FILE%"
    goto :error_exit
)

:: Проверка новой версии
echo [4/4] Проверка обновления...
echo [4/4] Verifying update... >> "%LOG_FILE%"

%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2>nul
if %errorlevel% equ 0 (
    for /f %%i in ('%PYTHON_CMD% -c "import handycode; print(handycode.__version__)" 2^>^&1') do (
        echo [OK] Новая версия: %%i
        echo [OK] New version: %%i >> "%LOG_FILE%"
        set NEW_VERSION=%%i
    )
) else (
    echo [ERROR] Проверка не пройдена
    echo [ERROR] Verification failed >> "%LOG_FILE%"
    goto :error_exit
)

:: Сравнение версий
if "%OLD_VERSION%"=="%NEW_VERSION%" (
    echo.
    echo [!] Версия не изменилась: %NEW_VERSION%
    echo [!] Version unchanged: %NEW_VERSION% >> "%LOG_FILE%"
    echo.
    echo Возможно, новых обновлений нет.
) else (
    echo.
    echo [OK] Обновление успешно!
    echo [OK] Update successful >> "%LOG_FILE%"
    echo.
    echo   %OLD_VERSION% → %NEW_VERSION%
)

:: Обновление скриптов запуска
echo [*] Обновление скриптов запуска...
echo [*] Updating launcher scripts >> "%LOG_FILE%"

set BIN_DIR=%USERPROFILE%\.local\bin

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\hc.bat"

(
echo @echo off
echo %PYTHON_CMD% -m handycode %%*
) > "%BIN_DIR%\handycode.bat"

echo [OK] Скрипты обновлены
echo [OK] Scripts updated >> "%LOG_FILE%"

:: Успешное завершение
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║              ✅ HANDYCODE ОБНОВЛЁН                      ║
echo ║                 v%NEW_VERSION%                                  ║
echo ║                                                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

if not "%OLD_VERSION%"=="%NEW_VERSION%" (
    echo Изменения:
    echo   • Обновлены файлы пакета
    echo   • Обновлены скрипты запуска
    echo   • Очищен кэш pip
)

echo.
echo Лог обновления: %LOG_FILE%
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
exit /b 0

:error_exit
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║              ❌ ОБНОВЛЕНИЕ НЕ УДАЛОСЬ                   ║
echo ║                                                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Содержимое лога:
echo ========================================
type "%LOG_FILE%"
echo ========================================
echo.
echo Попробуйте вручную:
echo   %PYTHON_CMD% -m pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/AuraTechno/HandyCode.git
echo.
echo Лог сохранён: %LOG_FILE%
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
exit /b 1