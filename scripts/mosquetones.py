import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

PRODUCT_IDS = [9400251973783, 9400251547799]
APPLY = "--apply" in sys.argv

all_cols = []
for kind in ("custom_collections", "smart_collections"):
    r = requests.get(f"{REST_BASE}/{kind}.json", headers=HEADERS,
                     params={"fields": "id,handle", "limit": 250}, timeout=45)
    all_cols += r.json().get(kind, [])
cols = {c["handle"]: c["id"] for c in all_cols}

hebillas_id = cols.get("hebillas")
if not hebillas_id:
    print("ERROR: coleccion hebillas no encontrada")
    sys.exit(1)
print(f"Coleccion hebillas ID: {hebillas_id}")

for pid in PRODUCT_IDS:
    r = requests.get(f"{REST_BASE}/products/{pid}.json", headers=HEADERS,
                     params={"fields": "id,title"}, timeout=30)
    title = r.json().get("product", {}).get("title", "?")
    r2 = requests.get(f"{REST_BASE}/collects.json", headers=HEADERS,
                      params={"product_id": pid, "collection_id": hebillas_id}, timeout=30)
    if r2.json().get("collects", []):
        print(f"  Ya en hebillas: [{pid}] {title}")
        continue
    if APPLY:
        r3 = requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
                           json={"collect": {"product_id": pid, "collection_id": hebillas_id}},
                           timeout=30)
        print(f"  {'OK' if r3.status_code in (200, 201) else 'ERR'}: [{pid}] {title}")
    else:
        print(f"  [DRY-RUN] agregaria: [{pid}] {title}")

if not APPLY:
    print("\nCorre con --apply para aplicar.")