"""Auditoria SEO basica."""
import sys, re, time
from pathlib import Path
from collections import Counter
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

def norm_tag(t): return t.lower().strip()

print("Cargando productos activos...")
prods = paginate("products.json", "products", fields="id,title,handle,status,tags")
active = [p for p in prods if p.get("status") == "active"]
print(f"  {len(active)} productos activos\n")

titulo_corto, titulo_generico, sin_handle_seo = [], [], []
tags_vacios, tags_problemas = [], []
tag_freq = Counter()
PALABRAS = ["aguja","hilo","prensatela","tijera","cierre","broche","elastic",
            "cinta","velcro","boton","hebilla","plancha","cortador","bobina",
            "canilla","repuesto","overlock"]

for p in active:
    title, pid = p["title"], p["id"]
    handle = p.get("handle", "")
    tags_raw = p.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    if len(title) < 20: titulo_corto.append((pid, title))
    tn = norm_tag(title)
    if not any(kw in tn for kw in PALABRAS): titulo_generico.append((pid, title))
    if re.search(r"[A-Z_]", handle): sin_handle_seo.append((pid, title, handle))
    if not tags: tags_vacios.append((pid, title))
    else:
        for t in tags:
            tag_freq[norm_tag(t)] += 1
            if t != t.strip() or "  " in t: tags_problemas.append((pid, title, t))
    time.sleep(0.01)

sep = "=" * 65
def show(label, items, extra=False):
    print(f"\n{sep}\n{label.upper()}  ({len(items)})\n{sep}")
    for row in items[:40]:
        e = f"  ->  {row[2]}" if extra and len(row) > 2 else ""
        print(f"  [{row[0]}] {row[1][:55]}{e}")
    if len(items) > 40: print(f"  ... y {len(items)-40} mas")

print(f"\n{sep}\nRESUMEN AUDITORIA SEO\n{sep}")
print(f"  Titulo muy corto (<20c)  : {len(titulo_corto):4d}")
print(f"  Titulo sin palabra clave : {len(titulo_generico):4d}")
print(f"  Sin tags                 : {len(tags_vacios):4d}")
print(f"  Tags formato incorrecto  : {len(tags_problemas):4d}")
print(f"  Tags unicos              : {len(tag_freq):4d}")
total = len(titulo_corto) + len(tags_vacios)
print(f"\nPROBLEMAS SEO CRITICOS: {total}")
if titulo_corto: show("titulo muy corto", titulo_corto)
if tags_vacios: show("sin tags", tags_vacios)
if titulo_generico: show("titulo sin palabra clave", titulo_generico)
if tags_problemas: show("tags incorrectos", tags_problemas, True)
print(f"\n{sep}\nTOP 20 TAGS\n{sep}")
for tag, cnt in tag_freq.most_common(20):
    print(f"  {cnt:4d}x  {tag}")
