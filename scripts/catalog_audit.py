"""
Auditoría del catálogo: productos sin colección específica, mal categorizados,
colecciones duplicadas o vacías.
"""
import sys, time
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

GENERIC = {
    "top-65-favoritos", "catalogo-completo",
    "insumos-de-confeccion", "insumos-confeccion",
}

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

print("🔍 Obteniendo colecciones...")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
all_cols = custom + smart
cols_by_handle = {c["handle"]: c for c in all_cols}
print(f"   {len(all_cols)} colecciones")

print("🔍 Obteniendo productos...")
products = paginate("products.json", "products", fields="id,title,handle,product_type")
prod_by_id = {p["id"]: p for p in products}
print(f"   {len(products)} productos")

print("🔍 Mapeando colecciones → productos...")
prod_cols = defaultdict(list)   # product_id → [handles]
col_counts = {}                 # handle → product count
for col in all_cols:
    prods = paginate(f"collections/{col['id']}/products.json", "products", fields="id")
    col_counts[col["handle"]] = len(prods)
    for p in prods:
        prod_cols[p["id"]].append(col["handle"])
    time.sleep(0.12)
print()

# ── 1. Colecciones duplicadas (mismo título, distinto handle) ────────────────
print("=" * 60)
print("1. COLECCIONES DUPLICADAS (mismo título)")
print("=" * 60)
by_title = defaultdict(list)
for c in all_cols:
    by_title[c["title"].strip().lower()].append(c)
dups = {t: cs for t, cs in by_title.items() if len(cs) > 1}
if dups:
    for title, cols in sorted(dups.items()):
        print(f"  \"{title}\"")
        for c in cols:
            print(f"    handle={c['handle']:40s} productos={col_counts.get(c['handle'],0)}")
else:
    print("  Ninguna.")
print()

# ── 2. Colecciones vacías ────────────────────────────────────────────────────
print("=" * 60)
print("2. COLECCIONES VACÍAS")
print("=" * 60)
empty = [(c["handle"], c["title"]) for c in all_cols if col_counts.get(c["handle"], 0) == 0]
if empty:
    for h, t in sorted(empty):
        print(f"  {h:45s} → {t}")
else:
    print("  Ninguna.")
print()

# ── 3. Productos SOLO en colecciones genéricas ───────────────────────────────
print("=" * 60)
print("3. PRODUCTOS SIN COLECCIÓN ESPECÍFICA (solo en genéricas)")
print("=" * 60)
only_generic = []
for p in products:
    specific = [h for h in prod_cols.get(p["id"], []) if h not in GENERIC]
    if not specific:
        only_generic.append(p)
print(f"  {len(only_generic)} productos sin colección específica:")
for p in only_generic[:50]:
    print(f"  [{p['id']}] {p['title'][:60]}")
if len(only_generic) > 50:
    print(f"  ... y {len(only_generic)-50} más")
print()

# ── 4. Resumen de colecciones por tamaño ────────────────────────────────────
print("=" * 60)
print("4. RESUMEN COLECCIONES (ordenado por cantidad de productos)")
print("=" * 60)
for h, count in sorted(col_counts.items(), key=lambda x: -x[1]):
    if h not in GENERIC:
        title = cols_by_handle[h]["title"]
        print(f"  {count:4d}  {h:45s} {title}")
print()
print(f"Total: {len(products)} productos / {len(all_cols)} colecciones")
