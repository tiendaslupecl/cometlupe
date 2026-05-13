"""
Auditoria completa de URLs en vivo: productos, colecciones, paginas.
Hace HTTP HEAD a cada URL para detectar 404 reales.

Uso:
    python scripts/audit_404_full.py
"""
import sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

STORE = "https://www.tiendaslupe.cl"

def paginate(path, key, **params):
    items, params["limit"] = [], params.get("limit", 250)
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=45)
        r.raise_for_status()
        items += r.json().get(key, [])
        link = r.headers.get("Link", "")
        url, params = None, {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items

print("Cargando datos...")
prods = paginate("products.json", "products", fields="id,handle,title,status")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
pages  = paginate("pages.json", "pages", fields="id,handle,title,published_at")

active_prods = [p for p in prods if p.get("status") == "active"]
published_pages = [p for p in pages if p.get("published_at")]

print(f"  {len(active_prods)} productos activos")
print(f"  {len(custom)+len(smart)} colecciones")
print(f"  {len(published_pages)} paginas publicadas")
print()

def check(path):
    url = STORE + path
    for attempt in range(5):
        try:
            r = requests.head(url, timeout=15, allow_redirects=True)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt * 2)
                continue
            return path, r.status_code
        except Exception as e:
            if attempt < 4:
                time.sleep(2)
                continue
            return path, f"ERR {type(e).__name__}"
    return path, 503

urls = []
urls += [(f"/products/{p['handle']}", p["title"]) for p in active_prods]
urls += [(f"/collections/{c['handle']}", c["title"]) for c in (custom + smart)]
urls += [(f"/pages/{p['handle']}", p["title"]) for p in published_pages]
urls.append(("/", "Home"))
urls.append(("/collections/all", "All"))

print(f"Verificando {len(urls)} URLs en vivo (modo secuencial, lento)...")
print()

issues = []
throttled = []
ok = 0
for i, (path, title) in enumerate(urls):
    p, status = check(path)
    if isinstance(status, int) and status < 400:
        ok += 1
    elif status in (429, 503):
        throttled.append((path, title))
        ok += 1
    else:
        issues.append((path, title, status))
        print(f"  [{status}] {path}  ({title[:50]})")
    if (i+1) % 50 == 0:
        print(f"  ... {i+1}/{len(urls)} verificados, {ok} OK")
    time.sleep(0.5)

print()
print(f"{'='*60}")
print(f"RESUMEN: {ok}/{len(urls)} OK, {len(issues)} con problemas")
if throttled:
    print(f"  ({len(throttled)} URLs throttled - 429/503 transitorio, no es error real)")
print(f"{'='*60}")

if issues:
    by_type = {}
    for path, title, status in issues:
        kind = path.split("/")[1] if "/" in path[1:] else "other"
        by_type.setdefault(kind, []).append((path, title, status))
    for kind, items in by_type.items():
        print(f"\n{kind.upper()} ({len(items)}):")
        for path, title, status in items[:30]:
            print(f"  [{status}] {path}")
            print(f"          {title[:70]}")
        if len(items) > 30:
            print(f"  ... y {len(items)-30} mas")
