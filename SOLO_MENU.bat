@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "LOG=%cd%\SALIDA_SOLO_MENU.txt"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not exist ".env" (
  echo Falta .env
  pause
  exit /b 1
)

echo === SOLO MENU %date% %time% === > "%LOG%"
echo --- >> "%LOG%"
python solo_menu.py >> "%LOG%" 2>&1
set PYERR=!ERRORLEVEL!
echo. >> "%LOG%"
echo EXIT_PYTHON=!PYERR! >> "%LOG%"

type "%LOG%"
echo.
echo Codigo: !PYERR!
start notepad "%LOG%"
pause
exit /b !PYERR!
