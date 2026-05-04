@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "LOG=%cd%\SALIDA_ULTIMA_EJECUCION.txt"

echo START %date% %time% > "%LOG%"
echo Folder: %cd% >> "%LOG%"
echo. >> "%LOG%"

if not exist ".env" goto ERR_NO_ENV

where python >nul 2>nul
if errorlevel 1 goto ERR_NO_PYTHON

echo --- pip install --- >> "%LOG%"
python -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 goto ERR_PIP

echo --- python main.py --- >> "%LOG%"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python main.py >> "%LOG%" 2>&1
set PYERR=!ERRORLEVEL!

echo EXIT_PYTHON=!PYERR! >> "%LOG%"
echo.
echo Listo. Codigo Python real: !PYERR!
echo execution_log.json debe estar en esta carpeta (no dentro de tasks^): >> "%LOG%"
echo %cd%\execution_log.json >> "%LOG%"
echo Se abre el archivo de texto con el detalle...
start notepad "%LOG%"
pause
exit /b !PYERR!

:ERR_NO_ENV
echo ERROR: falta archivo .env >> "%LOG%"
echo ERROR: falta archivo .env (copia .env.example a .env)
start notepad "%LOG%"
pause
exit /b 1

:ERR_NO_PYTHON
echo ERROR: no encuentro python en PATH >> "%LOG%"
echo ERROR: instala Python desde python.org y marca ADD TO PATH
start notepad "%LOG%"
pause
exit /b 1

:ERR_PIP
echo ERROR: fallo pip install >> "%LOG%"
start notepad "%LOG%"
pause
exit /b 1
