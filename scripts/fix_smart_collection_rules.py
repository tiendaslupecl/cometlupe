"""
Actualiza las reglas de smart collections para incluir todos los productos correctos.

Uso:
    python scripts/fix_smart_collection_rules.py --dry-run
    python scripts/fix_smart_collection_rules.py --apply
"""
import sys, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Nuevas reglas por handle de colección
UPDATES = {
    "prensatelas-para-maquina-de-cos": {
        "disjunctive": False,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "prensatela"},
        ],
    },
    "agujas-mano": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Aguja de Mano"},
            {"column": "title", "relation": "contains", "condition": "Aguja a Mano"},
            {"column": "title", "relation": "contains", "condition": "Aguja Circular"},
            {"column": "title", "relation": "contains", "condition": "Aguja de Tejer"},
            {"column": "title", "relation": "contains", "condition": "Aguja Tapiceria"},
            {"column": "title", "relation": "contains", "condition": "Aguja Lana"},
        ],
    },
    "herramientas-de-costura": {
        "disjunctive": True,
        "rules": [
            {"column": "tag",   "relation": "equals",   "condition": "cat-tijeras"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-alfileres"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-herramientas-costura"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-herramientas-marcado"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-herramientas-manuales"},
            {"column": "title", "relation": "contains", "condition": "Herramienta Manual"},
            {"column": "title", "relation": "contains", "condition": "Herramienta para Costura"},
        ],
    },
}

def get_smart_collections():
    r = requests.get(f"{REST_BASE}/smart_collections.json", headers=HEADERS,
                     params={"limit": 250}, timeout=30)
    r.raise_for_status()
    return {c["handle"]: c for c in r.json()["smart_collections"]}

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

print("Cargando smart collections...")
cols = get_smart_collections()
print()

for handle, new_config in UPDATES.items():
    col = cols.get(handle)
    if not col:
        print(f"  NO ENCONTRADA: {handle}")
        continue

    print(f"{'='*55}")
    print(f"Coleccion: {col['title']} ({handle})")
    print(f"  Reglas actuales (disjunctive={col.get('disjunctive')}):")
    for r in col.get("rules", []):
        print(f"    [{r['column']}] {r['relation']} '{r['condition']}'")
    print(f"  Reglas nuevas (disjunctive={new_config['disjunctive']}):")
    for r in new_config["rules"]:
        print(f"    [{r['column']}] {r['relation']} '{r['condition']}'")
    print()

    if args.apply:
        payload = {
            "smart_collection": {
                "id": col["id"],
                "disjunctive": new_config["disjunctive"],
                "rules": new_config["rules"],
            }
        }
        resp = requests.put(
            f"{REST_BASE}/smart_collections/{col['id']}.json",
            headers=HEADERS, json=payload, timeout=30
        )
        if resp.status_code == 200:
            print(f"  OK actualizada")
        else:
            print(f"  ERROR {resp.status_code}: {resp.text[:120]}")
    print()

if args.dry_run or not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
