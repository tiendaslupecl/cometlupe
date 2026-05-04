"""
Rellena Theme settings → Products → Custom colors (color_swatch_hexes) para nombres en español.

Xtra infiere swatches para inglés (Red, Black…). Sin mapeo, «Negro» no coincide y el círculo sale blanco/incorrecto.

Lee los valores de la opción de color del producto por GraphQL y aplica hex conocidos; valores sin mapa usan #888888.

Requiere: read_themes, write_themes

  python tasks/theme_apply_spanish_color_hexes.py
  python tasks/theme_apply_spanish_color_hexes.py --dry-run

Opcional:
  PRODUCT_HANDLE=otro-producto python tasks/theme_apply_spanish_color_hexes.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from shopify_client import API_VERSION, graphql  # noqa: E402

TOKEN = (os.getenv("ADMIN_API_TOKEN") or "").strip()
SHOP = (os.getenv("SHOP_DOMAIN") or "").strip().replace("https://", "").split("/")[0]

DEFAULT_HANDLE = "hilo-2000-yardas-lama-40-2-elige-tu-color-poliester-profesional"

# Nombres exactos como en Admin + hex representativo (hilos / tonos tela)
SPANISH_COLOR_HEX: dict[str, str] = {
    "Negro": "#000000",
    "Blanco": "#FFFFFF",
    "Crudo": "#E8DCC8",
    "Beige Oscuro": "#6B5344",
    "Rosa Palo": "#E8B4BC",
    "Sandia": "#E9546B",
    "Violeta": "#6B52D6",
    "Berenjena": "#5C2849",
    "Rojo": "#C41E3A",
    "Naranjo": "#FF6600",
    "Amarillo": "#FFD700",
    "Terracota": "#C47244",
    "Gris": "#808080",
    "Gris Marengo": "#3D464B",
    "Azul Marino": "#1E3A5F",
    "Celeste": "#87CEEB",
    "Verde Agua": "#66CDAA",
    "Verde Manzana": "#8DB600",
    "Esmeralda": "#50C878",
    "Beige Claro": "#D4C4A8",
    "Rosado Fuerte": "#E91E8C",
    "Turquesa": "#40E0D0",
    "Amarillo Pato": "#B5A642",
    "Gris Claro": "#D3D3D3",
    "Azul": "#2563EB",
    "Burdeo": "#722F37",
    "Fucsia": "#FF1493",
    "Verde Botella": "#006A4E",
    "Damasco": "#FFB347",
    "Café Moro": "#4A3728",
    "Azul Petróleo": "#2F4F4F",
    "Mostaza": "#D4AF37",
    "Verde Turquesa": "#00CED1",
    "Pistacho": "#93C572",
}

QUERY = """
query ($handle: String!) {
  productByHandle(handle: $handle) {
    title
    options {
      name
      values
    }
    variants(first: 100) {
      nodes {
        title
      }
    }
  }
}
"""


def _theme_main_id() -> int:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/themes.json"
    r = requests.get(url, headers={"X-Shopify-Access-Token": TOKEN}, timeout=30)
    r.raise_for_status()
    for t in r.json().get("themes") or []:
        if (t.get("role") or "").lower() == "main":
            return int(t["id"])
    raise SystemExit("[ERROR] Sin tema principal")


def _get_asset(theme_id: int, key: str) -> str:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/themes/{theme_id}/assets.json"
    r = requests.get(
        url,
        headers={"X-Shopify-Access-Token": TOKEN},
        params={"asset[key]": key},
        timeout=45,
    )
    r.raise_for_status()
    return (r.json().get("asset") or {})["value"]


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
        raise SystemExit(f"[ERROR] PUT {key}: {r.status_code} {r.text[:600]}")


def _color_option_values(data: dict) -> list[str]:
    p = data.get("productByHandle")
    if not p:
        raise SystemExit("[ERROR] Producto no encontrado")
    for opt in p.get("options") or []:
        name = (opt.get("name") or "").strip().lower()
        if name in ("color", "colour", "couleur", "farbe"):
            return list(opt.get("values") or [])
    # primera opción tipo lista larga (fallback)
    if p.get("options"):
        return list((p["options"][0] or {}).get("values") or [])
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not TOKEN or not SHOP:
        raise SystemExit("[ERROR] ADMIN_API_TOKEN y SHOP_DOMAIN")

    handle = os.getenv("PRODUCT_HANDLE", "").strip() or DEFAULT_HANDLE
    pdata = graphql(QUERY, {"handle": handle})
    p = pdata["productByHandle"]
    titles = [n["title"] for n in (p.get("variants") or {}).get("nodes") or []]

    values = _color_option_values(pdata)
    print(f"Producto: {p['title']} ({handle})")
    print(f"Variantes: {len(titles)} | Valores opción color: {len(values)}")
    if len(titles) != len(values):
        print(
            "[WARN] Cantidad variantes ≠ valores de opción; revisar duplicados o opciones extra."
        )

    missing_hex = [v for v in values if v not in SPANISH_COLOR_HEX]
    if missing_hex:
        print(f"[WARN] Sin hex predefinido para: {missing_hex} → se usará #888888")

    lines = []
    for v in values:
        hx = SPANISH_COLOR_HEX.get(v, "#888888")
        lines.append(f"{v}: {hx}")
    hex_blob = "\n".join(lines)

    tid = _theme_main_id()
    raw = _get_asset(tid, "config/settings_data.json")
    sd = json.loads(raw)
    cur = sd.setdefault("current", {})
    cur["enable_color_swatches"] = True
    cur["color_swatch_name"] = "Color\nColour"
    cur["color_swatch_hexes"] = hex_blob

    print("\nPrimeras líneas color_swatch_hexes:")
    print("\n".join(lines[:6]) + "\n…")

    if args.dry_run:
        print("(dry-run)")
        return

    _put_asset(
        tid,
        "config/settings_data.json",
        json.dumps(sd, ensure_ascii=False, indent=2),
    )
    print("\n✓ Guardado config/settings_data.json (swatches en español)")


if __name__ == "__main__":
    main()
