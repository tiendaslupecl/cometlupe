"""One-off: asignar los ultimos 3 productos sueltos."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests, time

ASSIGNMENTS = [
    (9425095622807, "cintas-algodon"),
    (9425112858775, "cintas-algodon"),
    (9183323685015, "materiales-para-manualidades"),
]

# Get collection ids
custom = requests.get(f"{REST_BASE}/custom_collections.json", headers=HEADERS,
                     params={"limit": 250, "fields":"id,handle"}, timeout=30).json()["custom_collections"]
smart  = requests.get(f"{REST_BASE}/smart_collections.json", headers=HEADERS,
                     params={"limit": 250, "fields":"id,handle"}, timeout=30).json()["smart_collections"]
custom_by_handle = {c["handle"]: c["id"] for c in custom}
smart_by_handle  = {c["handle"]: c["id"] for c in smart}

for pid, handle in ASSIGNMENTS:
    if handle in custom_by_handle:
        col_id = custom_by_handle[handle]
        r = requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
                          json={"collect": {"product_id": pid, "collection_id": col_id}}, timeout=30)
        print(f"  [{pid}] -> {handle} (custom): HTTP {r.status_code}")
    elif handle in smart_by_handle:
        print(f"  [{pid}] -> {handle} (SMART, no se puede asignar manual)")
    else:
        print(f"  [{pid}] -> {handle} NO ENCONTRADA")
    time.sleep(0.2)
