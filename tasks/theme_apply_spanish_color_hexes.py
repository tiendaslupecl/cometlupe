"""
Rellena Theme settings → Products → Custom colors (color_swatch_hexes) para nombres en español.

Xtra infiere swatches para inglés (Red, Black…). Sin mapeo, «Negro» no coincide y el círculo sale blanco/incorrecto.

Lee los valores de la opción «Color» de uno o más productos por GraphQL, **fusiona**
los nombres (sin perder los del hilo 2000 al añadir el 5000) y escribe `color_swatch_hexes`.
Hex conocidos en SPANISH_COLOR_HEX; el resto reusa hex ya guardado en el tema o #888888.

Requiere: read_themes, write_themes

  python tasks/theme_apply_spanish_color_hexes.py
  python tasks/theme_apply_spanish_color_hexes.py --dry-run

  python tasks/theme_apply_spanish_color_hexes.py --handles handle-a handle-b

Por defecto fusiona hilos Lama: 2000 yardas, 5000 yardas y Overlock 150g.
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

DEFAULT_MERGE_HANDLES = [
    "hilo-2000-yardas-lama-40-2-elige-tu-color-poliester-profesional",
    "hilo-de-costura-profesional-lama-5000-yardas-elige-tu-color-29-colores",
    "hilo-overlock-150g-lama",
]

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
    # Hilo 5000 yardas (y otros catálogos)
    "Morado": "#6B2D5C",
    "Palo Rosa Claro": "#E8B4BC",
    "Verde Esmeralda": "#50C878",
    "Azul Francia": "#1E6AE8",
    "Verde": "#228B22",
    "Lila": "#C8A2C8",
    "Naranja": "#FF8C00",
    "Rosa Pastel": "#FFD1DC",
    "Cafe": "#5D4037",
    "Beige": "#F5F5DC",
    # Hilo Overlock 150g (y similares)
    "Verde Petróleo": "#1B4D4D",
    "Calipso": "#00CED1",
    "Morado Profesional": "#4B0082",
    "Palo Rosa": "#E8A0A8",
    "Amarillo Oro": "#E6C200",
    "Gris Oscuro": "#4A4A4A",
    "Beige Profesional": "#B8A88E",
    "Arena": "#C2B280",
    "Vela": "#F5F0E6",
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


def _parse_hex_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (blob or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, _, rest = line.partition(":")
        name = name.strip()
        hx = rest.strip().split()[0] if rest.strip() else ""
        if name and hx.startswith("#"):
            out[name] = hx
    return out


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
    ap.add_argument(
        "--handles",
        nargs="*",
        default=None,
        metavar="HANDLE",
        help="Product handles a fusionar (default: hilo 2000 + 5000 yardas)",
    )
    args = ap.parse_args()

    if not TOKEN or not SHOP:
        raise SystemExit("[ERROR] ADMIN_API_TOKEN y SHOP_DOMAIN")

    handles = args.handles
    if handles is None:
        env_h = os.getenv("PRODUCT_HANDLE", "").strip()
        handles = [env_h] if env_h else list(DEFAULT_MERGE_HANDLES)

    tid = _theme_main_id()
    raw = _get_asset(tid, "config/settings_data.json")
    sd = json.loads(raw)
    cur = sd.setdefault("current", {})
    existing_hex = _parse_hex_blob(cur.get("color_swatch_hexes") or "")

    union: list[str] = []
    for handle in handles:
        pdata = graphql(QUERY, {"handle": handle})
        p = pdata["productByHandle"]
        if not p:
            raise SystemExit(f"[ERROR] Producto no encontrado: {handle}")
        titles = [n["title"] for n in (p.get("variants") or {}).get("nodes") or []]
        values = _color_option_values(pdata)
        print(f"— {p['title']} ({handle})")
        print(f"  Variantes: {len(titles)} | valores Color: {len(values)}")
        if len(titles) != len(values):
            print("  [WARN] variantes ≠ valores de opción")
        for v in values:
            if v not in union:
                union.append(v)

    missing_hex = [v for v in union if v not in SPANISH_COLOR_HEX and v not in existing_hex]
    if missing_hex:
        print(f"[WARN] Sin hex predefinido ni en tema para: {missing_hex} → #888888")

    lines = []
    for v in union:
        hx = SPANISH_COLOR_HEX.get(v) or existing_hex.get(v) or "#888888"
        lines.append(f"{v}: {hx}")
    hex_blob = "\n".join(lines)

    cur["enable_color_swatches"] = True
    cur["color_swatch_name"] = "Color\nColour"
    cur["color_swatch_hexes"] = hex_blob

    print(f"\nTotal colores únicos en tema: {len(union)}")
    print("Primeras líneas:")
    print("\n".join(lines[:8]) + "\n…")

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
