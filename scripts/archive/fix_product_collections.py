"""
Aplica las correcciones detectadas por verify_product_collections.py.
Agrega productos a sus colecciones correctas.

Uso:
    python scripts/fix_product_collections.py --dry-run
    python scripts/fix_product_collections.py --apply
"""
import sys, time, argparse
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Reglas: title keywords -> target handle (mismo orden que verify)
TITLE_RULES = [
    (["hilo bordadora", "hilo de bordado", "durafill", "hilo de bobina bordadora"],
                                                                        "hilos-bordar-profesionales"),
    (["hilo poliester 2000", "hilo 2000", "2000 yardas", "2000 yrds"],  "hilo-2000"),
    (["hilo poliester 5000", "hilo 5000", "5000 yardas"],               "hilo-5000"),
    (["hilo rendidor"],                                                 "hilo-2000"),
    (["hilo poliamida", "hilo nylon"],                                  "hilo-poliamida"),
    (["hilo overlock", "hilo collareta"],                               "hilo-overlock"),
    (["hilo de saco"],                                                  "hilo-de-saco"),
    # Cintas satin (antes de cierres)
    (["cinta satin", "cinta satín", "cinta satinada", "cinta de raso"], "cintas-satin"),
    (["cinta algodon", "cinta algodón", "cinta lona algodon",
      "cinta de lona algodon"],                                         "cintas-algodon"),
    (["sesgo", "bies", "formador de bies"],                             "sesgo-bies"),
    (["huincha mochila", "cinta mochila"],                              "huincha-mochila"),
    (["entretela"],                                                     "entretelas"),
    # Repuestos
    (["aceitera", "tensor de hilo", "guia de hilo", "guía de hilo",
      "tirahilo", "lampara led", "lámpara led", "foco led"],            "repuestos-maquinas-de-coser"),
    # Cortadoras / repuesto cortadora
    (["lija de repuesto", "repuesto eastman", "repuesto cortadora"],    "repuestos-de-cortadoras-de-telas"),
    (["cortadora de tela", "cuchilla cortadora"],                       "cortadoras-de-tela-circulares"),
    # Broches/ojetillado
    (["matriz ojetilladora", "prensa ojetilladora", "ojetilladora",
      "broche de jeans"],                                               "broches"),
    # Lentejuelas/strass (aplicadores tambien van aqui)
    (["lentejuela", "strass", "aplicador strass", "pegadora de perlas"],
                                                                        "lentejuelas-y-strass"),
    # Tinturas (antes de bisuteria si tiene "tintura")
    (["anilina", "tintura para tela", "tintura"],                       "tinturas"),
    # Herramientas
    (["brocha limpiadora", "pinza sujetadora", "pinza costura",
      "clips para tela", "pistola de silicona", "volteador de tiras"],  "herramientas-de-costura"),
]

# Excepciones: NO mover si el titulo contiene estas palabras
SKIP_IF_TITLE_HAS = {
    "hilo-poliamida": ["cierre"],  # "Cierre de Nylon" no es hilo
}

def match_title(title):
    t = title.lower()
    for keywords, handle in TITLE_RULES:
        if any(k in t for k in keywords):
            skip_words = SKIP_IF_TITLE_HAS.get(handle, [])
            if any(s in t for s in skip_words):
                continue
            return handle
    return None

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

print("Cargando colecciones (separando custom vs smart)...")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
custom_handles = {c["handle"]: c for c in custom}
smart_handles  = {c["handle"]: c for c in smart}
all_handles = {**custom_handles, **smart_handles}
print(f"  custom: {len(custom)}, smart: {len(smart)}")

print("Cargando productos...")
products = paginate("products.json", "products", fields="id,title,status")
print(f"  {len(products)} productos")

print("Mapeando colecciones actuales por producto...")
prod_cols = defaultdict(set)
for col in custom + smart:
    prods = paginate(f"collections/{col['id']}/products.json", "products", fields="id")
    for p in prods:
        prod_cols[p["id"]].add(col["handle"])
    time.sleep(0.1)
print()

# Construir plan
plan_custom = []   # (product, target_handle, target_id)
plan_smart  = []   # productos cuya regla es smart — necesitan ajuste de regla/tag
for p in products:
    if p.get("status") != "active":
        continue
    target = match_title(p["title"])
    if not target or target not in all_handles:
        continue
    current = prod_cols.get(p["id"], set())
    if target in current:
        continue
    if target in custom_handles:
        plan_custom.append((p, target, custom_handles[target]["id"]))
    else:
        plan_smart.append((p, target))

print("="*60)
print(f"PLAN")
print("="*60)
print(f"  A agregar a custom collections: {len(plan_custom)}")
print(f"  A smart collections (no se puede asignar manual): {len(plan_smart)}")
print()

from collections import Counter
print("Custom (se agregaran):")
for h, n in Counter(t for _,t,_ in plan_custom).most_common():
    print(f"  {n:3d} -> {h}")
print()
if plan_smart:
    print("Smart (requiere actualizar regla o agregar tag):")
    for h, n in Counter(t for _,t in plan_smart).most_common():
        print(f"  {n:3d} -> {h}")
    print()

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
    sys.exit(0)

print("Agregando a custom collections...")
ok = err = 0
for p, target, col_id in plan_custom:
    r = requests.post(
        f"{REST_BASE}/collects.json",
        headers=HEADERS,
        json={"collect": {"product_id": p["id"], "collection_id": col_id}},
        timeout=30,
    )
    if r.status_code in (200, 201):
        print(f"  OK  {p['title'][:50]:50s} -> {target}")
        ok += 1
    elif r.status_code == 422:
        print(f"  ya estaba: {p['title'][:50]}")
    else:
        print(f"  ERR {p['title'][:50]} HTTP {r.status_code}: {r.text[:80]}")
        err += 1
    time.sleep(0.2)

print()
print(f"OK {ok} agregados / ERR {err} errores")

if plan_smart:
    print()
    print("Productos que matchean smart collections (no se asignaron):")
    for p, target in plan_smart:
        print(f"  {target}: {p['title'][:60]}")
    print()
    print("Para estos: actualiza la regla de la smart collection en Shopify Admin")
    print("o agrega el tag/condicion correspondiente al producto.")
