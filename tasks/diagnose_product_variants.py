"""Diagnóstico Admin API: availableForSale e inventario por ubicación."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql

DEFAULT_HANDLE = "hilo-2000-yardas-lama-40-2-elige-tu-color-poliester-profesional"

QUERY = """
query ProductVariantDiag($handle: String!) {
  productByHandle(handle: $handle) {
    title
    status
    variants(first: 100) {
      nodes {
        title
        availableForSale
        inventoryPolicy
        inventoryItem {
          tracked
          inventoryLevels(first: 10) {
            nodes {
              quantities(names: ["available"]) {
                name
                quantity
              }
              location {
                name
                fulfillsOnlineOrders
              }
            }
          }
        }
      }
    }
  }
}
"""


def main() -> None:
    handle = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HANDLE
    data = graphql(QUERY, {"handle": handle})
    p = data.get("productByHandle")
    if not p:
        raise SystemExit(f"No existe producto: {handle}")
    print(f"Producto: {p['title']}\nEstado: {p['status']}\n")
    for v in p["variants"]["nodes"]:
        nodes = (
            (v.get("inventoryItem") or {}).get("inventoryLevels") or {}
        ).get("nodes") or []
        parts = []
        for n in nodes:
            qty = next(
                (q["quantity"] for q in n["quantities"] if q["name"] == "available"),
                "?",
            )
            loc = n["location"]["name"]
            fo = n["location"].get("fulfillsOnlineOrders")
            parts.append(f"{loc}: disponible={qty} fulfillsOnline={fo}")
        inv_txt = " | ".join(parts) if parts else "(sin niveles)"
        print(
            f"{(v['title'] or '')[:42]:42} "
            f"sale={v['availableForSale']} "
            f"policy={v['inventoryPolicy']:8} "
            f"{inv_txt}"
        )


if __name__ == "__main__":
    main()
