"""
Sube los archivos del tema CRO al tema live de Shopify vía Admin API (REST Asset).

Uso:
    python scripts/theme_push_live_id.py <THEME_ID>

Ejemplo:
    python scripts/theme_push_live_id.py 150148677783
"""
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS  # noqa: E402

import requests as _requests  # noqa: E402

THEME_DIR = _ROOT / "deliverables" / "lupe-cro-theme"

ASSET_DIRS = [
    "layout",
    "sections",
    "snippets",
    "templates",
    "config",
    "assets",
    "locales",
]

EXTENSIONS = {".liquid", ".json", ".jsonl", ".css", ".js", ".txt"}


def _collect_assets() -> list[tuple[str, str]]:
    """Return list of (shopify_key, file_content) tuples."""
    assets: list[tuple[str, str]] = []
    for dirname in ASSET_DIRS:
        dirpath = THEME_DIR / dirname
        if not dirpath.is_dir():
            continue
        for fp in sorted(dirpath.iterdir()):
            if fp.is_file() and fp.suffix in EXTENSIONS:
                key = f"{dirname}/{fp.name}"
                content = fp.read_text(encoding="utf-8")
                assets.append((key, content))
    return assets


def push_theme(theme_id: str) -> None:
    total = 0
    errors = 0
    assets = _collect_assets()
    print(f"📦 {len(assets)} archivos encontrados en {THEME_DIR}")
    print(f"🎯 Theme ID: {theme_id}")
    print()

    for key, value in assets:
        url = f"{REST_BASE}/themes/{theme_id}/assets.json"
        payload = {"asset": {"key": key, "value": value}}
        try:
            r = _requests.put(url, headers=HEADERS, json=payload, timeout=30)
            if r.status_code in (200, 201):
                print(f"  ✅ {key}")
                total += 1
            elif r.status_code == 422:
                body = r.json() if r.text else {}
                msg = body.get("errors", r.text)
                print(f"  ⚠️  {key} — 422: {msg}")
                errors += 1
            else:
                print(f"  ❌ {key} — HTTP {r.status_code}: {r.text[:200]}")
                errors += 1
        except _requests.exceptions.RequestException as exc:
            print(f"  ❌ {key} — {exc}")
            errors += 1

    print()
    if errors:
        print(f"⚠️  Theme upload finished with {errors} error(s) / {total} OK.")
    else:
        print(f"✅ Theme upload complete — {total} assets pushed to theme {theme_id}.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/theme_push_live_id.py <THEME_ID>")
        sys.exit(1)
    push_theme(sys.argv[1])
