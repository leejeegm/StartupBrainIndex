@echo off
setlocal
title SBI 서버
chcp 65001 >nul
cd /d "%~dp0"
if errorlevel 1 (
  echo [SBI] 프로젝트 폴더로 이동 실패. run_server.bat 이 있는 폴더에서 실행해 주세요.
  pause
  exit /b 1
)

set HOST=127.0.0.1
set PORT=
for /f %%P in ('powershell -NoProfile -Command "$ports=8000,8001,8050,8080; foreach($p in $ports){ try { $l=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$p); $l.Start(); $l.Stop(); Write-Output $p; break } catch {} }"') do set PORT=%%P
if "%PORT%"=="" set PORT=8000
set URL=http://%HOST%:%PORT%/

for /f "tokens=*" %%A in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } | Select-Object -First 1).IPAddress" 2^>nul') do set LAN_IP=%%A
if "%LAN_IP%"=="" set LAN_IP=(PC IP 확인: ipconfig)

echo.
echo [SBI] 서버를 시작합니다.
echo [SBI] PC 접속: %URL%
echo [SBI] 모바일 접속: http://%LAN_IP%:%PORT%/  ^(같은 Wi-Fi에서만^)
echo [SBI] 사용 포트: %PORT%
echo       *** 이 창을 닫지 마세요. 닫으면 서버가 종료됩니다. ***
echo.

echo %URL%| clip
echo [SBI] PC 접속 주소를 클립보드에 복사했습니다.

python main.py
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [SBI] 서버가 비정상 종료되었습니다. (exit code: %EXIT_CODE%)
  echo [SBI] Python 설치 및 PATH 확인: 명령 프롬프트에서 python --version
  echo [SBI] 접속 주소를 다시 복사했습니다: %URL%
  echo %URL%| clip
)

echo.
echo [SBI] 아무 키나 누르면 이 창이 닫힙니다.
pause >nul
endlocal & exit /b %EXIT_CODE%
