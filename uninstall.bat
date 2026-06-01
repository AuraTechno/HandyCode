@echo off
chcp 65001 >nul 2>&1
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║           HANDYCODE - UNINSTALL                      ║
echo ╚══════════════════════════════════════════════════════╝
echo.

echo [1/4] Удаление через pip...
pip uninstall handycode -y 2>nul
echo   [OK] Готово

echo [2/4] Удаление из site-packages...
for /f "tokens=*" %%i in ('python -c "import site; print(site.getsitepackages()[0])" 2^>^&1') do set SITE=%%i

if exist "%SITE%\handycode" (
    rmdir /s /q "%SITE%\handycode"
    echo   [OK] Папка handycode удалена
)

if exist "%SITE%\handycode-2.0.0.dist-info" (
    rmdir /s /q "%SITE%\handycode-2.0.0.dist-info"
    echo   [OK] dist-info удалён
)

for /d %%i in ("%SITE%\~*") do (
    rmdir /s /q "%%i" 2>nul
    echo   [OK] Удалено: %%~ni
)

echo [3/4] Удаление конфигурации...
if exist "%USERPROFILE%\.handycode" (
    rmdir /s /q "%USERPROFILE%\.handycode"
    echo   [OK] .handycode удалён
)

echo [4/4] Очистка кэша pip...
pip cache purge 2>nul
echo   [OK] Кэш очищен

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║           ✅ HANDYCODE ПОЛНОСТЬЮ УДАЛЁН              ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo Нажмите любую клавишу для выхода...
pause >nul