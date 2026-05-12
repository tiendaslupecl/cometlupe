"""
Arregla la regla smart de accesorios-maquina (que rompimos antes):
- Revierte a disjunctive=False con regla 'tag = cat-accesorios-maquina'
- Agrega el tag cat-accesorios-maquina a los 6 tornillos/planchas
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

# 1. Revertir regla smart de accesorios-maquina
print("1. Revertiendo regla de accesorios-maquina...")
smart = paginate("smart_collections.json", "smart_collections", fields="id,handle")
acc = next((c for c in smart if c["handle"] == "accesorios-maquina"), None)
if acc:
    payload = {"smart_collection": {
        "id": acc["id"],
        "disjunctive": False,
        "rules": [
            {"column":"tag","relation":"equals","condition":"cat-accesorios-maquina"},
            {"column":"title","relation":"not_contains","condition":"Prénsatela"},
        ],
    }}
    r = requests.put(f"{REST_BASE}/smart_collections/{acc['id']}.json",
                     headers=HEADERS, json=payload, timeout=30)
    print(f"   HTTP {r.status_code} - revertida a AND con tag cat-accesorios-maquina")
print()

# 2. Buscar productos que deberian tener el tag (los 6 falsos agujas + similares)
print("2. Buscando productos para taggear con cat-accesorios-maquina...")
all_prods = paginate("products.json", "products", fields="id,title,tags,status")

KEYWORDS = [
    "aguja tornillo", "plancha de aguja", "plancha aguja",
    "tornillo de aguja", "tornillo de diente",
    "tornillo de plancha de aguja",
    "tornillo para maquina", "tornillo para máquina",
]

targets = []
for p in all_prods:
    if p.get("status") != "active": continue
    t = p["title"].lower()
    if any(k in t for k in KEYWORDS):
        existing_tags = {x.strip() for x in (p.get("tags","") or "").split(",") if x.strip()}
        if "cat-accesorios-maquina" not in existing_tags:
            targets.append((p, existing_tags))

print(f"   {len(targets)} productos a taggear:")
for p, _ in targets[:15]:
    print(f"     - {p['title'][:65]}")
print()

# 3. Aplicar tags
print("3. Aplicando tags...")
ok = err = 0
for p, existing_tags in targets:
    new_tags = sorted(existing_tags | {"cat-accesorios-maquina"})
    r = requests.put(f"{REST_BASE}/products/{p['id']}.json", headers=HEADERS,
                     json={"product": {"id": p["id"], "tags": ", ".join(new_tags)}},
                     timeout=30)
    if r.status_code == 200:
        ok += 1
        print(f"   OK  {p['title'][:60]}")
    else:
        err += 1
        print(f"   ERR {p['title'][:50]} HTTP {r.status_code}")
    time.sleep(0.2)

print(f"\nOK {ok} / ERR {err}")
