# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python CLI tool ("Tiendas Lupe") that automates Shopify store navigation restructuring via the Shopify Admin API. There is no local web server, database, or Docker dependency — it is a pure CLI application.

### Running the application

- **Dependencies**: `pip install -r requirements.txt` (only `requests` and `python-dotenv`).
- **Entry point**: `python main.py` — runs 4 sequential tasks (collections, menu, redirects, filters report).
- **Credentials**: Requires a `.env` file (copy from `.env.example`) with valid `SHOP_DOMAIN` and `ADMIN_API_TOKEN` (Shopify Admin API token starting with `shpat_`). Without valid credentials, the app exits immediately with a clear error.
- The `shopify_client.py` module validates the token at import time via `load_dotenv()`. **Any import of `shopify_client`** will fail if `.env` is missing or has a placeholder token. This includes `scripts/theme_push_live_id.py` and `scripts/find_mixed_inventory_product.py`.

### Theme push

- `python scripts/theme_push_live_id.py <THEME_ID>` pushes all CRO theme assets from `deliverables/lupe-cro-theme/` to the specified Shopify theme via REST Asset API.
- Several existing section files have Shopify schema validation errors (url-type setting defaults, name length limits). These are pre-existing and result in 422 responses for those specific assets. The snippets, config, locales, layout, and CSS assets upload cleanly.

### Tasks that work without API credentials

- `python tasks/task4_filters_report.py` — generates the manual filters configuration report (no API calls).
- `python -c "import config"` — validates config data structures.

### No linting or test framework

This repo has no linter config (no `pyproject.toml`, `setup.cfg`, `ruff.toml`, etc.) and no test suite. Syntax can be verified with `python -m py_compile <file>`. The CI workflow (`.github/workflows/blank.yml`) is a placeholder that only echoes "Hello, world!".

### Static theme assets

The `deliverables/lupe-cro-theme/` directory contains Shopify Liquid/JSON/CSS theme files meant to be uploaded to Shopify via `scripts/theme_push_live_id.py` or manually.
