"""
Follow-up:
1. Quitar 'Aguja de Mano Singer' de aguja-maquina-casera
2. Actualizar regla smart de accesorios-maquina para capturar tornillos/planchas/etc.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests, time

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

# 1. Quitar Aguja de Mano de aguja-maquina-casera
print("1. Limpiando aguja-maquina-casera de agujas de mano...")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle")
cas_col = next((c for c in custom if c["handle"] == "aguja-maquina-casera"), None)
if cas_col:
    cas_prods = paginate(f"collections/{cas_col['id']}/products.json", "products", fields="id,title")
    keywords_mano = ["aguja de mano", "aguja a mano", "aguja circular",
                     "aguja de tejer", "aguja tapiceria", "aguja tapicería",
                     "aguja lana", "aguja bordado a mano"]
    to_remove = [p for p in cas_prods
                 if any(k in p["title"].lower() for k in keywords_mano)]
    print(f"   Encontrados {len(to_remove)} a quitar de casera:")
    for p in to_remove:
        print(f"     - {p['title'][:60]}")

    # Obtener collect IDs
    collects = paginate("collects.json", "collects", fields="id,product_id,collection_id")
    by_pair = {(c["product_id"], c["collection_id"]): c["id"] for c in collects}

    for p in to_remove:
        cid = by_pair.get((p["id"], cas_col["id"]))
        if cid:
            r = requests.delete(f"{REST_BASE}/collects/{cid}.json", headers=HEADERS, timeout=30)
            print(f"     HTTP {r.status_code} - quitado")
        time.sleep(0.15)

# 2. Actualizar regla smart de accesorios-maquina
print()
print("2. Actualizando regla smart de accesorios-maquina...")
smart = paginate("smart_collections.json", "smart_collections", fields="id,handle,rules,disjunctive")
acc = next((c for c in smart if c["handle"] == "accesorios-maquina"), None)
if not acc:
    print("   NOTA: accesorios-maquina no es smart (o no existe)")
else:
    print(f"   Reglas actuales (disjunctive={acc.get('disjunctive')}):")
    for r in acc.get("rules", []):
        print(f"     [{r['column']}] {r['relation']} '{r['condition']}'")
    new_rules = list(acc.get("rules", []))
    extras = [
        {"column":"title","relation":"contains","condition":"Aguja Tornillo"},
        {"column":"title","relation":"contains","condition":"Plancha de Aguja"},
        {"column":"title","relation":"contains","condition":"Plancha Aguja"},
        {"column":"title","relation":"contains","condition":"Tornillo de Aguja"},
        {"column":"title","relation":"contains","condition":"Tornillo de Diente"},
        {"column":"title","relation":"contains","condition":"Tornillo de Plancha de Aguja"},
        {"column":"title","relation":"contains","condition":"Tornillo para Maquina"},
        {"column":"title","relation":"contains","condition":"Tornillo para Máquina"},
        {"column":"tag",  "relation":"equals",   "condition":"cat-accesorios-maquina"},
    ]
    existing = {(r["column"], r["relation"], r["condition"].lower()) for r in new_rules}
    added = 0
    for e in extras:
        key = (e["column"], e["relation"], e["condition"].lower())
        if key not in existing:
            new_rules.append(e)
            added += 1

    payload = {"smart_collection": {
        "id": acc["id"],
        "disjunctive": True,
        "rules": new_rules,
    }}
    rr = requests.put(f"{REST_BASE}/smart_collections/{acc['id']}.json",
                      headers=HEADERS, json=payload, timeout=30)
    print(f"   HTTP {rr.status_code}, {added} reglas agregadas")
    print(f"   Reglas finales:")
    for r in new_rules:
        print(f"     [{r['column']}] {r['relation']} '{r['condition']}'")
