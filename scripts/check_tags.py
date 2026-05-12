"""Verifica que los productos en maquinas-y-repuestos sigan teniendo sus tags cat-*."""
import sys
from pathlib import Path
from collections import Counter

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

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

# Get maquinas-y-repuestos collection id
cols = paginate("smart_collections.json", "smart_collections", fields="id,handle")
cols += paginate("custom_collections.json", "custom_collections", fields="id,handle")
maq = next((c for c in cols if c["handle"] == "maquinas-y-repuestos"), None)
ins = next((c for c in cols if c["handle"] == "insumos-confeccion"), None)

for col, label in [(maq, "maquinas-y-repuestos"), (ins, "insumos-confeccion")]:
    if not col:
        print(f"NO ENCONTRADA: {label}")
        continue
    print(f"\n{'='*55}")
    print(f"COLECCION: {label} (id={col['id']})")
    products = paginate(f"collections/{col['id']}/products.json", "products",
                        fields="id,title,tags")
    print(f"Total productos: {len(products)}")

    # Count tags starting with "cat-"
    cat_tags = Counter()
    no_cat = 0
    for p in products:
        tags = [t.strip() for t in (p.get("tags") or "").split(",") if t.strip()]
        cats = [t for t in tags if t.startswith("cat-")]
        if cats:
            for c in cats:
                cat_tags[c] += 1
        else:
            no_cat += 1

    print(f"Productos sin tag cat-*: {no_cat}")
    print("Tags cat-* mas comunes:")
    for tag, n in cat_tags.most_common(20):
        print(f"  {n:4d}  {tag}")
