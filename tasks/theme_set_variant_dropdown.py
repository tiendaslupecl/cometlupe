"""
Añade o corrige el bloque «Variant selection» (Xtra) en templates/product.json para
mostrar un desplegable con los nombres de color/opción.

El tema Xtra usa el bloque variant_selection con selection_type = dropdown | buttons.
Si el bloque falta en la plantilla (caso Tiendas Lupe), solo se ven miniaturas en la galería.

Requiere scopes Admin API: read_themes y write_themes.

  python tasks/theme_set_variant_dropdown.py
  python tasks/theme_set_variant_dropdown.py --dry-run

Opcional — desactivar swatches globales (evita duplicar UI de color en algunos layouts):
  python tasks/theme_set_variant_dropdown.py --disable-color-swatches
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from shopify_client import API_VERSION  # noqa: E402

TOKEN = (os.getenv("ADMIN_API_TOKEN") or "").strip()
SHOP = (os.getenv("SHOP_DOMAIN") or "").strip().replace("https://", "").split("/")[0]


def _main_theme_id() -> tuple[int, str]:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/themes.json"
    r = requests.get(url, headers={"X-Shopify-Access-Token": TOKEN}, timeout=30)
    r.raise_for_status()
    for t in r.json().get("themes") or []:
        if (t.get("role") or "").lower() == "main":
            return int(t["id"]), t.get("name") or "main"
    raise SystemExit("[ERROR] No hay tema principal (role=main)")


def _get_asset(theme_id: int, key: str) -> str | None:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/themes/{theme_id}/assets.json"
    r = requests.get(
        url,
        headers={"X-Shopify-Access-Token": TOKEN},
        params={"asset[key]": key},
        timeout=45,
    )
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return (r.json().get("asset") or {}).get("value")


def _put_asset(theme_id: int, key: str, value: str) -> None:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/themes/{theme_id}/assets.json"
    r = requests.put(
        url,
        headers={
            "X-Shopify-Access-Token": TOKEN,
            "Content-Type": "application/json",
        },
        json={"asset": {"key": key, "value": value}},
        timeout=90,
    )
    if r.status_code >= 400:
        raise SystemExit(
            f"[ERROR] PUT {key} HTTP {r.status_code}: {r.text[:800]}\n"
            "¿Tiene el token el scope write_themes?"
        )


def _find_main_product_section(data: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    sections = data.get("sections")
    if not isinstance(sections, dict):
        return None
    for sid, sec in sections.items():
        if isinstance(sec, dict) and sec.get("type") in ("main-product", "main-product-cro"):
            return sid, sec
    return None


VARIANT_SETTINGS_DROPDOWN: dict[str, Any] = {
    "selection_type": "dropdown",
    "options": False,
    "show_variant_images": False,
    "show_unavailable_variants": True,
    "show_single_options": False,
    "enable_selling_plans": True,
}


def _patch_main_product(section: dict[str, Any]) -> tuple[bool, str]:
    """Returns (changed, message)."""
    blocks = section.setdefault("blocks", {})
    block_order = section.setdefault("block_order", [])
    if not isinstance(blocks, dict) or not isinstance(block_order, list):
        return False, "Sección main-product sin blocks/block_order válidos"

    # ¿Ya existe variant_selection?
    existing_id: str | None = None
    for bid, b in blocks.items():
        if isinstance(b, dict) and b.get("type") == "variant_selection":
            existing_id = bid
            break

    if existing_id:
        st = blocks[existing_id].setdefault("settings", {})
        changed = False
        for k, v in VARIANT_SETTINGS_DROPDOWN.items():
            if st.get(k) != v:
                st[k] = v
                changed = True
        return changed, f"Bloque variant_selection ({existing_id[:8]}…) actualizado"

    new_id = str(uuid.uuid4())
    blocks[new_id] = {
        "type": "variant_selection",
        "settings": dict(VARIANT_SETTINGS_DROPDOWN),
    }
    insert_at = 0
    if "short_description" in block_order:
        insert_at = block_order.index("short_description") + 1
    elif "title" in block_order:
        insert_at = block_order.index("title") + 1
    block_order.insert(insert_at, new_id)
    return True, f"Añadido variant_selection ({new_id}) en posición {insert_at}"


def _patch_disable_swatches(settings_data: dict[str, Any]) -> tuple[bool, str]:
    cur = settings_data.get("current")
    if not isinstance(cur, dict):
        return False, "settings_data sin clave current"
    if cur.get("enable_color_swatches") is False:
        return False, "enable_color_swatches ya estaba desactivado"
    cur["enable_color_swatches"] = False
    return True, "current.enable_color_swatches → false"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--disable-color-swatches",
        action="store_true",
        help="Desactiva Theme settings → Products → Enable color swatches (solo bloque current)",
    )
    args = ap.parse_args()

    if not TOKEN or not SHOP:
        raise SystemExit("[ERROR] ADMIN_API_TOKEN y SHOP_DOMAIN en .env")

    tid, tname = _main_theme_id()
    print(f"Tema: {tname} (id={tid})")

    raw = _get_asset(tid, "templates/product.json")
    if raw is None:
        raise SystemExit("[ERROR] Falta templates/product.json")

    data = json.loads(raw)
    found = _find_main_product_section(data)
    if not found:
        raise SystemExit("[ERROR] No hay sección main-product en templates/product.json")

    _, section = found
    changed, msg = _patch_main_product(section)
    print(msg)

    sd_changed = False
    sd_msg = ""
    if args.disable_color_swatches:
        raw_sd = _get_asset(tid, "config/settings_data.json")
        if not raw_sd:
            print("[WARN] No se encontró config/settings_data.json")
        else:
            sd = json.loads(raw_sd)
            sd_changed, sd_msg = _patch_disable_swatches(sd)
            print(sd_msg)

    if args.dry_run:
        print("(dry-run: no se guardó nada en Shopify)")
        return

    if changed:
        _put_asset(tid, "templates/product.json", json.dumps(data, ensure_ascii=False, indent=2))
        print("✓ Guardado templates/product.json")

    if args.disable_color_swatches and sd_changed:
        _put_asset(
            tid,
            "config/settings_data.json",
            json.dumps(sd, ensure_ascii=False, indent=2),
        )
        print("✓ Guardado config/settings_data.json")

    if not changed and not (args.disable_color_swatches and sd_changed):
        print("Nada que guardar.")
    else:
        print("\nAbre la tienda en una ventana privada y revisa la página del producto.")


if __name__ == "__main__":
    main()
