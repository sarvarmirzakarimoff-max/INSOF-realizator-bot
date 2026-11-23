@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo GitHub'dan eng yangi versiya yuklanmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$z=Join-Path $env:TEMP 'insof_yangi.zip'; $d=Join-Path $env:TEMP 'insof_yangi';" ^
  "Invoke-WebRequest 'https://github.com/sarvarmirzakarimoff-max/INSOF-realizator-bot/archive/refs/heads/main.zip' -OutFile $z;" ^
  "if (Test-Path $d) { Remove-Item $d -Recurse -Force };" ^
  "Expand-Archive $z $d -Force;" ^
  "$src=Get-ChildItem $d | Select-Object -First 1;" ^
  "Copy-Item (Join-Path $src.FullName '*') . -Recurse -Force -Exclude '.env','*.db';" ^
  "Write-Host 'Yangilandi.'"
if errorlevel 1 (
  echo XATO: yangilab bo'lmadi. Internetni tekshiring.
  pause
  exit /b 1
)
echo.
echo Endi eski bot oynasini yoping va ishga_tushirish.bat ni oching.
pause
