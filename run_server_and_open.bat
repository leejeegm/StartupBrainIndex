@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo [SBI] 서버 시작 후 브라우저를 엽니다. 잠시 기다리세요...
echo.

set PORT=8000
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000/"
python main.py
if errorlevel 1 pause
