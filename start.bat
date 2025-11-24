@echo off
REM Shopify Comet - arranca servidor y abre navegador
SETLOCAL
if not defined NODE_PATH (
  where node >nul 2>nul
  if ERRORLEVEL 1 (
    echo Node.js no encontrado. Por favor instala Node.js (https://nodejs.org/) y vuelve a ejecutar este archivo.
    pause
    exit /b 1
  )
)
cd server
start cmd /k "node index.js"
timeout /t 2 >nul
start "" "http://127.0.0.1:3000/"
echo Servidor iniciado. Cierra esta ventana para terminar.
ENDLOCAL
pause
