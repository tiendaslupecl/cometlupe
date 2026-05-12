"""Revisa los menus de navegacion y detecta links rotos a colecciones eliminadas."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

# Obtener todos los menus via GraphQL
GQL = """
{
  menus(first: 20) {
    edges {
      node {
        handle
        title
        items {
          title
          url
          items {
            title
            url
          }
        }
      }
    }
  }
}
"""

GRAPHQL_URL = REST_BASE.replace("/admin/api/2024-01", "/api/2024-01/graphql.json").replace(
    "admin/api", "admin/api"
)
# Use storefront? No, use admin GraphQL
store = REST_BASE.split("/admin/")[0]
url = f"{store}/admin/api/2024-01/graphql.json"

r = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"},
                  json={"query": GQL}, timeout=30)

if r.status_code != 200:
    print(f"GraphQL error {r.status_code}: {r.text[:200]}")
    # Fallback: REST menus via Online Store navigation (not available in REST)
    # Try with online store API
    sys.exit(1)

data = r.json()
if "errors" in data:
    print("Errors:", data["errors"])
    sys.exit(1)

menus = data.get("data", {}).get("menus", {}).get("edges", [])

# Obtener handles de colecciones existentes
all_cols = {}
for kind in ("custom_collections", "smart_collections"):
    cr = requests.get(f"{REST_BASE}/{kind}.json", headers=HEADERS,
                      params={"limit": 250, "fields": "id,handle,title"}, timeout=30)
    for c in cr.json().get(kind, []):
        all_cols[c["handle"]] = c["title"]

print(f"Colecciones existentes: {len(all_cols)}")
print()

broken = []
for edge in menus:
    menu = edge["node"]
    print(f"MENU: {menu['title']} ({menu['handle']})")
    for item in menu["items"]:
        url_path = item["url"]
        # Check if it's a collection URL
        if "/collections/" in url_path:
            handle = url_path.split("/collections/")[-1].strip("/")
            exists = handle in all_cols
            status = "OK" if exists else "ROTO"
            if not exists:
                broken.append((menu["handle"], item["title"], handle))
            print(f"  [{status}] {item['title']} → {handle}")
        else:
            print(f"  [--] {item['title']} → {url_path}")
        # Subitems
        for sub in item.get("items", []):
            sub_url = sub["url"]
            if "/collections/" in sub_url:
                handle = sub_url.split("/collections/")[-1].strip("/")
                exists = handle in all_cols
                status = "OK" if exists else "ROTO"
                if not exists:
                    broken.append((menu["handle"], sub["title"], handle))
                print(f"    [{status}] {sub['title']} → {handle}")
            else:
                print(f"    [--] {sub['title']} → {sub_url}")
    print()

if broken:
    print(f"\n{'='*50}")
    print(f"LINKS ROTOS ({len(broken)}):")
    for menu_h, title, handle in broken:
        print(f"  Menu '{menu_h}': '{title}' → /collections/{handle} (NO EXISTE)")
else:
    print("No se encontraron links rotos.")
