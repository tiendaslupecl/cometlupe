"""
Marca todas las variantes de un producto como comprables aunque el inventario sea 0:
inventoryPolicy = CONTINUE ("Continuar vendiendo cuando no hay stock").

Uso:
  python tasks/make_variants_available.py [handle-del-producto]

  O variable de entorno PRODUCT_HANDLE (por defecto el hilo 2000 yardas).

Opcional — además poner stock numérico en la ubicación principal del comercio:
  VARIANT_DEFAULT_QTY=50 python tasks/make_variants_available.py

Scopes Admin API: read_products, write_products; si usas VARIANT_DEFAULT_QTY también write_inventory.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql, rest

DEFAULT_HANDLE = "hilo-2000-yardas-lama-40-2-elige-tu-color-poliester-profesional"

PRODUCT_VARIANTS_PAGE = """
query ProductVariantsPage($handle: String!, $cursor: String) {
  productByHandle(handle: $handle) {
    id
    title
    variants(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        sku
        inventoryPolicy
        inventoryItem { id }
      }
    }
  }
}
"""

LOCATIONS_QUERY = """
query LocationsFirst {
  locations(first: 10, query: "active:true") {
    nodes {
      id
      name
      isActive
      fulfillsOnlineOrders
    }
  }
}
"""

INVENTORY_SET_QUANTITIES = """
mutation InvSetQty($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    userErrors { field message }
    inventoryAdjustmentGroup {
      reason
      changes {
        name
        delta
      }
    }
  }
}
"""


def gid_numeric(gid: str) -> str:
    return gid.split("/")[-1]


def gid_int(gid: str) -> int:
    return int(gid.split("/")[-1])


def fetch_all_variants(handle: str) -> tuple[str | None, str | None, list[dict]]:
    variants: list[dict] = []
    cursor: str | None = None
    product_id: str | None = None
    title: str | None = None
    while True:
        data = graphql(
            PRODUCT_VARIANTS_PAGE,
            {"handle": handle, "cursor": cursor},
        )
        p = data.get("productByHandle")
        if not p:
            return None, None, []
        product_id = p["id"]
        title = p.get("title")
        conn = p["variants"]
        for n in conn["nodes"]:
            variants.append(n)
        if not conn["pageInfo"]["hasNextPage"]:
            break
        cursor = conn["pageInfo"]["endCursor"]
        time.sleep(0.15)
    return product_id, title, variants


def pick_fulfillment_location_id() -> str | None:
    data = graphql(LOCATIONS_QUERY, {})
    nodes = (data.get("locations") or {}).get("nodes") or []
    for node in nodes:
        if node.get("fulfillsOnlineOrders"):
            return node["id"]
    return nodes[0]["id"] if nodes else None


def main() -> None:
    handle = (
        (sys.argv[1] if len(sys.argv) > 1 else None)
        or os.getenv("PRODUCT_HANDLE", "").strip()
        or DEFAULT_HANDLE
    )
    default_qty_raw = os.getenv("VARIANT_DEFAULT_QTY", "").strip()
    default_qty: int | None = None
    if default_qty_raw:
        try:
            default_qty = int(default_qty_raw)
        except ValueError:
            raise SystemExit(
                f"[ERROR] VARIANT_DEFAULT_QTY debe ser entero, recibí: {default_qty_raw!r}"
            )
        if default_qty < 0:
            raise SystemExit("[ERROR] VARIANT_DEFAULT_QTY no puede ser negativo")

    product_id, title, variants = fetch_all_variants(handle)
    if not product_id:
        raise SystemExit(f"[ERROR] No existe producto con handle: {handle}")
    if not variants:
        raise SystemExit(f"[ERROR] El producto no tiene variantes: {handle}")

    print(f"Producto: {title} ({gid_numeric(product_id)}) — {len(variants)} variantes")

    updated = 0
    skipped = 0
    errors = 0

    for v in variants:
        vid = v["id"]
        policy = (v.get("inventoryPolicy") or "").upper()
        label = v.get("title") or vid
        if policy == "CONTINUE":
            print(f"  ○ Ya CONTINUE: {label}")
            skipped += 1
            continue
        pid = gid_int(product_id)
        vid_num = gid_int(vid)
        try:
            rest(
                "PUT",
                f"/products/{pid}/variants/{vid_num}.json",
                {"variant": {"id": vid_num, "inventory_policy": "continue"}},
            )
            print(f"  ✓ CONTINUE (REST): {label}")
            updated += 1
        except Exception as e:
            print(f"  ✗ {label}: {e}")
            errors += 1
        time.sleep(0.12)

    if default_qty is not None:
        loc_id = pick_fulfillment_location_id()
        if not loc_id:
            raise SystemExit("[ERROR] No hay ubicaciones activas para asignar inventario.")
        print(f"\nAsignando cantidad {default_qty} en ubicación {gid_numeric(loc_id)} …")
        quantities = []
        for v in variants:
            inv = v.get("inventoryItem") or {}
            iid = inv.get("id")
            if not iid:
                print(f"  ⚠ Sin inventoryItem: {v.get('title')}")
                continue
            quantities.append(
                {
                    "inventoryItemId": iid,
                    "locationId": loc_id,
                    "quantity": default_qty,
                }
            )
        if quantities:
            data = graphql(
                INVENTORY_SET_QUANTITIES,
                {
                    "input": {
                        "name": "available",
                        "reason": "correction",
                        "quantities": quantities,
                        "ignoreCompareQuantity": True,
                    }
                },
            )
            inv = data.get("inventorySetQuantities") or {}
            ue = inv.get("userErrors") or []
            if ue:
                print(f"[ERROR] inventorySetQuantities: {ue}")
                errors += len(ue)
            else:
                print(f"  ✓ Inventario actualizado para {len(quantities)} ítems.")

    print(
        f"\nListo: actualizadas={updated}, ya_ok={skipped}, errores={errors}"
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
