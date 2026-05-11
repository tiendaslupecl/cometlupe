"""
Sube SOLO los snippets CRO al tema publicado, sin tocar layout, sections,
config/settings_data.json ni templates. Seguro para temas Xtra existentes.

Uso:
    python scripts/theme_push_snippets_only.py --allow-live
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS  # noqa: E402
import requests as _requests  # noqa: E402

THEME_DIR = _ROOT / "deliverables" / "lupe-cro-theme"

# Solo estos snippets — no layout, no sections, no config, no templates
SAFE_SNIPPETS = {
    "snippets/whatsapp-float.liquid",
    "snippets/upsell-inline.liquid",
    "snippets/quantity-breaks.liquid",
    "snippets/frequently-bought.liquid",
    "snippets/lupe-pdp-trust.liquid",
    "snippets/product-deliverytime.liquid",
    "snippets/bundle-card.liquid",
}


def _validate_target_theme(theme_id: str, allow_live: bool) -> None:
    url = f"{REST_BASE}/themes/{theme_id}.json"
    r = _requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"❌ No se pudo validar theme {theme_id} (HTTP {r.status_code})")
    theme = r.json().get("theme", {})
    role = (theme.get("role") or "").strip().lower()
    name = (theme.get("name") or "").strip()
    print(f"🧭 Target theme: {name} | role={role} | id={theme_id}")
    if role == "main" and not allow_live:
        raise SystemExit("🛑 Bloqueado: tema publicado. Usa --allow-live para confirmar.")


def push_snippets(theme_id: str, allow_live: bool = False) -> None:
    _validate_target_theme(theme_id, allow_live=allow_live)
    total = errors = 0
    print(f"\n📦 Subiendo snippets CRO al tema {theme_id}...\n")
    for key in sorted(SAFE_SNIPPETS):
        fp = THEME_DIR / key
        if not fp.exists():
            print(f"  ⚠️  {key} — no encontrado en deliverables, omitido")
            continue
        value = fp.read_text(encoding="utf-8")
        url = f"{REST_BASE}/themes/{theme_id}/assets.json"
        r = _requests.put(url, headers=HEADERS, json={"asset": {"key": key, "value": value}}, timeout=30)
        if r.status_code in (200, 201):
            print(f"  ✅ {key}")
            total += 1
        else:
            print(f"  ❌ {key} — HTTP {r.status_code}: {r.text[:200]}")
            errors += 1

    print()
    if errors:
        print(f"⚠️  Terminado con {errors} error(s) / {total} OK.")
    else:
        print(f"✅ {total} snippets CRO subidos al tema {theme_id} sin tocar el diseño.")


if __name__ == "__main__":
    allow_live = "--allow-live" in sys.argv
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        # Auto-detecta el tema publicado
        r = _requests.get(f"{REST_BASE}/themes.json", headers=HEADERS, timeout=30)
        r.raise_for_status()
        main_theme = next((t for t in r.json().get("themes", []) if t.get("role") == "main"), None)
        if not main_theme:
            raise SystemExit("❌ No se encontró tema publicado")
        theme_id_arg = str(main_theme["id"])
    else:
        theme_id_arg = sys.argv[1]
    push_snippets(theme_id_arg, allow_live=allow_live)
