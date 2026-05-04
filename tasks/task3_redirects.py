"""
Tarea 3: Crear redirects 301 desde colecciones viejas.
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql
from config import REDIRECT_MAP, PROTECTED_HANDLES, COLLECTIONS

LIST_COLLECTIONS = """
query listCollections($cursor: String) {
  collections(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes { id handle title productsCount { count } }
  }
}
"""

CREATE_REDIRECT = """
mutation urlRedirectCreate($urlRedirect: UrlRedirectInput!) {
  urlRedirectCreate(urlRedirect: $urlRedirect) {
    urlRedirect { id path target }
    userErrors { field message }
  }
}
"""

CHECK_REDIRECT = """
query checkRedirect($query: String!) {
  urlRedirects(first: 1, query: $query) {
    nodes { id path target }
  }
}
"""


def list_all_collections() -> list:
    """Lista todas las colecciones de la tienda con paginación."""
    collections = []
    cursor = None
    while True:
        data = graphql(LIST_COLLECTIONS, {"cursor": cursor})
        collections.extend(data["collections"]["nodes"])
        if not data["collections"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["collections"]["pageInfo"]["endCursor"]
    return collections


def find_redirect_target(handle: str) -> str | None:
    """Mapea handle viejo al destino correcto."""
    handle_lower = handle.lower()
    for keyword, target in REDIRECT_MAP.items():
        if keyword in handle_lower:
            return target
    return None


def create_redirect(path: str, target: str) -> bool:
    # Idempotencia
    existing = graphql(CHECK_REDIRECT, {"query": f"path:{path}"})
    if existing["urlRedirects"]["nodes"]:
        print(f"[SKIP] Redirect ya existe: {path}")
        return False
    
    result = graphql(
        CREATE_REDIRECT,
        {"urlRedirect": {"path": path, "target": target}},
    )
    errors = result["urlRedirectCreate"].get("userErrors", [])
    if errors:
        print(f"[ERROR] {path}: {errors}")
        return False
    
    print(f"[OK] {path} -> {target}")
    return True


def create_all_redirects() -> dict:
    """Procesa todas las colecciones viejas y crea redirects."""
    new_handles = {c["handle"] for c in COLLECTIONS}
    all_protected = PROTECTED_HANDLES | new_handles
    
    all_collections = list_all_collections()
    print(f"[INFO] Total colecciones encontradas: {len(all_collections)}")
    
    old_collections = [c for c in all_collections if c["handle"] not in all_protected]
    print(f"   Colecciones a redirigir: {len(old_collections)}")
    
    created = 0
    skipped = 0
    no_match = []
    
    for col in old_collections:
        path = f"/collections/{col['handle']}"
        target = find_redirect_target(col["handle"])
        
        if target is None:
            no_match.append(col["handle"])
            continue
        
        if create_redirect(path, target):
            created += 1
        else:
            skipped += 1
        
        time.sleep(0.5)
    
    print(f"\n[STATS] Redirects: {created} creados, {skipped} ya existian")
    if no_match:
        print(f"[WARN] Sin mapping ({len(no_match)} colecciones, requieren revision manual):")
        for h in no_match:
            print(f"   - /collections/{h}")
    
    return {
        "created": created,
        "skipped": skipped,
        "no_match": no_match,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("TAREA 3: Crear redirects 301")
    print("=" * 60)
    create_all_redirects()
