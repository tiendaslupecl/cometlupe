"""
Expande las reglas de smart collections para que capturen mas productos.
Basado en el output de verify_product_collections.py.

Uso:
    python scripts/expand_smart_rules.py --dry-run
    python scripts/expand_smart_rules.py --apply
"""
import sys, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Nuevas reglas (agregar a las existentes; disjunctive=True)
UPDATES = {
    "hilos-bordar-profesionales": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Hilo Bordadora"},
            {"column": "title", "relation": "contains", "condition": "Hilo de Bordado"},
            {"column": "title", "relation": "contains", "condition": "Durafill"},
            {"column": "title", "relation": "contains", "condition": "Hilo de Bobina Bordadora"},
            {"column": "title", "relation": "contains", "condition": "Hilos de Bordar"},
        ],
    },
    "cintas-satin": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Cinta Satin"},
            {"column": "title", "relation": "contains", "condition": "Cinta Satín"},
            {"column": "title", "relation": "contains", "condition": "Cinta Satinada"},
            {"column": "title", "relation": "contains", "condition": "Cinta de Raso"},
        ],
    },
    "broches": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Broche"},
            {"column": "title", "relation": "contains", "condition": "Matriz Ojetilladora"},
            {"column": "title", "relation": "contains", "condition": "Prensa Ojetilladora"},
            {"column": "title", "relation": "contains", "condition": "Ojetilladora"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-broches"},
        ],
    },
    "lentejuelas-y-strass": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Lentejuela"},
            {"column": "title", "relation": "contains", "condition": "Strass"},
            {"column": "title", "relation": "contains", "condition": "Aplicador Strass"},
            {"column": "title", "relation": "contains", "condition": "Aplicador de Strass"},
            {"column": "title", "relation": "contains", "condition": "Pegadora de Perlas"},
        ],
    },
    "sesgo-bies": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Sesgo"},
            {"column": "title", "relation": "contains", "condition": "Bies"},
            {"column": "title", "relation": "contains", "condition": "Formador de Bies"},
        ],
    },
    "tinturas": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Tintura"},
            {"column": "title", "relation": "contains", "condition": "Anilina"},
        ],
    },
    "cintas-algodon": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Cinta Algodon"},
            {"column": "title", "relation": "contains", "condition": "Cinta Algodón"},
            {"column": "title", "relation": "contains", "condition": "Cinta de Algodon"},
            {"column": "title", "relation": "contains", "condition": "Cinta de Algodón"},
            {"column": "title", "relation": "contains", "condition": "Cinta de Lona Algodon"},
            {"column": "title", "relation": "contains", "condition": "Cinta de Lona Algodón"},
            {"column": "title", "relation": "contains", "condition": "Cinta Lona Algodon"},
            {"column": "title", "relation": "contains", "condition": "Cinta Lona Algodón"},
        ],
    },
    "materiales-para-manualidades": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Hilo de Pesca"},
            {"column": "title", "relation": "contains", "condition": "Materiales para Manualidades"},
            {"column": "tag",   "relation": "equals",   "condition": "cat-materiales-manualidades"},
            {"column": "tag",   "relation": "equals",   "condition": "materiales-manualidades"},
        ],
    },
    # herramientas-de-costura: ya tiene 7 reglas, agregamos mas titulos
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
            {"column": "title", "relation": "contains", "condition": "Brocha Limpiadora"},
            {"column": "title", "relation": "contains", "condition": "Pinza Sujetadora"},
            {"column": "title", "relation": "contains", "condition": "Clips para Tela"},
            {"column": "title", "relation": "contains", "condition": "Pistola de Silicona"},
            {"column": "title", "relation": "contains", "condition": "Volteador"},
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
    print(f"{col['title']} ({handle})")
    print(f"  Reglas actuales (disjunctive={col.get('disjunctive')}):")
    for r in col.get("rules", []):
        print(f"    [{r['column']}] {r['relation']} '{r['condition']}'")
    print(f"  Reglas NUEVAS (disjunctive={new_config['disjunctive']}):")
    for r in new_config["rules"]:
        print(f"    [{r['column']}] {r['relation']} '{r['condition']}'")
    print()

    if args.apply:
        payload = {"smart_collection": {
            "id": col["id"],
            "disjunctive": new_config["disjunctive"],
            "rules": new_config["rules"],
        }}
        resp = requests.put(
            f"{REST_BASE}/smart_collections/{col['id']}.json",
            headers=HEADERS, json=payload, timeout=30
        )
        if resp.status_code == 200:
            print(f"  OK actualizada")
        else:
            print(f"  ERROR {resp.status_code}: {resp.text[:120]}")
        print()

if not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
