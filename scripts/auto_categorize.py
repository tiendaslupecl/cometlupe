"""Auto-categoriza productos creados en ultimas N horas."""
import sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shopify_client import REST_BASE, HEADERS
import requests

APPLY = "--apply" in sys.argv
SINCE = 24
if "--since-hours" in sys.argv:
    SINCE = int(sys.argv[sys.argv.index("--since-hours")+1])

TITLE_RULES = [
 (["hilo poliester 2000","hilo 2000","2000 yardas"], "hilo-2000"),
 (["hilo poliester 5000","hilo 5000","5000 yardas"], "hilo-5000"),
 (["hilo poliamida","hilo nylon"], "hilo-poliamida"),
 (["hilo overlock","hilo collareta"], "hilo-overlock"),
 (["hilo bordar","hilo bordado","durafill"], "hilos-bordar-profesionales"),
 (["aguja de mano","aguja a mano","aguja circular","aguja tapiceria","aguja lana","aguja de tejer"], "agujas-mano"),
 (["aguja industrial","groz","beckert","dbx","uy128","dbk","dax","aguja overlock","aguja collareta"], "aguja-maquina-industrial"),
 (["aguja casera","aguja schmetz","aguja singer","aguja brother","aguja janome","aguja universal","aguja bissel"], "aguja-maquina-casera"),
 (["alfiler"], "alfileres"),
 (["prensatela","pie cierre","pie patchwork","pie teflon","pie zigzag","pie recto","zapatilla"], "prensatelas-para-maquina-de-cos"),
 (["tornillo","resorte","tension completa","carrete","diente transportador","crochet para","lanzadera","canilla","correa","pedal","motor","guarda aguja","devanadora"], "repuestos-maquinas-de-coser"),
 (["cortadora","cuchilla cortadora"], "cortadoras-de-tela-circulares"),
 (["plancha industrial","plancha vapor","plancha a vapor"], "planchas-a-vapor-industrial"),
 (["elastico"], "elasticos-costura"),
 (["cierre","cremallera"], "cierres"),
 (["broche","ojetillo","remache"], "broches"),
 (["velcro"], "velcro"),
 (["cinta satin","satin"], "cintas-satin"),
 (["cinta algodon","cinta espiga","cinta lona"], "cintas-algodon"),
 (["sesgo","bies"], "sesgo-bies"),
 (["huincha mochila","cinta mochila"], "huincha-mochila"),
 (["entretela"], "entretelas"),
 (["tijera"], "tijeras-profesionales-para-costura"),
 (["lentejuela","strass"], "lentejuelas-y-strass"),
 (["hebilla"], "hebillas"),
 (["boton"], "botones"),
]

def norm(s):
    s = s.lower()
    for a,b in [("\u00e1","a"),("\u00e9","e"),("\u00ed","i"),("\u00f3","o"),("\u00fa","u"),("\u00f1","n")]:
        s = s.replace(a,b)
    return s

def expected(title):
    t = norm(title)
    for keys, handle in TITLE_RULES:
        if any(norm(k) in t for k in keys):
            return handle
    return None

_cache = {}
def get_col(handle):
    if handle in _cache: return _cache[handle]
    for kind in ("custom_collections","smart_collections"):
        r = requests.get(f"{REST_BASE}/{kind}.json", headers=HEADERS,
                         params={"handle":handle,"fields":"id,handle"}, timeout=30)
        items = r.json().get(kind, [])
        if items:
            _cache[handle] = (items[0]["id"], kind.replace("_collections",""))
            return _cache[handle]
    _cache[handle] = (None, None)
    return None, None

since = datetime.now(timezone.utc) - timedelta(hours=SINCE)
since_iso = since.strftime("%Y-%m-%dT%H:%M:%S-00:00")
print(f"Buscando productos creados desde {since_iso}")
print(f"Modo: {'APPLY' if APPLY else 'DRY-RUN'}")
print()

r = requests.get(f"{REST_BASE}/products.json", headers=HEADERS,
                 params={"created_at_min": since_iso, "status":"active",
                         "limit":250, "fields":"id,title,tags"}, timeout=45)
r.raise_for_status()
prods = r.json().get("products", [])
print(f"Encontrados {len(prods)} productos activos\n")

actions = 0
for p in prods:
    handle = expected(p["title"])
    if not handle:
        print(f"  ?  [{p['id']}] {p['title'][:60]} - sin regla")
        continue
    col_id, kind = get_col(handle)
    if not col_id:
        print(f"  !  [{p['id']}] -> {handle} (no existe)")
        continue
    cr = requests.get(f"{REST_BASE}/collects.json", headers=HEADERS,
                      params={"product_id": p["id"], "collection_id": col_id}, timeout=30)
    if cr.json().get("collects"):
        continue
    tag = f"cat-{handle}"
    tags = {t.strip() for t in (p.get("tags","") or "").split(",") if t.strip()}
    if kind == "custom":
        print(f"  +  [{p['id']}] {p['title'][:55]} -> {handle}")
        if APPLY:
            requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
                          json={"collect":{"product_id":p["id"],"collection_id":col_id}}, timeout=30)
            actions += 1
    elif kind == "smart":
        if tag not in tags:
            tags.add(tag)
            print(f"  +  [{p['id']}] {p['title'][:55]} -> tag {tag}")
            if APPLY:
                requests.put(f"{REST_BASE}/products/{p['id']}.json", headers=HEADERS,
                             json={"product":{"id":p["id"],"tags":", ".join(sorted(tags))}}, timeout=30)
                actions += 1
    time.sleep(0.15)

print(f"\n{actions} acciones {'aplicadas' if APPLY else 'pendientes'}")
