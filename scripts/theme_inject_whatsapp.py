"""
Inyecta el botón flotante WhatsApp en layout/theme.liquid del tema publicado.
Solo modifica esa línea — no toca nada más del diseño.

Uso:
    python scripts/theme_inject_whatsapp.py --allow-live
    python scripts/theme_inject_whatsapp.py --allow-live --phone 56912345678
"""
import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS  # noqa: E402
import requests as _requests  # noqa: E402

SNIPPETS_DIR = _ROOT / "deliverables" / "lupe-cro-theme" / "snippets"

EXTRA_SNIPPETS = ["icon-whatsapp.liquid"]
EXTRA_ASSETS = ["cro-whatsapp-float.css"]
ASSETS_DIR = _ROOT / "deliverables" / "lupe-cro-theme" / "assets"

INJECT_MARKER = "data-lupe-wa-injected"
INJECT_TEMPLATE = (
    "\n{{% render 'whatsapp-float', phone: '{phone}', brand: shop.name %}} "
    "<!-- {marker} -->"
)


def _get_main_theme() -> tuple[str, str]:
    r = _requests.get(f"{REST_BASE}/themes.json", headers=HEADERS, timeout=30)
    r.raise_for_status()
    for t in r.json().get("themes", []):
        if (t.get("role") or "").lower() == "main":
            return str(t["id"]), t.get("name", "main")
    raise SystemExit("❌ No se encontró tema publicado")


def _get_asset(theme_id: str, key: str) -> str:
    r = _requests.get(
        f"{REST_BASE}/themes/{theme_id}/assets.json",
        headers=HEADERS,
        params={"asset[key]": key},
        timeout=45,
    )
    if r.status_code == 404:
        return ""
    r.raise_for_status()
    return (r.json().get("asset") or {}).get("value", "")


def _put_asset(theme_id: str, key: str, value: str) -> None:
    r = _requests.put(
        f"{REST_BASE}/themes/{theme_id}/assets.json",
        headers=HEADERS,
        json={"asset": {"key": key, "value": value}},
        timeout=60,
    )
    if r.status_code >= 400:
        raise SystemExit(f"❌ PUT {key} HTTP {r.status_code}: {r.text[:400]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-live", action="store_true")
    ap.add_argument("--phone", default="56963855857", help="Número WhatsApp E.164 sin +")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.allow_live and not args.dry_run:
        raise SystemExit("🛑 Usa --allow-live para modificar el tema publicado.")

    tid, tname = _get_main_theme()
    print(f"🧭 Tema: {tname} (id={tid})")

    # 1. Subir snippets de soporte que pueden faltar en Xtra
    for fname in EXTRA_SNIPPETS:
        fp = SNIPPETS_DIR / fname
        if not fp.exists():
            continue
        key = f"snippets/{fname}"
        existing = _get_asset(tid, key)
        if existing:
            print(f"  ↩  {key} ya existe, omitido")
        else:
            if not args.dry_run:
                _put_asset(tid, key, fp.read_text(encoding="utf-8"))
            print(f"  ✅ {key} subido")

    # 2. Subir CSS del botón WhatsApp
    for fname in EXTRA_ASSETS:
        fp = ASSETS_DIR / fname
        if not fp.exists():
            continue
        key = f"assets/{fname}"
        if not args.dry_run:
            _put_asset(tid, key, fp.read_text(encoding="utf-8"))
        print(f"  ✅ {key} subido")

    # 3. Leer layout/theme.liquid
    layout = _get_asset(tid, "layout/theme.liquid")
    if not layout:
        raise SystemExit("❌ No se encontró layout/theme.liquid en el tema")

    # 4. Verificar si ya está inyectado
    if INJECT_MARKER in layout:
        print("ℹ️  El botón WhatsApp ya estaba inyectado anteriormente.")
        return

    # 5. Inyectar antes de </body>
    if "</body>" not in layout:
        raise SystemExit("❌ No se encontró </body> en layout/theme.liquid")

    inject_code = INJECT_TEMPLATE.format(phone=args.phone, marker=INJECT_MARKER)
    new_layout = layout.replace("</body>", inject_code + "\n</body>")

    if args.dry_run:
        print("(dry-run) Se inyectaría esto antes de </body>:")
        print(inject_code)
        return

    _put_asset(tid, "layout/theme.liquid", new_layout)
    print(f"\n✅ Botón WhatsApp ({args.phone}) inyectado en layout/theme.liquid")
    print("   Abre tiendaslupe.cl en ventana privada — verás el botón verde flotante.")


if __name__ == "__main__":
    main()
