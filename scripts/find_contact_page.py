"""Busca la pagina de contacto correcta."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

r = requests.get(f"{REST_BASE}/pages.json", headers=HEADERS,
                 params={"limit": 250, "fields":"id,handle,title,published_at"}, timeout=30)
pages = r.json()["pages"]

print("Paginas que matchean 'contact':")
for p in pages:
    if "contact" in p["handle"].lower() or "contact" in p["title"].lower():
        pub = "publicada" if p.get("published_at") else "DRAFT"
        print(f"  [{p['id']}] {p['handle']:30s} '{p['title']}' ({pub})")

print()
print("Todas las paginas publicadas:")
for p in sorted(pages, key=lambda x: x["handle"]):
    if p.get("published_at"):
        print(f"  /{p['handle']:35s} -> {p['title']}")
