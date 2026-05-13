"""Agrega 'Aguja de Mano' y similares a la regla de herramientas-de-costura."""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

r = requests.get(f"{REST_BASE}/smart_collections.json", headers=HEADERS,
                 params={"limit":250}, timeout=30)
smart = {c["handle"]: c for c in r.json()["smart_collections"]}
col = smart.get("herramientas-de-costura")
if not col:
    raise SystemExit("herramientas-de-costura no encontrada")

new_rules = list(col.get("rules", []))
# Agregar reglas si no estan
extras = [
    {"column":"title","relation":"contains","condition":"Aguja de Mano"},
    {"column":"title","relation":"contains","condition":"Aguja a Mano"},
    {"column":"title","relation":"contains","condition":"Aguja Circular"},
    {"column":"title","relation":"contains","condition":"Aguja de Tejer"},
    {"column":"title","relation":"contains","condition":"Aguja Tapiceria"},
    {"column":"title","relation":"contains","condition":"Aguja Lana"},
    {"column":"title","relation":"contains","condition":"Aguja Bordado a Mano"},
]
existing = {(r["column"], r["relation"], r["condition"].lower()) for r in new_rules}
for e in extras:
    key = (e["column"], e["relation"], e["condition"].lower())
    if key not in existing:
        new_rules.append(e)

payload = {"smart_collection": {
    "id": col["id"],
    "disjunctive": True,
    "rules": new_rules,
}}
rr = requests.put(f"{REST_BASE}/smart_collections/{col['id']}.json",
                  headers=HEADERS, json=payload, timeout=30)
print(f"HTTP {rr.status_code}")
print(f"Reglas finales: {len(new_rules)}")
for r in new_rules:
    print(f"  [{r['column']}] {r['relation']} '{r['condition']}'")
