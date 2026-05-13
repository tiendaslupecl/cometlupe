"""
Reemplaza URLs con filter.p.tag (que no funcionan) por links a colecciones reales.
"""
import sys, argparse
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

store_admin = REST_BASE.split("/admin/")[0]
GRAPHQL = f"{store_admin}/admin/api/2024-01/graphql.json"
STORE = "https://www.tiendaslupe.cl"

# Mapeo titulo del menu -> coleccion destino real
RETARGET = {
    # bajo Maquinas y Repuestos
    "agujas":                 "aguja-maquina-industrial",  # parent, casera/industrial son sub
    "prensatelas":            "prensatelas-para-maquina-de-cos",
    "repuestos":              "repuestos-maquinas-de-coser",
    "cuchillos y cortadoras": "cortadoras-de-tela-circulares",
    "planchas industriales":  "planchas-a-vapor-industrial",
    "accesorios de máquina":  "accesorios-maquina",
    "accesorios de maquina":  "accesorios-maquina",
    # bajo Insumos
    "hilos":                  "hilo-2000",
    "elásticos":              "elasticos-costura",
    "elasticos":              "elasticos-costura",
    "cierres":                "cierres-y-cremalleras-para-costura",
    "broches":                "broches",
    "velcros":                "velcro",
    "velcro":                 "velcro",
    "cintas":                 "cintas-algodon",
    "cintas y bies":          "sesgo-bies",
    "entretelas":             "entretelas",
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
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

print("Cargando menu principal...")
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
    # Si el titulo esta en RETARGET y la URL tiene filter.p.tag, reemplazar
    key = it["title"].lower().strip()
    if key in RETARGET and "filter.p.tag" in (it["url"] or ""):
        new_handle = RETARGET[key]
        out["type"] = "HTTP"
        out["url"] = f"{STORE}/collections/{new_handle}"
        print(f"  FIX: '{it['title']}' -> /collections/{new_handle}")
    if it.get("tags"): out["tags"] = it["tags"]
    if it.get("resourceId"): out["resourceId"] = it["resourceId"]
    if it.get("items"):
        out["items"] = [item_to_input(s) for s in it["items"]]
    return out

print("Preparando cambios...")
new_items = [item_to_input(it) for it in main["items"]]
print()

if not args.apply:
    print("Modo dry-run. Corre con --apply.")
    sys.exit(0)

print("Aplicando...")
m = """mutation menuUpdate($id:ID!,$title:String!,$handle:String!,$items:[MenuItemUpdateInput!]!){
  menuUpdate(id:$id,title:$title,handle:$handle,items:$items){
    menu{id} userErrors{field message}
  }
}"""
resp = gql(m, {"id": main["id"], "title": main["title"], "handle": main["handle"], "items": new_items})
if resp["menuUpdate"].get("userErrors"):
    for e in resp["menuUpdate"]["userErrors"]:
        print(f"  ERROR: {e}")
else:
    print("  OK menu actualizado")
