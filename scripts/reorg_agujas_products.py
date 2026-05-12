"""
Reorganiza productos de agujas (colecciones custom):
- aguja-maquina-casera: solo Schmetz y Singer
- aguja-maquina-industrial: las demas (Groz, Beckert, talon, overlock, bordadora, etc.)

Mueve productos entre colecciones segun titulo.

Uso:
    python scripts/reorg_agujas_products.py --dry-run
    python scripts/reorg_agujas_products.py --apply
"""
import sys, time, argparse
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

def is_casera(title):
    t = title.lower()
    return any(k in t for k in ["schmetz", "singer"])

def is_industrial(title):
    t = title.lower()
    keywords = ["groz", "beckert", "dbx", "dbk", "uy128", "dax",
                "overlock", "collareta", "bordadora",
                "talon delgado", "talón delgado",
                "talon grueso", "talón grueso",
                "aguja industrial", "aguja recta industrial",
                "aguja para maquina industrial", "aguja para máquina industrial"]
    return any(k in t for k in keywords)

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

# Cargar colecciones
print("Cargando colecciones...")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle")
custom_by_handle = {c["handle"]: c for c in custom}

cas_col = custom_by_handle.get("aguja-maquina-casera")
ind_col = custom_by_handle.get("aguja-maquina-industrial")
if not cas_col or not ind_col:
    raise SystemExit("Faltan colecciones aguja-maquina-casera o aguja-maquina-industrial")

# Productos actuales en cada coleccion
print("Productos actuales...")
cas_prods = paginate(f"collections/{cas_col['id']}/products.json", "products", fields="id,title")
ind_prods = paginate(f"collections/{ind_col['id']}/products.json", "products", fields="id,title")
cas_ids = {p["id"]: p for p in cas_prods}
ind_ids = {p["id"]: p for p in ind_prods}
print(f"  Casera: {len(cas_prods)}")
print(f"  Industrial: {len(ind_prods)}")

# Buscar todas las agujas en el catalogo (productos cuyo titulo empieza con o contiene 'Aguja')
print("Buscando todas las agujas en el catalogo...")
all_prods = paginate("products.json", "products", fields="id,title,status")
all_agujas = [p for p in all_prods
              if p.get("status") == "active"
              and ("aguja" in p["title"].lower() or
                   "schmetz" in p["title"].lower() or
                   "groz" in p["title"].lower() or
                   "beckert" in p["title"].lower())]
print(f"  {len(all_agujas)} candidatos a aguja")
print()

# Plan
to_add_casera     = []
to_add_industrial = []
to_remove_casera     = []
to_remove_industrial = []

for p in all_agujas:
    pid = p["id"]
    t = p["title"]
    cas = is_casera(t)
    ind = is_industrial(t)

    # Si es claramente casera y no industrial
    if cas and not ind:
        if pid not in cas_ids: to_add_casera.append(p)
        if pid in ind_ids:     to_remove_industrial.append(p)
    # Si es claramente industrial y no casera
    elif ind and not cas:
        if pid not in ind_ids: to_add_industrial.append(p)
        if pid in cas_ids:     to_remove_casera.append(p)
    # Si tiene ambos (raro): industrial gana
    elif cas and ind:
        if pid not in ind_ids: to_add_industrial.append(p)
        if pid in cas_ids:     to_remove_casera.append(p)
    # Ni casera ni industrial: si esta en casera, sacarlo
    else:
        if pid in cas_ids:     to_remove_casera.append(p)
        if pid in ind_ids:     to_remove_industrial.append(p)

print(f"PLAN:")
print(f"  Agregar a casera:    {len(to_add_casera)}")
print(f"  Agregar a industrial: {len(to_add_industrial)}")
print(f"  Quitar de casera:    {len(to_remove_casera)}")
print(f"  Quitar de industrial: {len(to_remove_industrial)}")
print()

# Tambien sacar productos NO agujas de las colecciones
non_aguja_in_cas = [cas_ids[pid] for pid in cas_ids
                    if pid not in {p["id"] for p in all_agujas}]
non_aguja_in_ind = [ind_ids[pid] for pid in ind_ids
                    if pid not in {p["id"] for p in all_agujas}]
if non_aguja_in_cas or non_aguja_in_ind:
    print(f"  Quitar NO-agujas de casera:    {len(non_aguja_in_cas)}")
    print(f"  Quitar NO-agujas de industrial: {len(non_aguja_in_ind)}")
    for p in non_aguja_in_cas: to_remove_casera.append(p)
    for p in non_aguja_in_ind: to_remove_industrial.append(p)
    print()

if to_remove_casera[:5]:
    print("Ejemplos a QUITAR de casera:")
    for p in to_remove_casera[:5]:
        print(f"  - {p['title'][:65]}")
if to_remove_industrial[:5]:
    print("Ejemplos a QUITAR de industrial:")
    for p in to_remove_industrial[:5]:
        print(f"  - {p['title'][:65]}")
if to_add_casera[:5]:
    print("Ejemplos a AGREGAR a casera:")
    for p in to_add_casera[:5]:
        print(f"  - {p['title'][:65]}")
if to_add_industrial[:5]:
    print("Ejemplos a AGREGAR a industrial:")
    for p in to_add_industrial[:5]:
        print(f"  - {p['title'][:65]}")
print()

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if not args.apply:
    print("Modo dry-run. Corre con --apply para aplicar.")
    sys.exit(0)

# Obtener collect IDs para poder eliminar
print("Cargando collects (relacion producto-coleccion)...")
all_collects = paginate("collects.json", "collects", fields="id,product_id,collection_id")
collect_by_pair = {(c["product_id"], c["collection_id"]): c["id"] for c in all_collects}

def remove_from_col(product, col_id):
    cid = collect_by_pair.get((product["id"], col_id))
    if not cid:
        return None  # no estaba via collects (puede ser por regla smart)
    r = requests.delete(f"{REST_BASE}/collects/{cid}.json", headers=HEADERS, timeout=30)
    return r.status_code

def add_to_col(product, col_id):
    r = requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
                      json={"collect": {"product_id": product["id"], "collection_id": col_id}},
                      timeout=30)
    return r.status_code

ok = err = 0
print("\nAplicando cambios...")
for p in to_add_casera:
    s = add_to_col(p, cas_col["id"])
    print(f"  + casera: {p['title'][:55]:55s} HTTP {s}")
    if s in (200,201,422): ok += 1
    else: err += 1
    time.sleep(0.15)

for p in to_add_industrial:
    s = add_to_col(p, ind_col["id"])
    print(f"  + industrial: {p['title'][:55]:55s} HTTP {s}")
    if s in (200,201,422): ok += 1
    else: err += 1
    time.sleep(0.15)

for p in to_remove_casera:
    s = remove_from_col(p, cas_col["id"])
    print(f"  - casera: {p['title'][:55]:55s} HTTP {s}")
    if s in (200,201,204): ok += 1
    elif s is None: pass
    else: err += 1
    time.sleep(0.15)

for p in to_remove_industrial:
    s = remove_from_col(p, ind_col["id"])
    print(f"  - industrial: {p['title'][:55]:55s} HTTP {s}")
    if s in (200,201,204): ok += 1
    elif s is None: pass
    else: err += 1
    time.sleep(0.15)

print(f"\nOK {ok} cambios / ERR {err} errores")
