"""
Redistribuye los 252 productos de maquinas-y-repuestos a sus colecciones
específicas según el título. Agrega el producto a la colección correcta
(no lo quita de maquinas-y-repuestos, eso se puede hacer después).

Uso:
    python scripts/fix_maquinas_repuestos.py --dry-run
    python scripts/fix_maquinas_repuestos.py --apply
"""
import sys, time, argparse
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Reglas por título → colección destino (primera que coincida gana)
# IMPORTANTE: agujas van ANTES que prensatelas — títulos como
# "Aguja Singer + Prensatela" deben ir a agujas, no a prensatelas.
RULES = [
    # Agujas a mano (primero)
    (["aguja de mano", "aguja a mano", "aguja tapiceria",
      "aguja tapicería", "aguja lana", "aguja bordado a mano",
      "aguja circular", "aguja de tejer"],               "agujas-mano"),
    # Agujas máquina industrial
    (["aguja industrial", "aguja para máquina industrial",
      "aguja overlock", "aguja collareta", "aguja recta industrial",
      "groz", "beckert", "dbx", "uy128", "dbk", "dax"],
                                                        "aguja-maquina-industrial"),
    # Agujas máquina casera
    (["aguja casera", "aguja doméstica", "aguja domestica",
      "aguja schmetz", "aguja singer", "aguja brother", "aguja janome",
      "aguja para máquina casera", "aguja para maquina casera",
      "aguja universal", "aguja bissel"],               "aguja-maquina-casera"),
    # Prensatelas (después de agujas)
    (["prensatela industrial", "prensatelas industrial",
      "recta industrial", "overlock industrial", "collareta industrial",
      "flatlock", "presser foot industrial"],           "prensatelas-para-maquina-de-cos"),
    (["prensatela casera", "prensatela doméstica", "prensatela domestica",
      "prensatela para máquina casera", "prensatela para maquina casera",
      "prensatela singer", "prensatela brother", "prensatela janome"],
                                                        "prensatelas-para-maquina-de-cos"),
    (["prensatela"],                                    "prensatelas-para-maquina-de-cos"),
    # Repuestos máquinas
    (["bobina", "lanzadera", "canilla", "correa", "pedal", "motor",
      "guarda aguja", "guía de hilo", "guia de hilo", "devanadora",
      "tensor", "tensión", "tension completa",
      "prensatelas pie", "piñón", "pinon",
      "ampolleta", "foco led", "aceitera", "brocha",
      "tornillo", "resorte", "interruptor",
      "carrete jumbo", "disco de friccion", "disco de fricción",
      "goma de repuesto", "goma para devanador",
      "cuchillo ojaladora", "cuchillo corta", "cuchillo inferior",
      "cuchillo superior", "cuchillo para overlock", "cuchillo para siruba",
      "cuchillo para yamato",
      "repuesto para máquina", "repuesto para maquina",
      "crochet para", "diente transportador", "filtro de aceite",
      "ref. ", " ref."],                               "repuestos-maquinas-de-coser"),
    # Accesorios máquina
    (["accesorio", "accesorios para máquina", "accesorios maquina",
      "guía magnética", "guia magnetica", "guía aérea", "guia aerea",
      "calibrador", "regla"],                           "repuestos-maquinas-de-coser"),
    # Herramientas costura
    (["herramienta manual", "herramienta para costura", "reach para"],
                                                        "herramientas-de-costura"),
    # Cierres
    (["cierre", "cremallera", "diente de perro"],       "cierres-y-cremalleras-para-costura"),
    # Cortadoras
    (["cortadora", "cuchilla cortadora", "repuesto cortadora"],
                                                        "cortadoras-de-tela-circulares"),
    # Planchas
    (["plancha", "planchas"],                           "planchas-a-vapor-industrial"),
]

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

def get_all_collections():
    cols = {}
    for kind in ("custom_collections", "smart_collections"):
        for c in paginate(f"{kind}.json", kind, fields="id,handle,title"):
            cols[c["handle"]] = c
    return cols

def match_rule(title):
    t = title.lower()
    for keywords, handle in RULES:
        if any(k in t for k in keywords):
            return handle
    return None

print("🔍 Cargando datos...")
cols = get_all_collections()

# Obtener productos de maquinas-y-repuestos
maq_col = cols.get("maquinas-y-repuestos")
if not maq_col:
    raise SystemExit("❌ No se encontró maquinas-y-repuestos")

products = paginate(
    f"collections/{maq_col['id']}/products.json", "products",
    fields="id,title,handle"
)
print(f"   {len(products)} productos en maquinas-y-repuestos")
print()

# Obtener colecciones actuales de cada producto
prod_current_cols = defaultdict(set)
collects = paginate("collects.json", "collects", fields="product_id,collection_id")
col_id_to_handle = {c["id"]: c["handle"] for c in cols.values()}
for col_entry in collects:
    h = col_id_to_handle.get(col_entry["collection_id"])
    if h:
        prod_current_cols[col_entry["product_id"]].add(h)

# Construir plan
plan = []        # (product, target_handle) — productos a mover
no_match = []    # productos sin regla

for p in products:
    target = match_rule(p["title"])
    if target and target in cols:
        current = prod_current_cols.get(p["id"], set())
        if target not in current:
            plan.append((p, target))
        # si ya está en la colección correcta, no hace falta mover
    else:
        no_match.append(p)

print(f"📦 Plan: {len(plan)} productos a agregar a colecciones específicas")
print(f"   {len(no_match)} sin regla (requieren revisión manual)")
print()

# Mostrar plan agrupado por colección destino
from collections import Counter
dest_counts = Counter(h for _, h in plan)
for handle, count in sorted(dest_counts.items(), key=lambda x: -x[1]):
    title = cols[handle]["title"]
    print(f"   {count:3d} productos → {handle} ({title})")
print()

if no_match:
    print(f"⚠️  Sin regla ({len(no_match)}) — revisar manualmente:")
    for p in no_match[:30]:
        print(f"   {p['title'][:70]}")
    if len(no_match) > 30:
        print(f"   ... y {len(no_match)-30} más")
    print()

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if args.dry_run or not args.apply:
    print("ℹ️  Modo dry-run. Corre con --apply para aplicar.")
    sys.exit(0)

print("🚀 Agregando productos a colecciones específicas...")
ok = err = skip = 0
for p, target_handle in plan:
    col = cols[target_handle]
    # Solo se puede agregar manualmente a custom_collections (collects API)
    # Para smart collections los productos se agregan automáticamente por reglas
    # Verificamos si es custom o smart
    is_custom = False
    r_check = requests.get(
        f"{REST_BASE}/custom_collections/{col['id']}.json",
        headers=HEADERS, timeout=20
    )
    is_custom = r_check.status_code == 200

    if is_custom:
        r = requests.post(
            f"{REST_BASE}/collects.json",
            headers=HEADERS,
            json={"collect": {"product_id": p["id"], "collection_id": col["id"]}},
            timeout=30,
        )
        if r.status_code in (200, 201):
            print(f"  ✅ {p['title'][:50]:50s} → {target_handle}")
            ok += 1
        elif r.status_code == 422:
            skip += 1  # ya estaba
        else:
            print(f"  ❌ {p['title'][:50]} HTTP {r.status_code}: {r.text[:80]}")
            err += 1
    else:
        print(f"  ℹ️  {p['title'][:50]:50s} → {target_handle} (smart — se asigna por reglas)")
        skip += 1
    time.sleep(0.2)

print()
print(f"✅ {ok} agregados / ⏭️  {skip} omitidos / ❌ {err} errores")
