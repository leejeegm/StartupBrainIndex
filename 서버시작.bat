@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo [SBI] 서버를 시작합니다...
echo.

set PORT=8765
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:%PORT%"

python main.py

pause
