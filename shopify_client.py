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
    saw_rate_limit = False
    for attempt in range(max_retries):
        try:
            r = requests.post(
                GRAPHQL_URL,
                headers=HEADERS,
                json={"query": query, "variables": variables or {}},
                timeout=30,
            )
            
            if r.status_code == 429:
                saw_rate_limit = True
                wait = 2 ** attempt
                print(f"⏳ Rate limited. Esperando {wait}s...")
                time.sleep(wait)
                continue
            
            saw_rate_limit = False
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
    if saw_rate_limit:
        raise Exception(
            f"GraphQL HTTP 429 persistente tras {max_retries} intentos"
        )
    raise Exception("GraphQL: máximo de reintentos excedido sin respuesta válida")


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


_ONLINE_STORE_PUBLICATION_ID: str | None = None
_ONLINE_STORE_PUBLISH_UNAVAILABLE = False


def get_online_store_publication_id() -> str | None:
    """GID de la publicación «Online Store» / «Tienda online» para publicar recursos."""
    global _ONLINE_STORE_PUBLICATION_ID, _ONLINE_STORE_PUBLISH_UNAVAILABLE
    if _ONLINE_STORE_PUBLISH_UNAVAILABLE:
        return None
    if _ONLINE_STORE_PUBLICATION_ID:
        return _ONLINE_STORE_PUBLICATION_ID
    q = """
    query pubs {
      publications(first: 40) {
        nodes { id name }
      }
    }
    """
    try:
        data = graphql(q, max_retries=1)
    except Exception as exc:
        _ONLINE_STORE_PUBLISH_UNAVAILABLE = True
        print(
            "⚠️ No se puede publicar colecciones en Tienda online sin scopes "
            "`read_publications` y `write_publications`. Añádelos a la app y reinstala."
        )
        print(f"   Detalle: {exc}")
        return None
    for node in data.get("publications", {}).get("nodes", []):
        name = (node.get("name") or "").strip().lower()
        if "online store" in name or "tienda online" in name:
            _ONLINE_STORE_PUBLICATION_ID = node["id"]
            return _ONLINE_STORE_PUBLICATION_ID
    print("⚠️ No se encontró la publicación Online Store en publications.")
    _ONLINE_STORE_PUBLISH_UNAVAILABLE = True
    return None


def publish_resource_to_online_store(resource_gid: str) -> bool:
    """
    Publica un recurso (colección, etc.) en el canal Tienda online.
    Evita 404 en el escaparate cuando la colección existe en Admin pero no está publicada.
    """
    pub_id = get_online_store_publication_id()
    if not pub_id:
        return False
    mutation = """
    mutation publishablePublish($id: ID!, $input: [PublicationInput!]!) {
      publishablePublish(id: $id, input: $input) {
        userErrors { field message }
        publishable {
          ... on Collection { id handle }
        }
      }
    }
    """
    try:
        result = graphql(
            mutation,
            {"id": resource_gid, "input": [{"publicationId": pub_id}]},
            max_retries=1,
        )
    except Exception as exc:
        print(f"⚠️ publishablePublish omitido: {exc}")
        return False
    block = result.get("publishablePublish") or {}
    errs = block.get("userErrors") or []
    if errs:
        msgs = [str(e.get("message", e)).lower() for e in errs]
        if any("already" in m or "published" in m for m in msgs):
            return True
        print(f"⚠️ publishablePublish: {errs}")
        return False
    return True


def print_store_tier_and_checklist(shop: dict) -> None:
    """Aclara Shopify Plus vs automatización y checklist para tienda lista en producción."""
    plan = (shop.get("plan") or {}).get("displayName") or "desconocido"
    print("\n📌 Plan comercial y Shopify Plus")
    print(f"   Plan detectado en Admin: {plan}")
    if "plus" not in plan.lower():
        print(
            "   Shopify Plus no se «activa» con este script: es un plan empresarial "
            "contratable con Shopify (límites API más altos, Checkout extensible, "
            "B2B avanzado, organización multi‑tienda). Información: "
            "https://www.shopify.com/plus"
        )
    else:
        print("   Tienes Shopify Plus: revisa límites de API y Checkout según tus apps.")

    print(
        "\n📌 Checklist para que la tienda quede sólida (cualquier plan pago):\n"
        "   1) App «Lupe Automation»: scopes Admin API completos (ver .env.example).\n"
        "   2) Tras cambiar scopes: guardar app → Instalar de nuevo → nuevo token en .env.\n"
        "   3) Sin 404 en colecciones: read_publications + write_publications "
        "(este repo publica al canal Tienda online).\n"
        "   4) Menú: read/write online_store_navigation (REST menús o GraphQL menuUpdate).\n"
        "   5) CONTACT_PAGE_PATH si tu página no es /pages/contacto.\n"
        "   6) Search & Discovery (filtros) + «Habilitar filtrado» en tema Xtra (manual).\n"
        "   7) SKIP_STORE_PUBLISH=1 en .env solo si publicas colecciones solo desde Admin."
    )
