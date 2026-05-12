"""
Auditoria integral de URLs de la tienda. Busca 404s en:
- Items de menus (todos)
- Colecciones referenciadas
- Paginas (/pages/*)
- Productos con status active sin imagen o sin variantes

Uso:
    python scripts/audit_store_404.py
    python scripts/audit_store_404.py --check-live  # verifica URLs en vivo (mas lento)
"""
import sys, time, argparse
from pathlib import Path
from urllib.parse import urlparse, urlunparse

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

store_admin = REST_BASE.split("/admin/")[0]
GRAPHQL = f"{store_admin}/admin/api/2024-01/graphql.json"
STOREFRONT = "https://www.tiendaslupe.cl"

def gql(query):
    r = requests.post(GRAPHQL, headers={**HEADERS, "Content-Type":"application/json"},
                      json={"query": query}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]

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

parser = argparse.ArgumentParser()
parser.add_argument("--check-live", action="store_true",
                    help="Verifica HTTP status de URLs en el storefront (mas lento)")
args = parser.parse_args()

# 1) Cargar todas las colecciones existentes
print("Cargando colecciones...")
all_cols = []
for kind in ("custom_collections", "smart_collections"):
    all_cols += paginate(f"{kind}.json", kind, fields="id,handle,title")
col_handles = {c["handle"] for c in all_cols}
col_titles  = {c["handle"]: c["title"] for c in all_cols}
print(f"  {len(col_handles)} colecciones")

# 2) Cargar paginas
print("Cargando paginas (/pages/*)...")
pages = paginate("pages.json", "pages", fields="id,handle,title,published_at")
page_handles = {p["handle"] for p in pages if p.get("published_at")}
print(f"  {len(page_handles)} paginas publicadas")

# 3) Cargar productos
print("Cargando productos...")
prods = paginate("products.json", "products", fields="id,handle,title,status,images")
prod_handles = {p["handle"]: p for p in prods if p.get("status") == "active"}
print(f"  {len(prod_handles)} productos activos")
print()

# 4) Cargar todos los menus
print("Cargando menus...")
q = """{
  menus(first:20){edges{node{
    handle title
    items{title type url
      items{title type url
        items{title type url}}}}}}
}"""
menus = [e["node"] for e in gql(q)["menus"]["edges"]]
print(f"  {len(menus)} menus")
print()

# 5) Auditar cada item de menu
issues = []

def check_url(url, ctx):
    """Devuelve (status, motivo)"""
    if not url or url == "#":
        return "OK", "anchor"
    parsed = urlparse(url)
    path = parsed.path or url
    if not path.startswith("/"):
        # URL externa o relativa rara
        if path.startswith("http"):
            return "OK", "externa"
        return "WARN", f"path raro: {url}"
    parts = path.strip("/").split("/")
    if not parts or parts[0] == "":
        return "OK", "raiz"

    section = parts[0]
    handle = parts[1] if len(parts) > 1 else None

    if section == "collections" and handle:
        if handle == "all":
            return "OK", "catalogo all"
        if handle not in col_handles:
            return "404", f"coleccion '{handle}' no existe"
        # Si tiene query con filter.p.tag, validar que el filtro tenga sentido
        return "OK", f"coleccion {handle}"
    if section == "products" and handle:
        if handle not in prod_handles:
            return "404", f"producto '{handle}' no existe"
        return "OK", f"producto {handle}"
    if section == "pages" and handle:
        if handle not in page_handles:
            return "404", f"pagina '{handle}' no existe"
        return "OK", f"pagina {handle}"
    if section == "policies":
        return "OK", "policy"
    if section == "blogs":
        return "OK", "blog (no validado)"
    return "OK", path

def walk(items, menu_h, depth=0):
    for it in items:
        url = it.get("url","")
        title = it.get("title","")
        status, motivo = check_url(url, f"{menu_h}>{title}")
        if status != "OK":
            issues.append((menu_h, title, url, status, motivo))
        walk(it.get("items", []), menu_h, depth+1)

print("Auditando menus...")
for menu in menus:
    walk(menu["items"], menu["handle"])
print()

# 6) Reporte
print("="*60)
print("REPORTE DE PROBLEMAS EN MENUS")
print("="*60)
if issues:
    for menu_h, title, url, status, motivo in issues:
        print(f"  [{status}] {menu_h} > '{title}'")
        print(f"         URL: {url}")
        print(f"         {motivo}")
        print()
else:
    print("  Sin problemas detectados en menus.")
print()

# 7) Colecciones vacias publicadas (no rotas pero molestas)
print("="*60)
print("COLECCIONES VACIAS (0 productos)")
print("="*60)
empty = []
for col in all_cols:
    prods_in = paginate(f"collections/{col['id']}/products.json", "products", fields="id")
    if len(prods_in) == 0:
        empty.append(col)
    time.sleep(0.08)
for c in empty:
    print(f"  [{c['handle']}] {c['title']}")
print(f"  Total vacias: {len(empty)}")
print()

# 8) Productos activos sin imagen
no_img = [p for p in prods if p.get("status")=="active" and not p.get("images")]
if no_img:
    print("="*60)
    print(f"PRODUCTOS ACTIVOS SIN IMAGEN ({len(no_img)})")
    print("="*60)
    for p in no_img[:30]:
        print(f"  [{p['handle']}] {p['title'][:60]}")
    if len(no_img) > 30:
        print(f"  ... y {len(no_img)-30} mas")
    print()

# 9) Verificacion en vivo opcional
if args.check_live:
    print("="*60)
    print("VERIFICACION EN VIVO (HTTP HEAD a storefront)")
    print("="*60)
    test_urls = []
    # Sample 5 collections, 5 products, all pages
    test_urls += [f"/collections/{c}" for c in list(col_handles)[:10]]
    test_urls += [f"/products/{h}" for h in list(prod_handles.keys())[:10]]
    test_urls += [f"/pages/{p}" for p in page_handles]
    for path in test_urls:
        full = STOREFRONT + path
        try:
            r = requests.head(full, timeout=10, allow_redirects=True)
            tag = "OK" if r.status_code < 400 else f"HTTP{r.status_code}"
        except Exception as e:
            tag = f"ERR {type(e).__name__}"
        if tag != "OK":
            print(f"  [{tag}] {path}")
        time.sleep(0.15)
    print()

print("="*60)
print(f"Resumen: {len(issues)} problemas en menus, {len(empty)} colecciones vacias")
print("="*60)
