# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a Python CLI tool ("Tiendas Lupe") that automates Shopify store navigation restructuring via the Shopify Admin API (GraphQL + REST). It creates collections, rebuilds menus, sets up 301 redirects, and generates a manual filter checklist. See `README.md` for the full user-facing guide (in Spanish).

### Running the application

- **Main orchestrator:** `python3 main.py` — runs all 4 tasks (collections, menu, redirects, filter report).
- **Menu-only:** `python3 solo_menu.py` — re-runs only the menu rebuild.
- **Utility tasks** are in `tasks/` (e.g., `diagnose_product_variants.py`, `fix_hilo_seo_color_count.py`).

### Credentials

A `.env` file is required with `SHOP_DOMAIN` and `ADMIN_API_TOKEN` (starts with `shpat_`). Copy `.env.example` to `.env` and fill in real values. The `shopify_client.py` module calls `SystemExit` at import time if these are missing or still set to the placeholder value.

The Shopify token requires these API scopes: `read_products`, `write_products`, `read_publications`, `write_publications`, `read_content`, `write_content`, `read_themes`.

### Linting

Run `flake8 --max-line-length=120 --exclude=deliverables *.py tasks/*.py`. Pre-existing style warnings (E402 for intentional import-after-path-setup, E501 for long config strings, W293 whitespace) are known and non-blocking.

### Testing

There are no automated tests in this repo. The only way to verify end-to-end functionality is with a real Shopify store and valid API token. The `tasks/task4_filters_report.py` module can be tested standalone without credentials (it generates a static report).

### Gotchas

- `shopify_client.py` raises `SystemExit` at **module import time** if `.env` is missing or credentials are placeholder. Any module that imports from `shopify_client` will trigger this check. To test code that imports `shopify_client`, a `.env` with a valid-format `shpat_*` token must exist.
- The REST menu API (`/menus.json`) requires the `menus` scope which may not be available on all stores. The code handles this gracefully — `task2_menu.py` falls back to GraphQL `menuUpdate` automatically when REST returns 403. No action needed.
- The script is **idempotent**: re-running `main.py` updates existing collections, skips already-created redirects, and rebuilds the menu from scratch. It is safe to run multiple times.
- After execution, `execution_log.json` is written to the repo root with full details (collection GIDs, redirect counts, timestamps). This file is not committed.
- The `deliverables/` directory contains a full Shopify Liquid theme and product CSV — these are deployment artifacts, not runnable code.
- The bundled `shopify-comet-electron-final (1).zip` is a separate Node.js/Electron project unrelated to the main Python automation.
