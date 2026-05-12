"""
Limpia el tag 'cat-agujas-maquina' de productos que no son agujas reales
(tornillos, planchas, etc.) para que el filtro del menu muestre solo agujas.
"""
import sys, time
from pathlib import Path
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
        link = r.headers.get("Link", "")
        url, params = None, {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items

# Buscar productos con tag cat-agujas-maquina pero que NO son agujas reales
print("Buscando productos con tag 'cat-agujas-maquina'...")
all_prods = paginate("products.json", "products", fields="id,title,tags,status")

FALSE_AGUJA_KEYWORDS = [
    "aguja tornillo", "tornillo de aguja", "tornillo de diente",
    "tornillo de plancha", "tornillo para maquina", "tornillo para máquina",
    "plancha de aguja", "plancha aguja",
    "guarda aguja", "guarda-aguja",
    "guia aguja", "guía aguja", "guia de aguja", "guía de aguja",
    "barra de aguja", "barra aguja",
    "soporte aguja", "soporte de aguja",
    "porta aguja", "porta-aguja",
    "placa aguja", "placa de aguja",
]

targets = []
for p in all_prods:
    if p.get("status") != "active": continue
    tags = {x.strip() for x in (p.get("tags","") or "").split(",") if x.strip()}
    if "cat-agujas-maquina" not in tags:
        continue
    t = p["title"].lower()
    is_false = any(k in t for k in FALSE_AGUJA_KEYWORDS)
    if is_false:
        targets.append((p, tags))

print(f"  {len(targets)} productos a destaggear:")
for p, _ in targets:
    print(f"    - {p['title'][:70]}")
print()

if not targets:
    print("Nada que hacer.")
    sys.exit(0)

print("Aplicando cambios...")
ok = err = 0
for p, tags in targets:
    new_tags = sorted(tags - {"cat-agujas-maquina", "cat-agujas"})
    r = requests.put(f"{REST_BASE}/products/{p['id']}.json", headers=HEADERS,
                     json={"product": {"id": p["id"], "tags": ", ".join(new_tags)}},
                     timeout=30)
    if r.status_code == 200:
        ok += 1
        print(f"  OK  {p['title'][:60]}")
    else:
        err += 1
        print(f"  ERR {p['title'][:50]} HTTP {r.status_code}")
    time.sleep(0.2)

print(f"\nOK {ok} / ERR {err}")
