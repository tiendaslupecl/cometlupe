"""
Arregla los 404s detectados:
1. Cambia link 'Contacto' del menu principal de /pages/contacto -> /pages/contact
2. Elimina las 3 colecciones de prensatelas duplicadas vacias

Uso:
    python scripts/fix_404s.py --dry-run
    python scripts/fix_404s.py --apply
"""
import sys, argparse
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

store_admin = REST_BASE.split("/admin/")[0]
GRAPHQL = f"{store_admin}/admin/api/2024-01/graphql.json"

DUPLICATE_COLLECTIONS = [
    "prensatelas-caseros",
    "prensatelas-industriales",
    "prensatelas-industriales-1",
]

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

# 1. Obtener menu principal
print("Cargando menu principal...")
q = """{menus(first:20){edges{node{id handle title items{
  id title type url tags resourceId
  items{id title type url tags resourceId
    items{id title type url tags resourceId}
  }
}}}}}"""
menus = [e["node"] for e in gql(q)["menus"]["edges"]]
main = next((m for m in menus if m["handle"] == "main-menu"), None)
if not main:
    raise SystemExit("main-menu no encontrado")

def item_to_input(it):
    out = {"title": it["title"], "type": it["type"], "url": it["url"]}
    # Fix: Contacto -> /pages/contact
    if it["title"].lower() in ("contacto","contact") and it["url"].endswith("/pages/contacto"):
        out["url"] = it["url"].replace("/pages/contacto", "/pages/contact")
        print(f"  FIX: '{it['title']}' {it['url']} -> {out['url']}")
    if it.get("tags"): out["tags"] = it["tags"]
    if it.get("resourceId"): out["resourceId"] = it["resourceId"]
    if it.get("items"):
        out["items"] = [item_to_input(s) for s in it["items"]]
    return out

print("Preparando update del menu...")
new_items = [item_to_input(it) for it in main["items"]]
print()

# 2. Cargar colecciones para eliminar
print("Identificando colecciones a eliminar...")
custom = requests.get(f"{REST_BASE}/custom_collections.json", headers=HEADERS,
                     params={"limit":250, "fields":"id,handle,title"}, timeout=30).json()["custom_collections"]
smart  = requests.get(f"{REST_BASE}/smart_collections.json", headers=HEADERS,
                     params={"limit":250, "fields":"id,handle,title"}, timeout=30).json()["smart_collections"]
by_handle = {c["handle"]: ("custom", c) for c in custom}
by_handle.update({c["handle"]: ("smart", c) for c in smart})

to_delete = []
for h in DUPLICATE_COLLECTIONS:
    if h in by_handle:
        kind, col = by_handle[h]
        to_delete.append((kind, col))
        print(f"  {h} ({kind}, id={col['id']}, titulo='{col['title']}')")
    else:
        print(f"  {h} no encontrada, omitida")
print()

if not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
    sys.exit(0)

# 3. Aplicar update de menu
print("Actualizando menu principal...")
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
    print("  OK menu actualizado")
print()

# 4. Eliminar colecciones duplicadas
print("Eliminando colecciones duplicadas...")
for kind, col in to_delete:
    ep = f"{kind}_collections" if kind == "custom" else f"{kind}_collections"
    r = requests.delete(f"{REST_BASE}/{ep}/{col['id']}.json", headers=HEADERS, timeout=30)
    if r.status_code in (200, 201, 204):
        print(f"  OK eliminada: {col['handle']}")
    else:
        print(f"  ERR {col['handle']} HTTP {r.status_code}")
