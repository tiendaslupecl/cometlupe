"""
Asigna custom.upsell_collection a cada producto basándose en las colecciones
a las que ya pertenece (no en palabras del título).

Uso:
    python scripts/upsell_assign.py --dry-run    # muestra el plan sin tocar nada
    python scripts/upsell_assign.py --apply      # aplica los cambios
"""
import sys
import time
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS
import requests

# ── Cross-sell map: si el producto está en esta colección → mostrar esta otra ─
# Lógica: complementos naturales de venta cruzada
CROSS_SELL = {
    # Agujas → Hilos y viceversa
    "aguja-maquina-casera":             "hilo-2000",
    "aguja-maquina-industrial":         "hilo-overlock",
    "agujas-mano":                      "hilo-2000",
    "agujas-crochet-y-tejido":          "lanas-ovillos-crochet-tejido",
    "hilo-2000":                        "aguja-maquina-casera",
    "hilo-5000":                        "aguja-maquina-casera",
    "hilo-overlock":                    "aguja-maquina-industrial",
    "hilo-de-saco":                     "agujas-mano",
    "hilo-poliamida":                   "aguja-maquina-industrial",
    "hilos-bordar-profesionales":       "bastidores-bordado",
    # Prensatelas → Agujas y repuestos
    "prensatelas-caseros":              "aguja-maquina-casera",
    "prensatelas-para-maquina-de-cos":  "aguja-maquina-casera",
    "prensatelas-industriales":         "aguja-maquina-industrial",
    "prensatelas-industriales-1":       "aguja-maquina-industrial",
    # Repuestos / Máquinas → Agujas
    "repuestos-maquinas-de-coser":      "aguja-maquina-casera",
    "maquinas-y-repuestos":             "accesorios-maquina",
    "accesorios-maquina":               "aguja-maquina-casera",
    # Cortadoras ↔ Repuestos
    "cortadoras-de-tela-circulares":    "repuestos-de-cortadoras-de-telas",
    "repuestos-de-cortadoras-de-telas": "cortadoras-de-tela-circulares",
    # Tijeras / Herramientas → Agujas
    "tijeras-profesionales-para-costura": "herramientas-de-costura",
    "herramientas-de-costura":          "aguja-maquina-casera",
    "herramientas-costura":             "aguja-maquina-casera",
    "herramientas":                     "aguja-maquina-casera",
    # Cierres / Elásticos / Botones
    "cierres":                          "herramientas-de-costura",
    "elasticos-costura":                "botones",
    "botones":                          "elasticos-costura",
    "broches":                          "botones",
    "hebillas":                         "herramientas-de-costura",
    "velcro":                           "elasticos-costura",
    # Bordado / Bastidores
    "bastidores-bordado":               "hilos-bordar-profesionales",
    # Tejido / Crochet / Lanas
    "lanas-ovillos-crochet-tejido":     "agujas-crochet-y-tejido",
    "crochet-accessories-ganchillos":   "lanas-ovillos-crochet-tejido",
    "trapillo-telas-crochet":           "agujas-crochet-y-tejido",
    "tejido-y-manualidades":            "lanas-ovillos-crochet-tejido",
    "tejido-manualidades":              "lanas-ovillos-crochet-tejido",
    # Entretelas / Adhesivos
    "entretelas":                       "herramientas-de-costura",
    "adhesivos-telas":                  "entretelas",
    # Cintas / Sesgo / Pasamanería
    "sesgo-bies":                       "herramientas-de-costura",
    "pasamaneria":                      "herramientas-de-costura",
    "cintas-algodon":                   "herramientas-de-costura",
    "cintas-satin":                     "herramientas-de-costura",
    "huincha-mochila":                  "herramientas-de-costura",
    "macrame-cordon-trenzado":          "herramientas",
    "cordones-zapatos-costura-manualidades": "herramientas",
    # Tinturas
    "tinturas":                         "herramientas-de-costura",
    "tinturas-y-pegamentos":            "herramientas-de-costura",
    "tinturas-pegamentos":              "herramientas-de-costura",
    # Bisutería / Decoración / Manualidades
    "bisuteria-y-decoracion":           "materiales-para-manualidades",
    "bisuteria-decoracion":             "materiales-para-manualidades",
    "lentejuelas-y-strass":             "materiales-para-manualidades",
    "flecos-decorativos":               "pasamaneria",
    "cascabeles-costura-manualidades":  "materiales-para-manualidades",
    "argollas-manualidades":            "materiales-para-manualidades",
    "cuencas-madera":                   "materiales-para-manualidades",
    "materiales-para-manualidades":     "agujas-crochet-y-tejido",
    # Alfileres
    "alfileres":                        "herramientas-de-costura",
    # Planchas industriales
    "planchas-a-vapor-industrial":      "herramientas-de-costura",
}

DEFAULT_UPSELL = "top-65-favoritos"


# ── Helpers ────────────────────────────────────────────────────────────────────

def paginate(path, key, **params):
    items = []
    params.setdefault("limit", 250)
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=45)
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
cols_by_id     = {c["id"]: c for c in all_cols}
print(f"   {len(all_cols)} colecciones")

print("🔍 Obteniendo productos...")
products = paginate("products.json", "products", fields="id,title,handle")
print(f"   {len(products)} productos")

print("🔍 Obteniendo relaciones producto↔colección (collects)...")
collects = paginate("collects.json", "collects", fields="product_id,collection_id")
print(f"   {len(collects)} relaciones")
print()

# Mapa: product_id → [collection_handles]
from collections import defaultdict
prod_cols: dict[int, list[str]] = defaultdict(list)
for c in collects:
    col = cols_by_id.get(c["collection_id"])
    if col:
        prod_cols[c["product_id"]].append(col["handle"])


# ── Asignar upsell ─────────────────────────────────────────────────────────────

def best_upsell_handle(product_id: int) -> str | None:
    handles = prod_cols.get(product_id, [])
    for h in handles:
        target = CROSS_SELL.get(h)
        if target and target in cols_by_handle:
            return target
    return DEFAULT_UPSELL if DEFAULT_UPSELL in cols_by_handle else None


plan = []
unmatched = []
for p in products:
    target_handle = best_upsell_handle(p["id"])
    if target_handle:
        plan.append((p, cols_by_handle[target_handle]))
    else:
        unmatched.append(p)

print(f"📦 Plan: {len(plan)} productos asignados / {len(unmatched)} sin colección upsell")
print()

# Muestra muestra del plan
for p, col in plan[:40]:
    src_handles = ", ".join(prod_cols.get(p["id"], ["?"]))
    print(f"   {p['title'][:42]:42s} [{src_handles[:30]}] → {col['handle']}")
if len(plan) > 40:
    print(f"   ... y {len(plan)-40} más")
print()

if unmatched:
    print(f"⚠️  Sin asignar ({len(unmatched)}):")
    for p in unmatched[:10]:
        print(f"   {p['title']}")
    print()

# ── Aplicar ────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if args.dry_run or not args.apply:
    print("ℹ️  Modo dry-run. Corre con --apply para guardar los cambios.")
    sys.exit(0)

print("🚀 Aplicando metafields...")
ok = err = 0
for p, col in plan:
    col_gid = f"gid://shopify/Collection/{col['id']}"

    # Buscar si ya existe el metafield
    existing = requests.get(
        f"{REST_BASE}/products/{p['id']}/metafields.json",
        headers=HEADERS,
        params={"namespace": "custom", "key": "upsell_collection"},
        timeout=30,
    ).json().get("metafields", [])

    if existing:
        mf_id = existing[0]["id"]
        r = requests.put(
            f"{REST_BASE}/products/{p['id']}/metafields/{mf_id}.json",
            headers=HEADERS,
            json={"metafield": {"id": mf_id, "value": col_gid}},
            timeout=30,
        )
        verb = "↩️ "
    else:
        r = requests.post(
            f"{REST_BASE}/products/{p['id']}/metafields.json",
            headers=HEADERS,
            json={"metafield": {
                "namespace": "custom",
                "key": "upsell_collection",
                "type": "collection_reference",
                "value": col_gid,
                "owner_id": p["id"],
                "owner_resource": "product",
            }},
            timeout=30,
        )
        verb = "✅ "

    if r.status_code in (200, 201):
        print(f"  {verb}{p['title'][:45]:45s} → {col['handle']}")
        ok += 1
    else:
        print(f"  ❌ {p['title'][:45]} — HTTP {r.status_code}: {r.text[:120]}")
        err += 1

    time.sleep(0.25)

print()
print(f"✅ {ok} asignados / ❌ {err} errores")
