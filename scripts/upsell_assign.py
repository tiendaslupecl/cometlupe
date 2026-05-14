"""
Asigna custom.upsell_collection a cada producto basÃ¡ndose en las colecciones
a las que ya pertenece (no en palabras del tÃ­tulo).

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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# GRUPOS DE TÃ‰CNICA â€” cross-sell solo dentro del mismo grupo
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â”€â”€ Grupo 1: Costura MÃ¡quina Casera â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# aguja casera â†” hilos caseros â†” prensatelas caseros â†” repuestos

# â”€â”€ Grupo 2: Costura MÃ¡quina Industrial â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# aguja industrial â†” hilo overlock â†” prensatelas industriales

# â”€â”€ Grupo 3: Bordado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# hilos bordar â†” bastidores â†” agujas mano

# â”€â”€ Grupo 4: Tejido / Crochet â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# lanas â†” agujas crochet/palillos â†” trapillo

# â”€â”€ Grupo 5: Insumos ConfecciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# cierres â†” entretelas â†” elasticos â†” botones â†” sesgo â†” broches

# â”€â”€ Grupo 6: Herramientas de Corte â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# tijeras â†” herramientas â†” cortadoras â†” repuestos cortadoras

# â”€â”€ Grupo 7: DecoraciÃ³n / Manualidades â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# bisuterÃ­a â†” lentejuelas â†” pasamanerÃ­a â†” cordones â†” tinturas

# Prioridad: colecciÃ³n mÃ¡s especÃ­fica gana cuando un producto pertenece a varias
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
    # G5 - Insumos confecciÃ³n
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
    # G7 - DecoraciÃ³n / Manualidades
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
    # MÃ¡quinas / repuestos / planchas
    "maquinas-y-repuestos",
    "accesorios-maquina",
    "repuestos-maquinas-de-coser",
    "planchas-a-vapor-industrial",
]

CROSS_SELL = {
    # â”€â”€ G1: Costura MÃ¡quina Casera â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "hilo-2000":                        "aguja-maquina-casera",
    "hilo-5000":                        "aguja-maquina-casera",
    "aguja-maquina-casera":             "hilo-2000",
    "prensatelas-caseros":              "aguja-maquina-casera",
    "prensatelas-para-maquina-de-cos":  "hilo-2000",
    "repuestos-maquinas-de-coser":      "aguja-maquina-casera",
    "accesorios-maquina":               "aguja-maquina-casera",
    "maquinas-y-repuestos":             "repuestos-maquinas-de-coser",

    # â”€â”€ G2: Costura MÃ¡quina Industrial â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "hilo-overlock":                    "aguja-maquina-industrial",
    "hilo-poliamida":                   "aguja-maquina-industrial",
    "hilo-de-saco":                     "aguja-maquina-industrial",
    "aguja-maquina-industrial":         "hilo-jeans",
    "prensatelas-industriales":         "aguja-maquina-industrial",
    "prensatelas-industriales-1":       "hilo-overlock",

    # â”€â”€ G3: Bordado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "hilos-bordar-profesionales":       "bastidores-bordado",
    "bastidores-bordado":               "hilos-bordar-profesionales",
    "agujas-mano":                      "hilos-bordar-profesionales",

    # â”€â”€ G4: Tejido / Crochet â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "lanas-ovillos-crochet-tejido":     "agujas-crochet-y-tejido",
    "agujas-crochet-y-tejido":          "lanas-ovillos-crochet-tejido",
    "crochet-accessories-ganchillos":   "lanas-ovillos-crochet-tejido",
    "trapillo-telas-crochet":           "agujas-crochet-y-tejido",

    # â”€â”€ G5: Insumos ConfecciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    # â”€â”€ G6: Herramientas de Corte â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "cortadoras-de-tela-circulares":    "repuestos-de-cortadoras-de-telas",
    "repuestos-de-cortadoras-de-telas": "cortadoras-de-tela-circulares",
    "tijeras-profesionales-para-costura": "herramientas-de-costura",
    "herramientas-de-costura":          "tijeras-profesionales-para-costura",
    "herramientas-costura":             "tijeras-profesionales-para-costura",
    "herramientas":                     "tijeras-profesionales-para-costura",
    "planchas-a-vapor-industrial":      "herramientas-de-costura",

    # â”€â”€ G7: DecoraciÃ³n / Manualidades â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "bisuteria-y-decoracion":           "lentejuelas-y-strass",
    "bisuteria-decoracion":             "lentejuelas-y-strass",
    "lentejuelas-y-strass":             "bisuteria-y-decoracion",
    "flecos-decorativos":               "pasamaneria",
    "pasamaneria":                      "flecos-decorativos",
    "cascabeles-costura-manualidades":  "bisuteria-y-decoracion",
    "argollas-manualidades":            "bisuteria-y-decoracion",
    "cuencas-madera":                   "bisuteria-y-decoracion",
    "macrame-cordon-trenzado":          "materiales-para-manualidades",
    "cordones-zapatos-costura-manualidades": "materiales-para-manualidades",
    "tinturas":                         "herramientas-de-costura",
    "tinturas-y-pegamentos":            "tinturas",
    "tinturas-pegamentos":              "tinturas",
}

# Sin match especÃ­fico â†’ no asignar (evita mezclar catÃ¡logo completo)
DEFAULT_UPSELL = None

# Colecciones genÃ©ricas que no sirven para cross-sell â€” ignorar al hacer match
EXCLUDE_FROM_MATCHING = {
    "top-65-favoritos",
    "catalogo-completo",
    "insumos-de-confeccion",
    "insumos-confeccion",
    "materiales-para-manualidades",
    "tejido-y-manualidades",
    "tejido-manualidades",
}


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Fetch data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

print("ðŸ” Obteniendo colecciones...")
custom_cols = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart_cols  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
all_cols    = custom_cols + smart_cols
cols_by_handle = {c["handle"]: c for c in all_cols}
cols_by_id     = {c["id"]: c for c in all_cols}
print(f"   {len(all_cols)} colecciones")

print("ðŸ” Obteniendo productos...")
products = paginate("products.json", "products", fields="id,title,handle")
print(f"   {len(products)} productos")

# collects.json solo cubre colecciones manuales; para smart collections
# hay que consultar cada colecciÃ³n individualmente.
print("ðŸ” Mapeando productos por colecciÃ³n (manual + smart)...")
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


# â”€â”€ Asignar upsell â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Override por tÃ­tulo: mÃ¡s especÃ­fico que colecciÃ³n (ej: bordadora dentro de industrial)
TITLE_OVERRIDES = [
    (["jeans", "coser jeans", "hilo de pesca"], "hilo-jeans"),
    (["plancha de aguja", "plancha aguja", "guarda aguja", "devanadora", "ampolleta"], "repuestos-maquinas-de-coser"),
    (["llave allen", "pinza de preci", "lubricador", "zurcido", "protector de dedo"], "repuestos-maquinas-de-coser"),
    (["crochet para maquina", "crochet overlock", "crochet siruba"], "repuestos-maquinas-de-coser"),
    (["correa dentada", "correa para maquina", "cana para prensatela", "guia de hilo"], "repuestos-maquinas-de-coser"),
    (["bissel", "aguja doble"], "aguja-maquina-casera"),
    (["f6000", "pegamento para tela", "adhesivo para tela"], "materiales-para-manualidades"),
    (["bordadora", "bordado", "dbk"], "hilos-bordar-profesionales"),
    (["schmetz", "singer"], "hilo-2000"),
    (["groz", "beckert", "gb "], "hilo-overlock"),
    (["macrame"], "macrame-cordon-trenzado"),
    (["palillo", "circular de acero"], "lanas-ovillos-crochet-tejido"),
    (["lana "], "lanas-ovillos-crochet-tejido"),
    (["hilo coser", "industrial gris"], "hilo-2000"),
]

def best_upsell_handle(product_id: int, title: str = "") -> str | None:
    t = title.lower()
    # 1. Override por tÃ­tulo (mÃ¡s especÃ­fico)
    for keywords, handle in TITLE_OVERRIDES:
        if any(k in t for k in keywords) and handle in cols_by_handle:
            return handle
    # 2. Por colecciÃ³n con prioridad
    handles = set(prod_cols.get(product_id, [])) - EXCLUDE_FROM_MATCHING
    ordered = [h for h in PRIORITY if h in handles] + [h for h in handles if h not in PRIORITY]
    for h in ordered:
        target = CROSS_SELL.get(h)
        if target and target in cols_by_handle:
            return target
    if DEFAULT_UPSELL and DEFAULT_UPSELL in cols_by_handle:
        return DEFAULT_UPSELL
    return None


# Sugerencia de colecciÃ³n para los sin asignar (por palabras en el tÃ­tulo)
TITLE_SUGGESTIONS = [
    (["palillo"],                                   "agujas-crochet-y-tejido"),
    (["aceitera", "aceite", "ampolleta", "foco"],   "repuestos-maquinas-de-coser"),
    (["bobina", "lanzadera", "canilla"],             "repuestos-maquinas-de-coser"),
    (["bastidor"],                                   "bastidores-bordado"),
    (["macramÃ©", "macrame", "cordÃ³n trenzado", "cordon trenzado"], "macrame-cordon-trenzado"),
    (["cordÃ³n", "cordon"],                           "cordones-zapatos-costura-manualidades"),
    (["tijera", "descosedor"],                       "herramientas-de-costura"),
    (["cinta", "sesgo", "bies"],                     "cierres"),
    (["elÃ¡stico", "elastico"],                       "elasticos-costura"),
    (["botÃ³n", "boton"],                             "botones"),
    (["hilo overlock", "overlock"],                  "hilo-overlock"),
    (["hilo bordar", "bordar"],                      "hilos-bordar-profesionales"),
    (["hilo"],                                       "hilo-2000"),
    (["aguja mano", "aguja a mano"],                 "agujas-mano"),
    (["schmetz", "singer"],                          "aguja-maquina-casera"),
    (["groz", "beckert", "industrial"],              "aguja-maquina-industrial"),
    (["aguja"],                                      "aguja-maquina-casera"),
    (["lana", "ovillo"],                             "lanas-ovillos-crochet-tejido"),
    (["cierre", "cremallera"],                       "cierres"),
    (["entretela"],                                  "entretelas"),
    (["tintura", "anilina"],                         "tinturas"),
    (["broche"],                                     "broches"),
    (["hebilla"],                                    "hebillas"),
    (["repuesto", "accesorio maquina"],              "repuestos-maquinas-de-coser"),
]

def suggest_by_title(title: str) -> str:
    t = title.lower()
    for keywords, handle in TITLE_SUGGESTIONS:
        if any(k in t for k in keywords):
            if handle in cols_by_handle:
                return handle
    return "â€” sin sugerencia â€”"


plan = []
unmatched = []
for p in products:
    target_handle = best_upsell_handle(p["id"], p.get("title", ""))
    if target_handle:
        plan.append((p, cols_by_handle[target_handle]))
    else:
        unmatched.append(p)

print(f"ðŸ“¦ Plan: {len(plan)} productos asignados / {len(unmatched)} sin colecciÃ³n upsell")
print()

# Muestra muestra del plan
for p, col in plan[:40]:
    src_handles = ", ".join(prod_cols.get(p["id"], ["?"]))
    print(f"   {p['title'][:42]:42s} [{src_handles[:30]}] â†’ {col['handle']}")
if len(plan) > 40:
    print(f"   ... y {len(plan)-40} mÃ¡s")
print()

if unmatched:
    print(f"âš ï¸  Sin asignar ({len(unmatched)}) â€” agregar a la colecciÃ³n sugerida en Shopify Admin:")
    print(f"   {'Producto':50s}  {'ColecciÃ³n sugerida'}")
    print(f"   {'-'*50}  {'-'*35}")
    for p in unmatched:
        suggestion = suggest_by_title(p["title"])
        print(f"   {p['title'][:50]:50s}  {suggestion}")
    print()

# â”€â”€ Aplicar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if args.dry_run or not args.apply:
    print("â„¹ï¸  Modo dry-run. Corre con --apply para guardar los cambios.")
    sys.exit(0)

print("ðŸš€ Aplicando metafields...")
ok = err = 0
for p, col in plan:
    col_handle = col["handle"]

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
            json={"metafield": {"id": mf_id, "value": col_handle, "type": "single_line_text_field"}},
            timeout=30,
        )
        verb = "â†©ï¸ "
    else:
        r = requests.post(
            f"{REST_BASE}/products/{p['id']}/metafields.json",
            headers=HEADERS,
            json={"metafield": {
                "namespace": "custom",
                "key": "upsell_collection",
                "type": "single_line_text_field",
                "value": col_handle,
                "owner_id": p["id"],
                "owner_resource": "product",
            }},
            timeout=30,
        )
        verb = "âœ… "

    if r.status_code in (200, 201):
        print(f"  {verb}{p['title'][:45]:45s} â†’ {col['handle']}")
        ok += 1
    else:
        print(f"  âŒ {p['title'][:45]} â€” HTTP {r.status_code}: {r.text[:120]}")
        err += 1

    time.sleep(0.25)

print()
print(f"âœ… {ok} asignados / âŒ {err} errores")


