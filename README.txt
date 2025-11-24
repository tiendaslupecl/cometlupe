Shopify Comet — Paquete completo (listo para usar)

Contenido:
- server/    -> servidor Node.js que maneja OAuth con Shopify y guarda tokens en SQLite.
- app/       -> frontend simple (HTML + JS).
- electron/  -> Electron wrapper que inicia el servidor y abre la UI (opcional).
- start.bat  -> Arranca el servidor y abre el navegador (Windows).
- start.sh   -> Arranca el servidor y abre el navegador (macOS / Linux).
- .env.example -> archivo de ejemplo para tus credenciales (NO contiene claves).

Objetivo:
Este paquete está preparado para que **no necesites editar código**. Solo sigue los pasos a continuación.
Si prefieres que yo te guíe paso a paso, responde **"Guiame"**.

INSTRUCCIONES SIMPLES (Windows)
1. Instala Node.js si no lo tienes: https://nodejs.org/ (elige LTS).
2. Descarga y descomprime este ZIP en una carpeta, por ejemplo C:\proyectos\shopify-comet
3. Abre la carpeta y haz doble clic en `start.bat`.
   - Si Node.js está instalado, se abrirá una ventana de comandos y el servidor se iniciará.
   - Se abrirá automáticamente tu navegador en http://127.0.0.1:3000/
4. Para conectar una tienda Shopify, en el navegador visita:
   http://127.0.0.1:3000/auth?shop=your-shop.myshopify.com
   (reemplaza your-shop.myshopify.com por tu dominio)
5. Cuando la instalación termine verás un mensaje "Instalación completada" y el token se guardará localmente en `server/shopify_tokens.db`.

INSTRUCCIONES SIMPLES (macOS / Linux)
1. Instala Node.js (LTS) si no lo tienes.
2. Descomprime el ZIP.
3. Abre Terminal, navega a la carpeta y ejecuta: `./start.sh`
4. Sigue los pasos 4–5 de arriba para conectar la tienda.

IMPORTANTE — Añadir tus credenciales de Shopify (sólo si quieres instalar en una tienda)
1. Crea un archivo `.env` en la raíz del proyecto copiando `.env.example`:
   - Windows: crea un archivo de texto llamado `.env` con el contenido del `.env.example` y rellena las claves.
   - macOS/Linux: `cp .env.example .env` y edítalo.
2. Rellena `SHOPIFY_API_KEY` y `SHOPIFY_API_SECRET` con tus claves desde Shopify Partner Dashboard.
3. Reinicia `start.bat` o `start.sh` si el servidor ya estaba corriendo.

¿Quieres que haga algo más por ti?
- Si quieres, creo un instalador .exe compilado mediante GitHub Actions (necesitarás pegar tus secrets en GitHub). Dime **"Haz .exe en GitHub"** y te doy los pasos exactos.
- Si quieres que te guíe por teléfono/compartiendo pantalla, dímelo y te doy los pasos de validación.

FIN
