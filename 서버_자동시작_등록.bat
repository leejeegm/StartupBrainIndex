@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 이 배치를 "시작 프로그램" 폴더에 바로가기로 넣으면, Windows 로그인 후 SBI 서버가 자동으로 실행됩니다.
:: 사용법: 이 파일 우클릭 → "바로 가기 만들기" → Win+R → shell:startup → 그 폴더에 바로가기 붙여넣기

set PORT=8000
for /f %%P in ('powershell -NoProfile -Command "$ports=8000,8001,8050,8080; foreach($p in $ports){ try { $l=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$p); $l.Start(); $l.Stop(); Write-Output $p; break } catch {} }"') do set PORT=%%P
if "%PORT%"=="" set PORT=8000

for /f "tokens=*" %%A in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } | Select-Object -First 1).IPAddress" 2^>nul') do set LAN_IP=%%A
if "%LAN_IP%"=="" set LAN_IP=(ipconfig 로 확인)

echo.
echo [SBI] 서버 자동시작 - 이 창을 닫으면 서버가 종료됩니다.
echo [SBI] PC: http://127.0.0.1:%PORT%/
echo [SBI] 모바일: http://%LAN_IP%:%PORT%/
echo.

python main.py
if errorlevel 1 pause
