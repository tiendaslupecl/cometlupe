"""Auditoria de calidad del catalogo."""
import sys, time, re
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
        link, url, params = r.headers.get("Link", ""), None, {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items

print("Cargando productos activos...")
prods = paginate("products.json", "products",
                 fields="id,title,status,body_html,images,variants,product_type")
active = [p for p in prods if p.get("status") == "active"]
print(f"  {len(active)} productos activos\n")

sin_imagen, una_imagen, sin_descripcion, desc_corta = [], [], [], []
variante_cero, variante_sin_stock, sin_tipo = [], [], []

for p in active:
    title, pid = p["title"], p["id"]
    imgs = p.get("images", [])
    body = (p.get("body_html") or "").strip()
    body_text = re.sub(r"<[^>]+>", "", body).strip()
    if len(imgs) == 0: sin_imagen.append((pid, title))
    elif len(imgs) == 1: una_imagen.append((pid, title))
    if not body_text: sin_descripcion.append((pid, title))
    elif len(body_text) < 60: desc_corta.append((pid, title, body_text[:80]))
    if not p.get("product_type", "").strip(): sin_tipo.append((pid, title))
    for v in p.get("variants", []):
        price = float(v.get("price") or 0)
        stock = v.get("inventory_quantity") or 0
        inv = v.get("inventory_management") or ""
        if price == 0: variante_cero.append((pid, title, v.get("title",""), price))
        if inv == "shopify" and stock <= 0: variante_sin_stock.append((pid, title, v.get("title",""), stock))
    time.sleep(0.01)

sep = "=" * 65
def show(label, items, extra=False):
    print(f"\n{sep}\n{label.upper()}  ({len(items)})\n{sep}")
    for row in items[:40]:
        e = f"  ->  {row[2]}" if extra and len(row) > 2 else ""
        print(f"  [{row[0]}] {row[1][:60]}{e}")
    if len(items) > 40: print(f"  ... y {len(items)-40} mas")

print(f"\n{sep}\nRESUMEN AUDITORIA CATALOGO\n{sep}")
print(f"  Sin imagen            : {len(sin_imagen):4d}")
print(f"  Con 1 sola imagen     : {len(una_imagen):4d}")
print(f"  Sin descripcion       : {len(sin_descripcion):4d}")
print(f"  Descripcion muy corta : {len(desc_corta):4d}  (<60 chars)")
print(f"  Variante precio $0    : {len(variante_cero):4d}")
print(f"  Variante sin stock    : {len(variante_sin_stock):4d}")
print(f"  Sin product_type      : {len(sin_tipo):4d}")
total = len(sin_imagen) + len(sin_descripcion) + len(variante_cero)
print(f"\nPROBLEMAS CRITICOS: {total}")
if sin_imagen: show("sin imagen", sin_imagen)
if sin_descripcion: show("sin descripcion", sin_descripcion)
if variante_cero: show("variante precio $0", variante_cero, True)
if desc_corta: show("descripcion corta", desc_corta, True)
if variante_sin_stock: show("variante sin stock", variante_sin_stock, True)
if una_imagen: show("con 1 sola imagen", una_imagen)
if sin_tipo: show("sin product_type", sin_tipo)
