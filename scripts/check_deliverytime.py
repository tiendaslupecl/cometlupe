"""Muestra el contenido actual de product-deliverytime.liquid en el tema live."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS
import requests

r = requests.get(f"{REST_BASE}/themes.json", headers=HEADERS, timeout=30)
r.raise_for_status()
main = next(t for t in r.json()["themes"] if t.get("role") == "main")
tid = str(main["id"])
print(f"Theme: {main['name']} (id={tid})")

r2 = requests.get(
    f"{REST_BASE}/themes/{tid}/assets.json",
    headers=HEADERS,
    params={"asset[key]": "snippets/product-deliverytime.liquid"},
    timeout=30,
)
if r2.status_code == 404:
    print("❌ Snippet no existe en el tema")
else:
    val = r2.json().get("asset", {}).get("value", "")
    print(f"--- CONTENIDO ({len(val)} chars) ---")
    print(repr(val))
