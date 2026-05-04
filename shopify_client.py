"""
Cliente HTTP para Shopify Admin API.
Maneja GraphQL, REST, rate limits y reintentos.
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def _configure_stdio_utf8() -> None:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass


_configure_stdio_utf8()
load_dotenv(Path(__file__).resolve().parent / ".env")

_raw_shop = (os.getenv("SHOP_DOMAIN") or "").strip()
_raw_shop = _raw_shop.replace("https://", "").replace("http://", "").split("/")[0]
SHOP_DOMAIN = _raw_shop.rstrip("/")
TOKEN = (os.getenv("ADMIN_API_TOKEN") or "").strip()
API_VERSION = "2025-01"

if not SHOP_DOMAIN or not TOKEN:
    raise SystemExit("[ERROR] Falta SHOP_DOMAIN o ADMIN_API_TOKEN en archivo .env")

if TOKEN.startswith("PEGA_AQUI"):
    raise SystemExit("[ERROR] Edita el archivo .env y pega tu token real")

GRAPHQL_URL = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/graphql.json"
REST_BASE = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}"

HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}


def graphql(query: str, variables: dict | None = None, max_retries: int = 3) -> dict:
    """Ejecuta query GraphQL con reintentos exponenciales."""
    for attempt in range(max_retries):
        try:
            r = requests.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": query, "variables": variables or {}},
                timeout=30,
            )
            
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"⏳ Rate limited. Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            if r.status_code == 401:
                raise SystemExit("[ERROR] Token invalido o expirado. Revisa .env")
            
            if r.status_code == 403:
                raise SystemExit(
                    f"[ERROR] Permisos insuficientes en token. Verifica scopes en Shopify admin.\nResponse: {r.text}"
                )
            
            if r.status_code >= 400:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"GraphQL HTTP {r.status_code}: {r.text}")
            
            data = r.json()
            
            if "errors" in data:
                if attempt < max_retries - 1:
                    print(f"[WARN] GraphQL errors (reintentando): {data['errors']}")
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            return data["data"]
        
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Error de red (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def rest(method: str, path: str, payload: dict | None = None, max_retries: int = 3) -> dict:
    """Llamada REST API (fallback para menús)."""
    url = f"{REST_BASE}{path}"
    for attempt in range(max_retries):
        try:
            r = requests.request(
                method, url, headers=HEADERS, json=payload, timeout=30
            )
            
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"⏳ Rate limit REST. Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            if r.status_code == 401:
                raise SystemExit("[ERROR] Token invalido")
            
            if r.status_code >= 400:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"REST {method} {path} -> {r.status_code}: {r.text}")
            
            return r.json() if r.text else {}
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    
    raise Exception(f"REST {method} {path}: máximo de reintentos excedido")


def validate_token() -> dict:
    """Valida que el token funcione. Retorna info de la tienda."""
    query = """
    query {
      shop {
        name
        myshopifyDomain
        plan { displayName }
        primaryDomain { url }
      }
    }
    """
    data = graphql(query)
    shop = data["shop"]
    plan = shop["plan"]["displayName"]
    print(f"✅ Token OK | Shop: {shop['name']} | Plan: {plan}")
    dom = shop.get("primaryDomain") or {}
    if dom.get("url"):
        print(f"   URL principal: {dom['url']}")
    return shop
