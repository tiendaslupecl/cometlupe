#!/usr/bin/env bash
# Shopify Comet - start server and open browser
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js no encontrado. Instalar Node.js desde https://nodejs.org/"
  exit 1
fi
(cd server && node index.js) &
sleep 1
# open default browser
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:3000/"
elif command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:3000/"
else
  echo "Abre http://127.0.0.1:3000/ en tu navegador."
fi
