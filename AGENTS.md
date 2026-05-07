# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python CLI tool ("Tiendas Lupe") that automates Shopify store navigation restructuring via the Shopify Admin API. There is no local web server, database, or Docker dependency — it is a pure CLI application.

### Running the application

- **Dependencies**: `pip install -r requirements.txt` (only `requests` and `python-dotenv`).
- **Entry point**: `python main.py` — runs 4 sequential tasks (collections, menu, redirects, filters report).
- **Credentials**: Requires a `.env` file (copy from `.env.example`) with valid `SHOP_DOMAIN` and `ADMIN_API_TOKEN` (Shopify Admin API token starting with `shpat_`). Without valid credentials, the app exits immediately with a clear error.
- The `shopify_client.py` module is imported at the top level and calls `load_dotenv()` + validates the token at import time. This means **any import of `shopify_client`** will fail if `.env` is missing or has a placeholder token.

### Tasks that work without API credentials

- `python tasks/task4_filters_report.py` — generates the manual filters configuration report (no API calls).
- `python -c "import config"` — validates config data structures.

### No linting or test framework

This repo has no linter config (no `pyproject.toml`, `setup.cfg`, `ruff.toml`, etc.) and no test suite. Syntax can be verified with `python -m py_compile <file>`. The CI workflow (`.github/workflows/blank.yml`) is a placeholder that only echoes "Hello, world!".

### Static theme assets

The `deliverables/lupe-cro-theme/` directory contains Shopify Liquid/JSON/CSS theme files meant to be uploaded to Shopify directly — they are not runnable locally.
