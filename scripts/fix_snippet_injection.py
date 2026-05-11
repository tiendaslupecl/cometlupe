"""
Mueve los snippets CRO al lugar correcto en snippets/main-product-info.liquid
"""
import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
t = os.getenv("ADMIN_API_TOKEN")
s = os.getenv("SHOP_DOMAIN")

r = requests.get(f"https://{s}/admin/api/2025-01/themes.json", headers={"X-Shopify-Access-Token": t})
tid = next(x["id"] for x in r.json()["themes"] if x["role"] == "main")

r2 = requests.get(
    f"https://{s}/admin/api/2025-01/themes/{tid}/assets.json",
    headers={"X-Shopify-Access-Token": t},
    params={"asset[key]": "snippets/main-product-info.liquid"},
)
content = r2.json()["asset"]["value"]

INJECT = (
    "\n  {%- render 'lupe-pdp-trust' -%}"
    "\n  {%- render 'quantity-breaks', product: product -%}"
    "\n  {%- render 'upsell-inline', host: product -%}"
)

# Quitar inyección incorrecta si existe
content = content.replace(INJECT, "")

# Inyectar justo antes del </div> final (último del archivo)
last_div = content.rfind("\n</div>")
if last_div == -1:
    raise SystemExit("No se encontró </div> al final del archivo")

content = content[:last_div] + INJECT + content[last_div:]

r3 = requests.put(
    f"https://{s}/admin/api/2025-01/themes/{tid}/assets.json",
    headers={"X-Shopify-Access-Token": t, "Content-Type": "application/json"},
    json={"asset": {"key": "snippets/main-product-info.liquid", "value": content}},
)
print("OK" if r3.status_code in (200, 201) else f"Error {r3.status_code}: {r3.text[:300]}")
