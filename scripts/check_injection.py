"""Verifica si los snippets CRO están inyectados en main-product-info.liquid"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

r = requests.get(f"{REST_BASE}/themes.json", headers=HEADERS, timeout=30)
main = next(t for t in r.json()["themes"] if t.get("role") == "main")
tid = str(main["id"])
print(f"Tema: {main['name']} (id={tid})")

r2 = requests.get(
    f"{REST_BASE}/themes/{tid}/assets.json",
    headers=HEADERS,
    params={"asset[key]": "snippets/main-product-info.liquid"},
    timeout=45,
)
content = r2.json().get("asset", {}).get("value", "")
print(f"Tamaño: {len(content)} chars")

markers = [
    "render 'lupe-pdp-trust'",
    "render 'quantity-breaks'",
    "render 'upsell-inline'",
]
for m in markers:
    found = m in content
    print(f"  {'✅' if found else '❌'} {m}")
