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

# ═══════════════════════════════════════════════════════════════════════════════
# GRUPOS DE TÉCNICA — cross-sell solo dentro del mismo grupo
# ═══════════════════════════════════════════════════════════════════════════════

# ── Grupo 1: Costura Máquina Casera ──────────────────────────────────────────
# aguja casera ↔ hilos caseros ↔ prensatelas caseros ↔ repuestos

# ── Grupo 2: Costura Máquina Industrial ──────────────────────────────────────
# aguja industrial ↔ hilo overlock ↔ prensatelas industriales

# ── Grupo 3: Bordado ──────────────────────────────────────────────────────────
# hilos bordar ↔ bastidores ↔ agujas mano

# ── Grupo 4: Tejido / Crochet ─────────────────────────────────────────────────
# lanas ↔ agujas crochet/palillos ↔ trapillo

# ── Grupo 5: Insumos Confección ───────────────────────────────────────────────
# cierres ↔ entretelas ↔ elasticos ↔ botones ↔ sesgo ↔ broches

# ── Grupo 6: Herramientas de Corte ────────────────────────────────────────────
# tijeras ↔ herramientas ↔ cortadoras ↔ repuestos cortadoras

# ── Grupo 7: Decoración / Manualidades ───────────────────────────────────────
# bisutería ↔ lentejuelas ↔ pasamanería ↔ cordones ↔ tinturas

# Prioridad: colección más específica gana cuando un producto pertenece a varias
PRIORITY = [
    # G1 - Casera (hilos primero para que un hilo no sea confundido con aguja)
    "hilo-5000",
    "hilo-2000",
    "aguja-maquina-casera",
    "prensatelas-caseros",
    "prensatelas-para-maquina-de-cos",
    # G2 - Industrial
    "hilo-overlock",
    "hilo-poliamida",
    "hilo-de-saco",
    "aguja-maquina-industrial",
    "prensatelas-industriales-1",
    "prensatelas-industriales",
    # G3 - Bordado
    "hilos-bordar-profesionales",
    "bastidores-bordado",
    "agujas-mano",
    # G4 - Tejido / Crochet
    "lanas-ovillos-crochet-tejido",
    "agujas-crochet-y-tejido",
    "crochet-accessories-ganchillos",
    "trapillo-telas-crochet",
    # G5 - Insumos confección
    "cierres",
    "entretelas",
    "elasticos-costura",
    "botones",
    "sesgo-bies",
    "broches",
    "hebillas",
    "velcro",
    "adhesivos-telas",
    "cintas-algodon",
    "cintas-satin",
    "huincha-mochila",
    "alfileres",
    # G6 - Herramientas
    "cortadoras-de-tela-circulares",
    "repuestos-de-cortadoras-de-telas",
    "tijeras-profesionales-para-costura",
    "herramientas-de-costura",
    "herramientas-costura",
    "herramientas",
    # G7 - Decoración / Manualidades
    "bisuteria-y-decoracion",
    "bisuteria-decoracion",
    "lentejuelas-y-strass",
    "pasamaneria",
    "flecos-decorativos",
    "cascabeles-costura-manualidades",
    "argollas-manualidades",
    "cuencas-madera",
    "macrame-cordon-trenzado",
    "cordones-zapatos-costura-manualidades",
    "tinturas",
    "tinturas-y-pegamentos",
    "tinturas-pegamentos",
    # Máquinas / repuestos / planchas
    "maquinas-y-repuestos",
    "accesorios-maquina",
    "repuestos-maquinas-de-coser",
    "planchas-a-vapor-industrial",
]

CROSS_SELL = {
    # ── G1: Costura Máquina Casera ──────────────────────────────────────────
    "hilo-2000":                        "aguja-maquina-casera",
    "hilo-5000":                        "aguja-maquina-casera",
    "aguja-maquina-casera":             "hilo-2000",
    "prensatelas-caseros":              "aguja-maquina-casera",
    "prensatelas-para-maquina-de-cos":  "hilo-2000",
    "repuestos-maquinas-de-coser":      "aguja-maquina-casera",
    "accesorios-maquina":               "aguja-maquina-casera",
    "maquinas-y-repuestos":             "repuestos-maquinas-de-coser",

    # ── G2: Costura Máquina Industrial ──────────────────────────────────────
    "hilo-overlock":                    "aguja-maquina-industrial",
    "hilo-poliamida":                   "aguja-maquina-industrial",
    "hilo-de-saco":                     "aguja-maquina-industrial",
    "aguja-maquina-industrial":         "hilo-overlock",
    "prensatelas-industriales":         "aguja-maquina-industrial",
    "prensatelas-industriales-1":       "hilo-overlock",

    # ── G3: Bordado ──────────────────────────────────────────────────────────
    "hilos-bordar-profesionales":       "bastidores-bordado",
    "bastidores-bordado":               "hilos-bordar-profesionales",
    "agujas-mano":                      "hilos-bordar-profesionales",

    # ── G4: Tejido / Crochet ─────────────────────────────────────────────────
    "lanas-ovillos-crochet-tejido":     "agujas-crochet-y-tejido",
    "agujas-crochet-y-tejido":          "lanas-ovillos-crochet-tejido",
    "crochet-accessories-ganchillos":   "lanas-ovillos-crochet-tejido",
    "trapillo-telas-crochet":           "agujas-crochet-y-tejido",

    # ── G5: Insumos Confección ───────────────────────────────────────────────
    "cierres":                          "entretelas",
    "entretelas":                       "cierres",
    "adhesivos-telas":                  "entretelas",
    "elasticos-costura":                "botones",
    "botones":                          "elasticos-costura",
    "broches":                          "botones",
    "hebillas":                         "elasticos-costura",
    "velcro":                           "elasticos-costura",
    "sesgo-bies":                       "cierres",
    "cintas-algodon":                   "sesgo-bies",
    "cintas-satin":                     "sesgo-bies",
    "huincha-mochila":                  "elasticos-costura",
    "alfileres":                        "herramientas-de-costura",

    # ── G6: Herramientas de Corte ────────────────────────────────────────────
    "cortadoras-de-tela-circulares":    "repuestos-de-cortadoras-de-telas",
    "repuestos-de-cortadoras-de-telas": "cortadoras-de-tela-circulares",
    "tijeras-profesionales-para-costura": "herramientas-de-costura",
    "herramientas-de-costura":          "tijeras-profesionales-para-costura",
    "herramientas-costura":             "tijeras-profesionales-para-costura",
    "herramientas":                     "tijeras-profesionales-para-costura",
    "planchas-a-vapor-industrial":      "herramientas-de-costura",

    # ── G7: Decoración / Manualidades ────────────────────────────────────────
    "bisuteria-y-decoracion":           "lentejuelas-y-strass",
    "bisuteria-decoracion":             "lentejuelas-y-strass",
    "lentejuelas-y-strass":             "bisuteria-y-decoracion",
    "flecos-decorativos":               "pasamaneria",
    "pasamaneria":                      "flecos-decorativos",
    "cascabeles-costura-manualidades":  "bisuteria-y-decoracion",
    "argollas-manualidades":            "bisuteria-y-decoracion",
    "cuencas-madera":                   "bisuteria-y-decoracion",
    "macrame-cordon-trenzado":          "cordones-zapatos-costura-manualidades",
    "cordones-zapatos-costura-manualidades": "macrame-cordon-trenzado",
    "tinturas":                         "herramientas-de-costura",
    "tinturas-y-pegamentos":            "tinturas",
    "tinturas-pegamentos":              "tinturas",
}

# Sin match específico → no asignar (evita mezclar catálogo completo)
DEFAULT_UPSELL = None

# Colecciones genéricas que no sirven para cross-sell — ignorar al hacer match
EXCLUDE_FROM_MATCHING = {
    "top-65-favoritos",
    "catalogo-completo",
    "insumos-de-confeccion",
    "insumos-confeccion",
    "materiales-para-manualidades",
    "tejido-y-manualidades",
    "tejido-manualidades",
}


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

# collects.json solo cubre colecciones manuales; para smart collections
# hay que consultar cada colección individualmente.
print("🔍 Mapeando productos por colección (manual + smart)...")
from collections import defaultdict
prod_cols: dict[int, list[str]] = defaultdict(list)
total_rels = 0
for col in all_cols:
    col_products = paginate(
        f"collections/{col['id']}/products.json", "products",
        fields="id", limit=250,
    )
    for p in col_products:
        prod_cols[p["id"]].append(col["handle"])
        total_rels += 1
    time.sleep(0.15)  # evitar rate limit
print(f"   {total_rels} relaciones (manual + smart)")


# ── Asignar upsell ─────────────────────────────────────────────────────────────

def best_upsell_handle(product_id: int) -> str | None:
    handles = set(prod_cols.get(product_id, [])) - EXCLUDE_FROM_MATCHING
    # Revisar primero en orden de PRIORITY, luego el resto
    ordered = [h for h in PRIORITY if h in handles] + [h for h in handles if h not in PRIORITY]
    for h in ordered:
        target = CROSS_SELL.get(h)
        if target and target in cols_by_handle:
            return target
    if DEFAULT_UPSELL and DEFAULT_UPSELL in cols_by_handle:
        return DEFAULT_UPSELL
    return None


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
