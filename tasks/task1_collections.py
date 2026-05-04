"""
Tarea 1: Crear las 6 colecciones automatizadas.
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql
from config import COLLECTIONS

CREATE_COLLECTION = """
mutation collectionCreate($input: CollectionInput!) {
  collectionCreate(input: $input) {
    collection {
      id
      handle
      title
      productsCount { count }
    }
    userErrors { field message }
  }
}
"""

CHECK_HANDLE = """
query checkHandle($handle: String!) {
  collectionByHandle(handle: $handle) {
    id
    handle
    productsCount { count }
  }
}
"""


def create_all_collections() -> dict:
    """Crea las 6 colecciones, retorna {handle: id}."""
    collection_ids = {}
    
    for c in COLLECTIONS:
        # Idempotencia: ¿ya existe?
        existing = graphql(CHECK_HANDLE, {"handle": c["handle"]})
        if existing.get("collectionByHandle"):
            cid = existing["collectionByHandle"]["id"]
            count = existing["collectionByHandle"]["productsCount"]["count"]
            print(f"[SKIP] '{c['title']}' ya existe ({count} productos) - saltando")
            collection_ids[c["handle"]] = cid
            continue
        
        # Construir reglas
        rules = [
            {"column": "TAG", "relation": "EQUALS", "condition": tag}
            for tag in c["tags"]
        ]
        if "extra_rules" in c:
            rules.extend(c["extra_rules"])
        
        variables = {
            "input": {
                "title": c["title"],
                "handle": c["handle"],
                "descriptionHtml": f"<p>{c['description']}</p>",
                "ruleSet": {
                    "appliedDisjunctively": True,
                    "rules": rules
                },
                "seo": {
                    "title": c["seo_title"],
                    "description": c["seo_description"]
                },
            }
        }
        
        result = graphql(CREATE_COLLECTION, variables)
        
        errors = result["collectionCreate"].get("userErrors", [])
        if errors:
            print(f"[ERROR] Error creando '{c['title']}': {errors}")
            continue
        
        col = result["collectionCreate"]["collection"]
        collection_ids[c["handle"]] = col["id"]
        print(f"[OK] Creada '{col['title']}'")
        
        time.sleep(2)  # Esperar que Shopify indexe productos
        
        # Validar conteo de productos
        check = graphql(CHECK_HANDLE, {"handle": c["handle"]})
        actual = check["collectionByHandle"]["productsCount"]["count"]
        expected = c["expected_count"]
        delta_pct = abs(actual - expected) / expected * 100 if expected else 0
        
        icon = "[OK]" if delta_pct <= 15 else "[WARN]"
        print(f"   {icon} {actual} productos (esperado ~{expected}, delta {delta_pct:.1f}%)")
        
        time.sleep(1)
    
    return collection_ids


if __name__ == "__main__":
    print("=" * 60)
    print("TAREA 1: Crear colecciones automatizadas")
    print("=" * 60)
    ids = create_all_collections()
    print(f"\n[IDS] IDs guardados: {ids}")
