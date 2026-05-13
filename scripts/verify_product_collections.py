"""
Verifica que cada producto este en su coleccion correcta.
Detecta productos sin coleccion especifica y productos potencialmente mal categorizados.
"""
import sys, time
from pathlib import Path
from collections import defaultdict, Counter

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Colecciones consideradas "genericas" (no cuentan como categoria especifica)
GENERIC = {
    "catalogo-completo", "top-65-favoritos",
    "maquinas-y-repuestos", "insumos-confeccion", "insumos-de-confeccion",
}

# Reglas: (lista de palabras clave en titulo, coleccion esperada)
# Primera regla que matchea gana
TITLE_RULES = [
    # Hilos
    (["hilo poliester 2000", "hilo 2000", "2000 yardas", "2000 yrds"],  "hilo-2000"),
    (["hilo poliester 5000", "hilo 5000", "5000 yardas"],               "hilo-5000"),
    (["hilo poliamida", "hilo nylon"],                                       "hilo-poliamida"),
    (["hilo overlock", "hilo collareta"],                               "hilo-overlock"),
    (["hilo bordar", "hilo bordado"],                                   "hilos-bordar-profesionales"),
    (["hilo de saco", "hilo saco"],                                     "hilo-de-saco"),
    # Agujas
    (["aguja de mano", "aguja a mano", "aguja circular", "aguja tapiceria",
      "aguja lana", "aguja de tejer"],                                  "agujas-mano"),
    (["aguja industrial", "groz", "beckert", "dbx", "uy128", "dbk", "dax",
      "aguja overlock", "aguja collareta"],                             "aguja-maquina-industrial"),
    (["aguja casera", "aguja schmetz", "aguja singer", "aguja brother",
      "aguja janome", "aguja universal", "aguja bissel"],               "aguja-maquina-casera"),
    (["alfiler"],                                                       "alfileres"),
    # Prensatelas / Repuestos
    (["prensatela", "pie cierre", "pie de cierre", "pie patchwork",
      "pie teflon", "pie zigzag", "pie zig-zag", "pie recogedor",
      "pie ribete", "pie recto", "zapatilla"],                          "prensatelas-para-maquina-de-cos"),
    (["tornillo", "resorte", "tension completa", "tensor",
      "carrete", "disco de friccion", "diente transportador",
      "filtro de aceite", "crochet para maquina", "lanzadera",
      "canilla", "correa", "pedal", "motor", "guarda aguja",
      "devanadora", "ampolleta", "foco led", "aceitera",
      "interruptor", "cuchillo ojaladora", "cuchillo inferior",
      "cuchillo superior", "goma de repuesto"],                         "repuestos-maquinas-de-coser"),
    (["repuesto cortadora", "repuesto para cortadora", "engranaje repuesto", "lija de repuesto", "cuchillo circular repuesto"], "repuestos-de-cortadoras-de-telas"),
    (["cortadora", "cuchilla cortadora"],                               "cortadoras-de-tela-circulares"),
    (["plancha industrial", "plancha vapor", "plancha a vapor"],        "planchas-a-vapor-industrial"),
    # Insumos
    (["elastico", "elástico"],                                          "elasticos-costura"),
    (["cierre", "cremallera"],                                          "cierres"),
    (["broche"],                                                        "broches"),
    (["velcro"],                                                        "velcro"),
    (["cinta satin", "cinta satín"],                                    "cintas-satin"),
    (["cinta algodon", "cinta algodón"],                                "cintas-algodon"),
    (["sesgo", "bies"],                                                 "sesgo-bies"),
    (["huincha mochila", "cinta mochila"],                              "huincha-mochila"),
    (["entretela"],                                                     "entretelas"),
    (["pasamaneria", "pasamanería"],                                    "pasamaneria"),
    (["flecos", "fleco decorativo"],                                    "flecos-decorativos"),
    (["hebilla"],                                                       "hebillas"),
    # Tijeras / Herramientas
    (["tijera"],                                                        "tijeras-profesionales-para-costura"),
    (["regla", "calibrador", "marcador costura"],                       "herramientas-de-costura"),
    # Manualidades / Tejido
    (["lana ovillo", "ovillo de lana", "lana para tejer"],              "lanas-ovillos-crochet-tejido"),
    (["trapillo"],                                                      "trapillo-telas-crochet"),
    (["bastidor"],                                                      "bastidores-bordado"),
    (["argolla"],                                                       "argollas-manualidades"),
    (["cuenca", "cuenta de madera"],                                    "cuencas-madera"),
    (["cascabel"],                                                      "cascabeles-costura-manualidades"),
    (["macrame", "macramé", "cordon trenzado"],                         "macrame-cordon-trenzado"),
    (["lentejuela", "strass"],                                          "lentejuelas-y-strass"),
    (["ganchillo", "crochet"],                                          "crochet-accessories-ganchillos"),
    (["adhesivo tela", "pegamento tela"],                               "adhesivos-telas"),
    (["anilina", "tintura"],                                            "tinturas"),
    (["cordon zapato", "cordón zapato"],                                "cordones-zapatos-costura-manualidades"),
    (["boton"],                                                         "botones"),
]

def match_title(title):
    t = title.lower()
    for keywords, handle in TITLE_RULES:
        if any(k in t for k in keywords):
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

print("Cargando colecciones...")
all_cols = []
for kind in ("custom_collections", "smart_collections"):
    all_cols += paginate(f"{kind}.json", kind, fields="id,handle,title")
cols_by_handle = {c["handle"]: c for c in all_cols}
print(f"  {len(all_cols)} colecciones")

print("Cargando productos...")
products = paginate("products.json", "products", fields="id,title,handle,tags,status")
prod_by_id = {p["id"]: p for p in products}
print(f"  {len(products)} productos")

print("Mapeando colecciones -> productos...")
prod_cols = defaultdict(set)
for col in all_cols:
    prods = paginate(f"collections/{col['id']}/products.json", "products", fields="id")
    for p in prods:
        prod_cols[p["id"]].add(col["handle"])
    time.sleep(0.1)
print()

# Clasificar productos
no_collection      = []   # sin coleccion especifica
wrong_collection   = []   # tiene match en titulo pero no esta en esa coleccion
ok_count           = 0

for p in products:
    if p.get("status") != "active":
        continue
    pid = p["id"]
    current = prod_cols.get(pid, set())
    specific = current - GENERIC

    expected = match_title(p["title"])

    if expected and expected in cols_by_handle:
        if expected in current:
            ok_count += 1
        else:
            wrong_collection.append((p, expected, specific))
    else:
        if not specific:
            no_collection.append(p)
        else:
            ok_count += 1

print("="*60)
print("RESUMEN")
print("="*60)
print(f"  Productos activos: {sum(1 for p in products if p.get('status')=='active')}")
print(f"  OK (con coleccion correcta): {ok_count}")
print(f"  FALTA agregar a coleccion sugerida: {len(wrong_collection)}")
print(f"  SIN coleccion especifica:    {len(no_collection)}")
print()

# Detalle: productos que falta agregar
if wrong_collection:
    print("="*60)
    print(f"PRODUCTOS QUE DEBERIAN ESTAR EN OTRA COLECCION ({len(wrong_collection)}):")
    print("="*60)
    by_target = defaultdict(list)
    for p, expected, current in wrong_collection:
        by_target[expected].append((p, current))
    for target, items in sorted(by_target.items(), key=lambda x: -len(x[1])):
        print(f"\n  -> {target} ({len(items)} productos):")
        for p, current in items[:10]:
            cur_str = ", ".join(sorted(current)) if current else "(ninguna especifica)"
            print(f"     [{p['id']}] {p['title'][:55]:55s}  actual: {cur_str[:40]}")
        if len(items) > 10:
            print(f"     ... y {len(items)-10} mas")

# Detalle: productos sin coleccion
if no_collection:
    print()
    print("="*60)
    print(f"PRODUCTOS ACTIVOS SIN COLECCION ESPECIFICA ({len(no_collection)}):")
    print("="*60)
    for p in no_collection[:40]:
        print(f"  [{p['id']}] {p['title'][:70]}")
    if len(no_collection) > 40:
        print(f"  ... y {len(no_collection)-40} mas")
