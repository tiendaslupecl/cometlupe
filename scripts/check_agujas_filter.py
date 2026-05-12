"""Lista productos que el filtro de agujas estaria mostrando."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests
from collections import Counter

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

# Productos en maquinas-y-repuestos
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle")
smart = paginate("smart_collections.json", "smart_collections", fields="id,handle")
all_cols = custom + smart
maq = next((c for c in all_cols if c["handle"] == "maquinas-y-repuestos"), None)
prods = paginate(f"collections/{maq['id']}/products.json", "products", fields="id,title,tags,status")

print(f"Total en maquinas-y-repuestos: {len(prods)}")
print()

# Contar cuantos tienen el tag cat-agujas-maquina
con_tag = []
sin_tag = []
for p in prods:
    tags = {x.strip() for x in (p.get("tags","") or "").split(",") if x.strip()}
    if "cat-agujas-maquina" in tags:
        con_tag.append(p)
    else:
        sin_tag.append(p)

print(f"CON tag 'cat-agujas-maquina': {len(con_tag)}")
print(f"SIN tag 'cat-agujas-maquina': {len(sin_tag)}")
print()

# Todos los tags cat-* en productos CON cat-agujas-maquina
print("Todos los tags 'cat-*' en productos con cat-agujas-maquina:")
all_tags = Counter()
for p in con_tag:
    tags = {x.strip() for x in (p.get("tags","") or "").split(",") if x.strip()}
    for t in tags:
        if t.startswith("cat-"):
            all_tags[t] += 1
for t, n in all_tags.most_common():
    print(f"  {n:3d}  {t}")
print()

# Mostrar primeros 30 productos con el tag
print("Primeros 30 productos con tag cat-agujas-maquina:")
for p in con_tag[:30]:
    print(f"  [{p.get('status')}] {p['title'][:75]}")
