"""
Elimina colecciones duplicadas — conserva la de handle más descriptivo
y elimina el alias corto.

Uso:
    python scripts/fix_duplicate_collections.py --dry-run
    python scripts/fix_duplicate_collections.py --apply
"""
import sys, time, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Par: (conservar, eliminar)
# La insumos-de-confeccion vs insumos-confeccion tienen distinto contenido — se omite
DUPLICATES = [
    ("bisuteria-y-decoracion",   "bisuteria-decoracion"),
    ("herramientas-de-costura",  "herramientas-costura"),
    ("tejido-y-manualidades",    "tejido-manualidades"),
    ("tinturas-y-pegamentos",    "tinturas-pegamentos"),
]

def get_all_collections():
    cols = {}
    for kind in ("custom_collections", "smart_collections"):
        url = f"{REST_BASE}/{kind}.json"
        while url:
            r = requests.get(url, headers=HEADERS, params={"limit": 250}, timeout=30)
            r.raise_for_status()
            for c in r.json().get(kind, []):
                cols[c["handle"]] = {**c, "_kind": kind}
            link = r.headers.get("Link", "")
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
    return cols

def delete_collection(col):
    kind = col["_kind"]
    endpoint = "custom_collections" if kind == "custom_collections" else "smart_collections"
    r = requests.delete(
        f"{REST_BASE}/{endpoint}/{col['id']}.json",
        headers=HEADERS,
        timeout=30,
    )
    return r.status_code

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

print("🔍 Cargando colecciones...")
cols = get_all_collections()
print(f"   {len(cols)} colecciones cargadas")
print()

print("📋 Plan:")
for keep_h, delete_h in DUPLICATES:
    keep   = cols.get(keep_h)
    delete = cols.get(delete_h)
    if not keep:
        print(f"  ⚠️  '{keep_h}' no encontrada — omitida")
        continue
    if not delete:
        print(f"  ⚠️  '{delete_h}' no encontrada — omitida")
        continue
    print(f"  ✅ conservar: {keep_h:40s} ({keep['_kind']}, {keep['id']})")
    print(f"  🗑️  eliminar:  {delete_h:40s} ({delete['_kind']}, {delete['id']})")
    print()

if args.dry_run or not args.apply:
    print("ℹ️  Modo dry-run. Corre con --apply para eliminar.")
    sys.exit(0)

print("🚀 Eliminando duplicados...")
for keep_h, delete_h in DUPLICATES:
    keep   = cols.get(keep_h)
    delete = cols.get(delete_h)
    if not keep or not delete:
        continue
    status = delete_collection(delete)
    if status in (200, 201, 204):
        print(f"  ✅ Eliminada: {delete_h}")
    else:
        print(f"  ❌ Error eliminando {delete_h} — HTTP {status}")
    time.sleep(0.5)

print()
print("✅ Listo. Recuerda actualizar los links internos que apunten a los handles eliminados.")
