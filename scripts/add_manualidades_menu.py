"""
Agrega una seccion 'Manualidades' al menu principal con submenus para
todas las categorias de manualidades existentes.

Uso:
    python scripts/add_manualidades_menu.py --dry-run
    python scripts/add_manualidades_menu.py --apply
"""
import sys, argparse, json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

store = REST_BASE.split("/admin/")[0]
GRAPHQL = f"{store}/admin/api/2024-01/graphql.json"

# Items a agregar bajo "Manualidades"
MANUALIDADES = [
    ("Tejido y Manualidades",         "tejido-y-manualidades"),
    ("Crochet y Ganchillos",          "crochet-accessories-ganchillos"),
    ("Lanas y Ovillos",               "lanas-ovillos-crochet-tejido"),
    ("Trapillo",                      "trapillo-telas-crochet"),
    ("Bastidores Bordado",            "bastidores-bordado"),
    ("Bisuteria y Decoracion",        "bisuteria-y-decoracion"),
    ("Argollas",                      "argollas-manualidades"),
    ("Cuencas de Madera",             "cuencas-madera"),
    ("Hebillas",                      "hebillas"),
    ("Cascabeles",                    "cascabeles-costura-manualidades"),
    ("Macrame y Cordones",            "macrame-cordon-trenzado"),
    ("Lentejuelas y Strass",          "lentejuelas-y-strass"),
    ("Adhesivos Telas",               "adhesivos-telas"),
    ("Anilinas y Tinturas",           "tinturas"),
    ("Tinturas y Pegamentos",         "tinturas-y-pegamentos"),
    ("Materiales para Manualidades",  "materiales-para-manualidades"),
]

def gql(query, variables=None):
    r = requests.post(GRAPHQL, headers={**HEADERS, "Content-Type":"application/json"},
                      json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]

# 1) Verificar que las colecciones existen
print("Verificando colecciones...")
existing = set()
for kind in ("custom_collections", "smart_collections"):
    r = requests.get(f"{REST_BASE}/{kind}.json", headers=HEADERS,
                     params={"limit":250, "fields":"handle"}, timeout=30)
    for c in r.json().get(kind, []):
        existing.add(c["handle"])

missing = [(t,h) for t,h in MANUALIDADES if h not in existing]
valid   = [(t,h) for t,h in MANUALIDADES if h in existing]
if missing:
    print(f"  AVISO: {len(missing)} colecciones no existen (se saltan):")
    for t,h in missing:
        print(f"    {h}")
print(f"  Validas: {len(valid)}")
print()

# 2) Obtener menu principal con items existentes
print("Obteniendo menu principal...")
q = """
{
  menus(first: 20) {
    edges { node {
      id handle title
      items { id title type url tags resourceId
        items { id title type url tags resourceId }
      }
    }}
  }
}
"""
data = gql(q)
menus = [e["node"] for e in data["menus"]["edges"]]
main = next((m for m in menus if m["handle"] == "main-menu"), None)
if not main:
    raise SystemExit("No se encontro main-menu")

print(f"  Menu ID: {main['id']}")
print(f"  Items actuales: {len(main['items'])}")
for it in main["items"]:
    print(f"    - {it['title']} ({len(it.get('items',[]))} sub)")
print()

# 3) Construir nuevos items: preservar todo + agregar Manualidades antes de Contacto
def item_to_input(it):
    """Convierte un MenuItem existente al formato de input para menuUpdate."""
    out = {
        "title": it["title"],
        "type": it["type"],
        "url": it["url"],
    }
    if it.get("tags"):
        out["tags"] = it["tags"]
    if it.get("resourceId"):
        out["resourceId"] = it["resourceId"]
    if it.get("items"):
        out["items"] = [item_to_input(s) for s in it["items"]]
    return out

new_items = []
manualidades_inserted = False
for it in main["items"]:
    # Insertar Manualidades antes de "Contacto"
    if not manualidades_inserted and it["title"].lower() in ("contacto", "contact"):
        new_items.append({
            "title": "Manualidades",
            "type": "HTTP",
            "url": "https://www.tiendaslupe.cl/collections/tejido-y-manualidades",
            "items": [
                {
                    "title": title,
                    "type": "HTTP",
                    "url": f"https://www.tiendaslupe.cl/collections/{handle}",
                } for title, handle in valid
            ],
        })
        manualidades_inserted = True
    new_items.append(item_to_input(it))

if not manualidades_inserted:
    # Agregar al final si no habia Contacto
    new_items.append({
        "title": "Manualidades",
        "type": "HTTP",
        "url": "https://www.tiendaslupe.cl/collections/tejido-y-manualidades",
        "items": [
            {"title": title, "type": "HTTP",
             "url": f"https://www.tiendaslupe.cl/collections/{handle}"}
            for title, handle in valid
        ],
    })

print("Nuevo menu (preview):")
for it in new_items:
    print(f"  - {it['title']} -> {it.get('url','')}")
    for s in it.get("items", []):
        print(f"      - {s['title']} -> {s.get('url','')}")
print()

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if not args.apply:
    print("Modo dry-run. Corre con --apply para actualizar el menu.")
    sys.exit(0)

# 4) Aplicar menuUpdate
print("Aplicando cambios...")
mutation = """
mutation menuUpdate($id: ID!, $title: String!, $handle: String!, $items: [MenuItemUpdateInput!]!) {
  menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
    menu { id handle title items { title url } }
    userErrors { field message }
  }
}
"""
resp = gql(mutation, {
    "id": main["id"],
    "title": main["title"],
    "handle": main["handle"],
    "items": new_items,
})
result = resp["menuUpdate"]
if result.get("userErrors"):
    print("ERRORES:")
    for e in result["userErrors"]:
        print(f"  {e['field']}: {e['message']}")
else:
    print(f"OK Menu actualizado con {len(result['menu']['items'])} items")
