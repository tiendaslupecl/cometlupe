@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Abriendo Shopify Admin (Apps, Temas, Paginas)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\open_shopify_admin.ps1"
echo.
echo LISTO: en el navegador configura la app y scopes; el script Python no puede hacer ese paso por ti.
pause
