"""
Crea la definición de metafield custom.upsell_collection (collection_reference)
en Shopify para que sea accesible en Liquid.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

SHOP_DOMAIN = REST_BASE.split("/admin")[0].replace("https://", "")

# Usar GraphQL Admin API para crear la definición
GRAPHQL_URL = f"https://{SHOP_DOMAIN}/admin/api/2025-01/graphql.json"

MUTATION = """
mutation CreateMetafieldDefinition($definition: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $definition) {
    createdDefinition {
      id
      name
      namespace
      key
      type { name }
    }
    userErrors {
      field
      message
    }
  }
}
"""

variables = {
    "definition": {
        "name": "Upsell Collection",
        "namespace": "custom",
        "key": "upsell_collection",
        "type": "collection_reference",
        "ownerType": "PRODUCT",
        "visibleToStorefrontApi": True,
    }
}

r = requests.post(
    GRAPHQL_URL,
    headers={**HEADERS, "Content-Type": "application/json"},
    json={"query": MUTATION, "variables": variables},
    timeout=30,
)

data = r.json()
result = data.get("data", {}).get("metafieldDefinitionCreate", {})
errors = result.get("userErrors", [])

if errors:
    for e in errors:
        print(f"⚠️  {e['field']}: {e['message']}")
else:
    defn = result.get("createdDefinition", {})
    print(f"✅ Definición creada: {defn.get('namespace')}.{defn.get('key')} ({defn.get('type', {}).get('name')})")
    print("   Ahora product.metafields.custom.upsell_collection.value funciona en Liquid.")
