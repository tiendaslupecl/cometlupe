"""
Reestructura agujas:
1. aguja-maquina-casera = solo Schmetz y Singer
2. aguja-maquina-industrial = talon delgado/grueso, overlock, bordadora,
   Groz, Beckert, DBx, DBK, etc.
3. Menu: bajo "Agujas" agrega subcategorias Casera e Industrial

Uso:
    python scripts/fix_agujas.py --dry-run
    python scripts/fix_agujas.py --apply
"""
import sys, argparse
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

store_admin = REST_BASE.split("/admin/")[0]
GRAPHQL = f"{store_admin}/admin/api/2024-01/graphql.json"

# Reglas smart actualizadas
RULES_UPDATES = {
    "aguja-maquina-casera": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Schmetz"},
            {"column": "title", "relation": "contains", "condition": "Singer"},
            {"column": "title", "relation": "contains", "condition": "Aguja Casera"},
            {"column": "title", "relation": "contains", "condition": "Aguja Domestica"},
            {"column": "title", "relation": "contains", "condition": "Aguja Doméstica"},
            {"column": "title", "relation": "contains", "condition": "Aguja para Maquina Casera"},
            {"column": "title", "relation": "contains", "condition": "Aguja para Máquina Casera"},
        ],
    },
    "aguja-maquina-industrial": {
        "disjunctive": True,
        "rules": [
            {"column": "title", "relation": "contains", "condition": "Aguja Industrial"},
            {"column": "title", "relation": "contains", "condition": "Aguja para Maquina Industrial"},
            {"column": "title", "relation": "contains", "condition": "Aguja para Máquina Industrial"},
            {"column": "title", "relation": "contains", "condition": "Aguja Overlock"},
            {"column": "title", "relation": "contains", "condition": "Aguja Collareta"},
            {"column": "title", "relation": "contains", "condition": "Aguja Recta Industrial"},
            {"column": "title", "relation": "contains", "condition": "Aguja Bordadora"},
            {"column": "title", "relation": "contains", "condition": "Aguja para Bordadora"},
            {"column": "title", "relation": "contains", "condition": "Aguja de Bordadora"},
            {"column": "title", "relation": "contains", "condition": "Talon Delgado"},
            {"column": "title", "relation": "contains", "condition": "Talón Delgado"},
            {"column": "title", "relation": "contains", "condition": "Talon Grueso"},
            {"column": "title", "relation": "contains", "condition": "Talón Grueso"},
            {"column": "title", "relation": "contains", "condition": "Groz"},
            {"column": "title", "relation": "contains", "condition": "Beckert"},
            {"column": "title", "relation": "contains", "condition": "DBx"},
            {"column": "title", "relation": "contains", "condition": "DBK"},
            {"column": "title", "relation": "contains", "condition": "UY128"},
            {"column": "title", "relation": "contains", "condition": "DAx"},
        ],
    },
}

def gql(query, variables=None):
    r = requests.post(GRAPHQL, headers={**HEADERS, "Content-Type":"application/json"},
                      json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL: {data['errors']}")
    return data["data"]

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

# 1. Mostrar reglas actuales
print("Cargando smart collections...")
r = requests.get(f"{REST_BASE}/smart_collections.json", headers=HEADERS,
                 params={"limit": 250}, timeout=30)
smart = {c["handle"]: c for c in r.json()["smart_collections"]}

for handle, cfg in RULES_UPDATES.items():
    col = smart.get(handle)
    if not col:
        print(f"  NO ENCONTRADA: {handle}")
        continue
    print(f"\n{'='*55}")
    print(f"{col['title']} ({handle})")
    print(f"  Reglas actuales:")
    for rl in col.get("rules", []):
        print(f"    [{rl['column']}] {rl['relation']} '{rl['condition']}'")
    print(f"  Reglas nuevas (disjunctive={cfg['disjunctive']}):")
    for rl in cfg["rules"]:
        print(f"    [{rl['column']}] {rl['relation']} '{rl['condition']}'")

# 2. Mostrar plan de menu
print(f"\n{'='*55}")
print("MENU UPDATE: agregar sub-sub items bajo 'Agujas'")
print(f"{'='*55}")
q = """{menus(first:20){edges{node{id handle title items{
  id title type url tags resourceId
  items{id title type url tags resourceId
    items{id title type url tags resourceId}}
}}}}}"""
menus = [e["node"] for e in gql(q)["menus"]["edges"]]
main = next((m for m in menus if m["handle"] == "main-menu"), None)
if not main:
    raise SystemExit("main-menu no encontrado")

def item_to_input(it):
    out = {"title": it["title"], "type": it["type"], "url": it["url"]}
    if it.get("tags"): out["tags"] = it["tags"]
    if it.get("resourceId"): out["resourceId"] = it["resourceId"]
    if it.get("items"):
        out["items"] = [item_to_input(s) for s in it["items"]]
    return out

# Construir nuevo arbol de menu agregando sub items bajo 'Agujas'
new_items = []
for it in main["items"]:
    new_it = item_to_input(it)
    # Buscar item Agujas en submenu de Maquinas y Repuestos
    if it["title"].lower() in ("máquinas y repuestos", "maquinas y repuestos"):
        new_subs = []
        for sub in new_it.get("items", []):
            if sub["title"].lower() == "agujas":
                # Reemplazar con un item que tiene 2 sub-sub items
                sub_with_children = {
                    "title": sub["title"],
                    "type": sub["type"],
                    "url": sub["url"],
                    "items": [
                        {"title": "Aguja Máquina Casera",
                         "type": "HTTP",
                         "url": "https://www.tiendaslupe.cl/collections/aguja-maquina-casera"},
                        {"title": "Aguja Máquina Industrial",
                         "type": "HTTP",
                         "url": "https://www.tiendaslupe.cl/collections/aguja-maquina-industrial"},
                    ],
                }
                new_subs.append(sub_with_children)
                print(f"  Agregando bajo 'Agujas':")
                print(f"    - Aguja Maquina Casera -> /collections/aguja-maquina-casera")
                print(f"    - Aguja Maquina Industrial -> /collections/aguja-maquina-industrial")
            else:
                new_subs.append(sub)
        new_it["items"] = new_subs
    new_items.append(new_it)

print()
if not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
    sys.exit(0)

# 3. Aplicar reglas smart
print("\nAplicando reglas smart...")
for handle, cfg in RULES_UPDATES.items():
    col = smart.get(handle)
    if not col: continue
    payload = {"smart_collection": {
        "id": col["id"],
        "disjunctive": cfg["disjunctive"],
        "rules": cfg["rules"],
    }}
    rr = requests.put(f"{REST_BASE}/smart_collections/{col['id']}.json",
                      headers=HEADERS, json=payload, timeout=30)
    if rr.status_code == 200:
        print(f"  OK {handle}")
    else:
        print(f"  ERR {handle} HTTP {rr.status_code}: {rr.text[:120]}")

# 4. Aplicar menu update
print("\nActualizando menu...")
m = """mutation menuUpdate($id:ID!,$title:String!,$handle:String!,$items:[MenuItemUpdateInput!]!){
  menuUpdate(id:$id,title:$title,handle:$handle,items:$items){
    menu{id} userErrors{field message}
  }
}"""
resp = gql(m, {"id": main["id"], "title": main["title"], "handle": main["handle"], "items": new_items})
if resp["menuUpdate"].get("userErrors"):
    for e in resp["menuUpdate"]["userErrors"]:
        print(f"  ERROR: {e['field']}: {e['message']}")
else:
    print(f"  OK menu actualizado")
