"""
Crea la coleccion Hilo de Jeans, agrega productos y la muestra para el menu.
Uso: python scripts/create_hilo_jeans.py
"""
import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

JEANS_KEYWORDS = ["jeans", "jean", "hilo de pesca"]
COLLECTION_TITLE = "Hilo de Jeans"
COLLECTION_HANDLE = "hilo-jeans"

def paginate(path, key, **params):
    items, params["limit"] = [], 250
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=45)
        r.raise_for_status()
        items += r.json().get(key, [])
        link, url, params = r.headers.get("Link", ""), None, {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items

print("Buscando coleccion existente...")
existing = paginate("custom_collections.json", "custom_collections", handle=COLLECTION_HANDLE, fields="id,handle,title")
if existing:
    col_id = existing[0]["id"]
    print(f"  Ya existe: id={col_id}")
else:
    print("  Creando coleccion...")
    r = requests.post(f"{REST_BASE}/custom_collections.json", headers=HEADERS, json={
        "custom_collection": {
            "title": COLLECTION_TITLE,
            "handle": COLLECTION_HANDLE,
            "published": True,
            "sort_order": "best-selling",
        }
    }, timeout=30)
    r.raise_for_status()
    col_id = r.json()["custom_collection"]["id"]
    print(f"  Creada: id={col_id}")

print("Buscando productos de hilo jeans...")
all_prods = paginate("products.json", "products", fields="id,title,status")
jeans_prods = [p for p in all_prods if p.get("status") == "active"
               and any(kw in p["title"].lower() for kw in JEANS_KEYWORDS)]
print(f"  {len(jeans_prods)} productos encontrados")
for p in jeans_prods:
    print(f"    - {p['title'][:70]}")

print("\nAgregando productos a la coleccion...")
existing_collects = paginate("collects.json", "collects", collection_id=col_id, fields="product_id")
already_in = {c["product_id"] for c in existing_collects}
added = 0
for p in jeans_prods:
    if p["id"] in already_in:
        print(f"  ya esta: {p['title'][:50]}")
        continue
    r = requests.post(f"{REST_BASE}/collects.json", headers=HEADERS, json={
        "collect": {"product_id": p["id"], "collection_id": col_id}
    }, timeout=30)
    if r.status_code in (200, 201):
        print(f"  + {p['title'][:60]}")
        added += 1
    else:
        print(f"  ERROR {r.status_code}: {p['title'][:50]}")
    time.sleep(0.2)

print(f"\n{added} productos agregados.")
print(f"\nPara agregar al menu: Shopify Admin -> Navigation -> menu principal -> Add menu item")
print(f"  Nombre: {COLLECTION_TITLE}  |  URL: /collections/{COLLECTION_HANDLE}")
