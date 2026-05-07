"""
Busca productos con tracking de inventario mixto (algunas variantes tracked, otras no).

Uso:
    python scripts/find_mixed_inventory_product.py

Requiere .env con ADMIN_API_TOKEN y SHOP_DOMAIN.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import graphql  # noqa: E402

QUERY = """
query products($cursor: String) {
  products(first: 50, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      handle
      totalVariants
      variants(first: 100) {
        nodes {
          id
          title
          inventoryPolicy
          inventoryManagement
          inventoryQuantity
        }
      }
    }
  }
}
"""


def find_mixed() -> list[dict]:
    mixed: list[dict] = []
    cursor = None
    page = 0

    while True:
        page += 1
        data = graphql(QUERY, {"cursor": cursor})
        products = data["products"]["nodes"]
        pi = data["products"]["pageInfo"]

        for p in products:
            variants = p["variants"]["nodes"]
            mgmt_values = {v.get("inventoryManagement") for v in variants}
            if len(mgmt_values) > 1:
                tracked = [v for v in variants if v.get("inventoryManagement") == "shopify"]
                untracked = [v for v in variants if v.get("inventoryManagement") != "shopify"]
                mixed.append({
                    "id": p["id"],
                    "title": p["title"],
                    "handle": p["handle"],
                    "total_variants": p["totalVariants"],
                    "tracked": len(tracked),
                    "untracked": len(untracked),
                })

        print(f"  Página {page}: {len(products)} productos revisados, {len(mixed)} mixtos hasta ahora")

        if not pi["hasNextPage"]:
            break
        cursor = pi["endCursor"]

    return mixed


def main() -> None:
    print("🔍 Buscando productos con inventario mixto...\n")
    results = find_mixed()

    if not results:
        print("\n✅ No se encontraron productos con inventario mixto.")
        return

    print(f"\n⚠️  {len(results)} producto(s) con inventario mixto:\n")
    print(f"{'Producto':<50} {'Variantes':>10} {'Tracked':>8} {'Untracked':>10}")
    print("-" * 80)
    for r in results:
        print(f"{r['title'][:49]:<50} {r['total_variants']:>10} {r['tracked']:>8} {r['untracked']:>10}")
    print()
    print("Para corregir: Shopify Admin → Productos → [producto] → variantes → activar tracking.")


if __name__ == "__main__":
    main()
