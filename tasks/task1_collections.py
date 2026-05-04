"""
Tarea 1: Crear las 6 colecciones automatizadas.
"""
import os
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql, publish_resource_to_online_store
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

UPDATE_COLLECTION = """
mutation collectionUpdate($input: CollectionInput!) {
  collectionUpdate(input: $input) {
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


def _build_input(c: dict, collection_id: str | None = None) -> dict:
    rel = c.get("rule_relation", "EQUALS")
    rules = [
        {"column": "TAG", "relation": rel, "condition": tag}
        for tag in c["tags"]
    ]
    if "extra_rules" in c:
        rules.extend(c["extra_rules"])
    payload = {
        "title": c["title"],
        "handle": c["handle"],
        "descriptionHtml": f"<p>{c['description']}</p>",
        "ruleSet": {
            "appliedDisjunctively": True,
            "rules": rules,
        },
        "seo": {
            "title": c["seo_title"],
            "description": c["seo_description"],
        },
    }
    if collection_id:
        payload["id"] = collection_id
    return payload


def _validate_count(c: dict) -> tuple[int, float]:
    check = graphql(CHECK_HANDLE, {"handle": c["handle"]})
    actual = check["collectionByHandle"]["productsCount"]["count"]
    expected = c["expected_count"]
    delta_pct = abs(actual - expected) / expected * 100 if expected else 0
    status = "✅" if delta_pct <= 15 else "⚠️"
    print(f"   {status} Productos: {actual} (esperado ~{expected}, delta {delta_pct:.1f}%)")
    return actual, delta_pct


def create_all_collections() -> dict:
    """Crea o actualiza las 6 colecciones, retorna {handle: id}."""
    collection_ids = {}

    for c in COLLECTIONS:
        existing = graphql(CHECK_HANDLE, {"handle": c["handle"]})
        current = existing.get("collectionByHandle")

        if current:
            cid = current["id"]
            count = current["productsCount"]["count"]
            print(f"🔄 '{c['title']}' ya existe ({cid}, {count} productos) — actualizando reglas/SEO")
            result = graphql(UPDATE_COLLECTION, {"input": _build_input(c, cid)})
            errors = result["collectionUpdate"].get("userErrors", [])
            if errors:
                print(f"❌ {c['title']} (update): {errors}")
                collection_ids[c["handle"]] = cid
                continue
            col = result["collectionUpdate"]["collection"]
            collection_ids[c["handle"]] = col["id"]
            print(f"✅ Actualizada '{col['title']}' ({col['id']})")
        else:
            result = graphql(CREATE_COLLECTION, {"input": _build_input(c)})
            errors = result["collectionCreate"].get("userErrors", [])
            if errors:
                print(f"❌ {c['title']} (create): {errors}")
                continue
            col = result["collectionCreate"]["collection"]
            collection_ids[c["handle"]] = col["id"]
            print(f"✅ Creada '{col['title']}' ({col['id']})")

        skip_pub = os.getenv("SKIP_STORE_PUBLISH", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        if not skip_pub and publish_resource_to_online_store(col["id"]):
            print("   📣 Publicada en canal Tienda online (evita 404 en el escaparate)")

        time.sleep(5)
        _validate_count(c)
        time.sleep(0.5)

    return collection_ids


if __name__ == "__main__":
    print("=" * 60)
    print("TAREA 1: Crear colecciones automatizadas")
    print("=" * 60)
    ids = create_all_collections()
    print(f"\n[IDS] IDs guardados: {ids}")
