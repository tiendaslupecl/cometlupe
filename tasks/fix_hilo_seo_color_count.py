"""Unifica el texto «36 colores/tonos» con las 34 variantes reales del producto."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from shopify_client import graphql  # noqa: E402

HANDLE = "hilo-2000-yardas-lama-40-2-elige-tu-color-poliester-profesional"

GET = """
query ($handle: String!) {
  productByHandle(handle: $handle) {
    id
    descriptionHtml
    seo {
      title
      description
    }
    variants(first: 5) {
      nodes {
        id
      }
    }
  }
}
"""

UPDATE = """
mutation ($input: ProductInput!) {
  productUpdate(input: $input) {
    product {
      id
      descriptionHtml
      seo {
        title
        description
      }
    }
    userErrors {
      field
      message
    }
  }
}
"""


def main() -> None:
    data = graphql(GET, {"handle": HANDLE})
    p = data["productByHandle"]
    if not p:
        raise SystemExit("Producto no encontrado")
    vid_count = graphql(
        """
        query ($h: String!) {
          productByHandle(handle: $h) {
            variants(first: 100) {
              nodes {
                id
              }
            }
          }
        }
        """,
        {"h": HANDLE},
    )
    n = len(vid_count["productByHandle"]["variants"]["nodes"])
    desc = p.get("descriptionHtml") or ""
    seo_title = (p.get("seo") or {}).get("title") or ""
    seo_desc = (p.get("seo") or {}).get("description") or ""

    old_desc = desc
    desc = desc.replace("36 tonos", "34 tonos")
    desc = desc.replace("36 Colores", "34 colores")
    desc = desc.replace("36 colores", "34 colores")

    new_seo_title = seo_title.replace("36 Colores", "34 colores").replace(
        "36 colores", "34 colores"
    )
    new_seo_desc = seo_desc.replace("36 tonos", "34 tonos").replace(
        "36 colores", "34 colores"
    )

    if desc == old_desc and new_seo_title == seo_title and new_seo_desc == seo_desc:
        print("Nada que reemplazar (texto ya actualizado o sin coincidencias).")
        return

    inp: dict = {"id": p["id"], "descriptionHtml": desc}
    if new_seo_title != seo_title or new_seo_desc != seo_desc:
        inp["seo"] = {}
        if new_seo_title != seo_title:
            inp["seo"]["title"] = new_seo_title
        if new_seo_desc != seo_desc:
            inp["seo"]["description"] = new_seo_desc

    out = graphql(UPDATE, {"input": inp})
    errs = (out.get("productUpdate") or {}).get("userErrors") or []
    if errs:
        raise SystemExit(f"userErrors: {errs}")
    print(f"OK — variantes en catálogo: {n}. Descripción/SEO ajustados de 36 → 34 donde aplicaba.")


if __name__ == "__main__":
    main()
