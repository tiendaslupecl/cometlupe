import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

APPLY = "--apply" in sys.argv

def norm(s):
    s = s.lower()
    for a, b in [("\u00e1","a"),("\u00e9","e"),("\u00ed","i"),("\u00f3","o"),("\u00fa","u"),("\u00f1","n")]:
        s = s.replace(a, b)
    return s

def paginate(path, key, **params):
    items, params["limit"] = [], params.get("limit", 250)
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

print("Cargando colecciones...")
all_cols = []
for kind in ("custom_collections","smart_collections"):
    all_cols += paginate(f"{kind}.json", kind, fields="id,handle")
cols = {c["handle"]: c["id"] for c in all_cols}

REPUESTOS = cols.get("repuestos-maquinas-de-coser")
PRENSATELAS = cols.get("prensatelas-para-maquina-de-cos")
HEBILLAS = cols.get("hebillas")
PRENSATELA_KEYS = ["prensatela","zapatilla","pie cierre","pie patchwork","pie teflon"]

def get_collects(product_id, collection_id):
    r = requests.get(f"{REST_BASE}/collects.json", headers=HEADERS,
                     params={"product_id": product_id, "collection_id": collection_id}, timeout=30)
    return r.json().get("collects", [])

def add_to_collection(product_id, collection_id):
    r = requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
                      json={"collect":{"product_id":product_id,"collection_id":collection_id}}, timeout=30)
    return r.status_code in (200,201)

def remove_from_collection(product_id, collection_id):
    for c in get_collects(product_id, collection_id):
        requests.delete(f"{REST_BASE}/collects/{c['id']}.json", headers=HEADERS, timeout=30)

print()
print("=== Prensatelas en repuestos-maquinas-de-coser ===")
prods = paginate(f"collections/{REPUESTOS}/products.json", "products", fields="id,title")
moved = 0
for p in prods:
    t = norm(p["title"])
    if any(k in t for k in PRENSATELA_KEYS):
        already = bool(get_collects(p["id"], PRENSATELAS))
        action = "remove" if already else "move"
        print(f"  [{action}] {p['title'][:65]}")
        if APPLY:
            if not already:
                add_to_collection(p["id"], PRENSATELAS)
                time.sleep(0.6)
            remove_from_collection(p["id"], REPUESTOS)
            time.sleep(0.6)
            moved += 1

print()
print("=== Mosquetones en hebillas ===")
removed = 0
for p in paginate(f"collections/{HEBILLAS}/products.json", "products", fields="id,title"):
    if "mosqueton" in norm(p["title"]):
        print(f"  [remove] {p['title'][:65]}")
        if APPLY:
            remove_from_collection(p["id"], HEBILLAS)
            time.sleep(0.6)
            removed += 1

print()
if APPLY:
    print(f"OK: {moved} prensatelas movidas, {removed} mosquetones removidos")
else:
    print("DRY-RUN. Corre con --apply para aplicar.")