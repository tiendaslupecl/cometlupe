"""
Auditoria inversa: para cada coleccion clave, detecta productos que NO deberian estar ahi.
Por ejemplo: tornillos dentro de agujas, prensatelas dentro de agujas, etc.
"""
import sys, time
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

def norm(s):
    s = s.lower()
    for a, b in [("\u00e1","a"),("\u00e9","e"),("\u00ed","i"),("\u00f3","o"),("\u00fa","u"),("\u00f1","n")]:
        s = s.replace(a, b)
    return s

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

RULES = {
    "aguja-maquina-casera": {
        "must": ["aguja"],
        "exclude": ["tornillo","plancha de aguja","guarda aguja","barra de aguja","porta aguja","placa aguja","aguja de mano","aguja a mano","aguja circular","aguja tapiceria","aguja lana","aguja de tejer","groz","beckert","dbx","dbk","uy128","dax","aguja industrial","aguja overlock","aguja collareta","bordadora industrial"],
    },
    "aguja-maquina-industrial": {
        "must": ["aguja"],
        "exclude": ["tornillo","plancha de aguja","guarda aguja","barra de aguja","porta aguja","placa aguja","aguja de mano","aguja a mano","aguja circular","aguja tapiceria","aguja lana","aguja de tejer","aguja casera","schmetz","singer universal","aguja bissel"],
    },
    "agujas-mano": {
        "must": ["aguja","alfiler"],
        "exclude": ["tornillo","schmetz","groz","beckert","singer universal","dbx","dbk","uy128","aguja casera","aguja industrial"],
    },
    "prensatelas-para-maquina-de-cos": {
        "must": ["prensatela","pie ","zapatilla"],
        "exclude": ["aguja schmetz","aguja singer","tornillo solo","hilo ","cremallera ","elastico"],
    },
    "repuestos-maquinas-de-coser": {
        "must": ["tornillo","resorte","tension","carrete","disco","diente","filtro","crochet para","lanzadera","canilla","correa","pedal","motor","guarda","devanadora","ampolleta","foco","aceitera","interruptor","cuchillo","goma de repuesto","repuesto","barra de aguja","porta aguja","soporte","guia","placa","rueda","engranaje","palanca","perilla","boton","regulador","balanza"],
        "exclude": ["aguja schmetz","aguja singer","aguja groz","aguja beckert","aguja bissel","aguja industrial","aguja casera","aguja de mano","prensatela","hilo poliester","hilo poliamida"],
    },
    "cortadoras-de-tela-circulares": {"must": ["cortadora","cutter"], "exclude": ["repuesto","cuchilla cortadora","lija cortadora","filo cortadora"]},
    "repuestos-de-cortadoras-de-telas": {"must": ["cortadora","cuchilla","lija","filo","tornillo","repuesto"], "exclude": []},
    "planchas-a-vapor-industrial": {"must": ["plancha"], "exclude": ["plancha de aguja","repuesto plancha"]},
    "hilo-2000": {"must": ["hilo","2000"], "exclude": ["5000","bordar","bordado","poliamida","nylon","overlock","collareta"]},
    "hilo-5000": {"must": ["hilo","5000"], "exclude": ["2000","bordar","bordado","poliamida","nylon"]},
    "hilo-poliamida": {"must": ["hilo","poliamida","nylon"], "exclude": ["bordar","bordado","2000","5000","cierre","cremallera"]},
    "hilo-overlock": {"must": ["hilo","overlock","collareta"], "exclude": ["bordar"]},
    "hilos-bordar-profesionales": {"must": ["hilo","bordar","bordado","durafill"], "exclude": ["2000 yardas","5000 yardas","poliamida"]},
    "elasticos-costura": {"must": ["elastico"], "exclude": ["hilo","cinta","broche"]},
    "cierres": {"must": ["cierre","cremallera"], "exclude": ["pie cierre","prensatela"]},
    "broches": {"must": ["broche","ojetillo","remache","ojetilladora","alicate"], "exclude": ["elastico","cinta"]},
    "velcro": {"must": ["velcro"], "exclude": []},
    "cintas-satin": {"must": ["cinta satin","satin"], "exclude": ["algodon","mochila","sesgo","bies"]},
    "cintas-algodon": {"must": ["cinta","algodon","espiga","lona"], "exclude": ["satin","mochila"]},
    "sesgo-bies": {"must": ["sesgo","bies"], "exclude": []},
    "huincha-mochila": {"must": ["mochila","huincha"], "exclude": []},
    "entretelas": {"must": ["entretela"], "exclude": []},
    "tijeras-profesionales-para-costura": {"must": ["tijera"], "exclude": []},
    "alfileres": {"must": ["alfiler"], "exclude": []},
    "botones": {"must": ["boton"], "exclude": ["broche","regulador"]},
    "hebillas": {"must": ["hebilla"], "exclude": []},
    "accesorios-maquina": {"must": ["tornillo","plancha","guarda","porta","guia","barra","soporte","placa","accesorio","prensatela"], "exclude": []},
}

print("Cargando colecciones y productos...")
all_cols = []
for kind in ("custom_collections","smart_collections"):
    all_cols += paginate(f"{kind}.json", kind, fields="id,handle,title")
cols_by_handle = {c["handle"]: c for c in all_cols}

intruders_by_col = defaultdict(list)
totals = {}

for handle, rules in RULES.items():
    col = cols_by_handle.get(handle)
    if not col:
        print(f"  [SKIP] {handle} no existe")
        continue
    prods = paginate(f"collections/{col['id']}/products.json", "products", fields="id,title,status")
    active = [p for p in prods if p.get("status") == "active"]
    totals[handle] = len(active)
    must = [norm(m) for m in rules["must"]]
    exc  = [norm(e) for e in rules["exclude"]]
    for p in active:
        t = norm(p["title"])
        ok = any(m in t for m in must) if must else True
        bad = any(e in t for e in exc) if exc else False
        if not ok or bad:
            reason = "no_match_must" if not ok else "matches_exclude"
            intruders_by_col[handle].append((p, reason))
    time.sleep(0.1)

print()
print("=" * 70)
print("RESUMEN DE INTRUSOS POR COLECCION")
print("=" * 70)
total_intruders = 0
for handle in RULES:
    if handle not in totals: continue
    n = len(intruders_by_col.get(handle, []))
    total_intruders += n
    marker = "  " if n == 0 else "!!"
    print(f"  {marker} {handle:45s} {n:3d} intrusos / {totals[handle]:3d} productos")
print()
print(f"TOTAL: {total_intruders} productos potencialmente mal categorizados")
print()

if total_intruders:
    print("=" * 70)
    print("DETALLE")
    print("=" * 70)
    for handle, items in intruders_by_col.items():
        if not items: continue
        print(f"\n>>> {handle} ({len(items)} intrusos):")
        for p, reason in items[:25]:
            tag = "[no-match]" if reason == "no_match_must" else "[excluded]"
            print(f"   {tag} [{p['id']}] {p['title'][:70]}")
        if len(items) > 25:
            print(f"   ... y {len(items)-25} mas")
