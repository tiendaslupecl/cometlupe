"""
Asigna el metafield custom.upsell_collection a cada producto según su tipo/colección.
Uso:
    python scripts/upsell_assign.py --dry-run    # solo muestra el plan
    python scripts/upsell_assign.py --apply      # aplica los cambios
"""
import sys
import json
import time
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS
import requests

# ── Helpers ────────────────────────────────────────────────────────────────────

def get(path, **params):
    r = requests.get(f"{REST_BASE}/{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def put(path, payload):
    r = requests.put(f"{REST_BASE}/{path}", headers=HEADERS, json=payload, timeout=30)
    return r

def paginate(path, key, **params):
    items = []
    params.setdefault("limit", 250)
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        items += r.json().get(key, [])
        link = r.headers.get("Link", "")
        url = None
        params = {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items


# ── Fetch data ─────────────────────────────────────────────────────────────────

print("🔍 Obteniendo colecciones...")
custom_cols = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart_cols  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
all_cols    = custom_cols + smart_cols
cols_by_handle = {c["handle"]: c for c in all_cols}

print(f"   {len(all_cols)} colecciones encontradas")
print()

print("🔍 Obteniendo productos...")
products = paginate("products.json", "products", fields="id,title,product_type,tags,handle")
print(f"   {len(products)} productos encontrados")
print()

# ── Mostrar colecciones disponibles ───────────────────────────────────────────
print("📋 Colecciones disponibles:")
for c in sorted(all_cols, key=lambda x: x["title"]):
    print(f"   {c['handle']:40s} → {c['title']}")
print()

# ── Reglas de asignación ──────────────────────────────────────────────────────
# Mapeo: palabra clave en título/tipo/tags del producto → handle de colección upsell
# Prioridad: primera regla que coincida gana.
RULES = [
    # (lista de keywords, handle_colección_upsell)
    (["aguja", "agujas"],                   "hilos"),
    (["hilo", "hilos"],                     "agujas"),
    (["tela", "telas"],                     "accesorios-costura"),
    (["cremallera", "cierre", "zipper"],    "hilos"),
    (["patron", "patrón", "patrones"],      "telas"),
    (["bordado", "bordar"],                 "hilos"),
    (["máquina", "maquina", "singer"],      "accesorios-maquinas-coser"),
    (["accesorio", "accesorios", "prensatelas"], "agujas"),
    (["botón", "boton", "botones"],         "hilos"),
    (["encaje", "elástico", "elastico"],    "accesorios-costura"),
]

DEFAULT_UPSELL = "accesorios-costura"  # colección fallback si ninguna regla aplica


def best_upsell(product):
    text = " ".join([
        product.get("title", ""),
        product.get("product_type", ""),
        product.get("tags", "") if isinstance(product.get("tags"), str) else "",
    ]).lower()
    for keywords, col_handle in RULES:
        if any(k in text for k in keywords):
            if col_handle in cols_by_handle:
                return cols_by_handle[col_handle]
    if DEFAULT_UPSELL in cols_by_handle:
        return cols_by_handle[DEFAULT_UPSELL]
    return None


# ── Construir plan ─────────────────────────────────────────────────────────────
plan = []
for p in products:
    col = best_upsell(p)
    if col:
        plan.append((p, col))

print(f"📦 Plan de asignación ({len(plan)} productos):")
for p, col in plan:
    print(f"   [{p['id']}] {p['title'][:45]:45s} → {col['handle']} ({col['title']})")
print()

# ── Aplicar ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if args.dry_run or (not args.apply):
    print("ℹ️  Modo dry-run. Corre con --apply para guardar los cambios.")
    sys.exit(0)

print("🚀 Aplicando metafields...")
ok = err = 0
for p, col in plan:
    col_gid = f"gid://shopify/Collection/{col['id']}"
    payload = {
        "metafield": {
            "namespace": "custom",
            "key": "upsell_collection",
            "type": "collection_reference",
            "value": col_gid,
            "owner_id": p["id"],
            "owner_resource": "product",
        }
    }
    r = requests.post(
        f"{REST_BASE}/products/{p['id']}/metafields.json",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code in (200, 201):
        print(f"  ✅ {p['title'][:40]} → {col['handle']}")
        ok += 1
    else:
        body = r.json()
        # Si ya existe, actualizarlo
        existing = requests.get(
            f"{REST_BASE}/products/{p['id']}/metafields.json",
            headers=HEADERS,
            params={"namespace": "custom", "key": "upsell_collection"},
            timeout=30,
        ).json().get("metafields", [])
        if existing:
            mf_id = existing[0]["id"]
            r2 = requests.put(
                f"{REST_BASE}/products/{p['id']}/metafields/{mf_id}.json",
                headers=HEADERS,
                json={"metafield": {"id": mf_id, "value": col_gid}},
                timeout=30,
            )
            if r2.status_code in (200, 201):
                print(f"  ↩️  {p['title'][:40]} → {col['handle']} (actualizado)")
                ok += 1
            else:
                print(f"  ❌ {p['title'][:40]} — {r2.status_code}: {r2.text[:120]}")
                err += 1
        else:
            print(f"  ❌ {p['title'][:40]} — {r.status_code}: {r.text[:120]}")
            err += 1
    time.sleep(0.3)  # respetar rate limit

print()
print(f"✅ {ok} asignados / ❌ {err} errores")
