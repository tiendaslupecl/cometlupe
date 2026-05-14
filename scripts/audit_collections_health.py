"""Auditoria de salud de colecciones."""
import sys, time
from pathlib import Path
from collections import defaultdict
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS, graphql
import requests

def paginate(path, key, **params):
    items, params["limit"] = [], params.get("limit", 250)
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=45)
        r.raise_for_status()
        items += r.json().get(key, [])
        link, url, params = r.headers.get("Link", ""), None, {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items

print("Cargando colecciones...")
custom = paginate("custom_collections.json", "custom_collections", fields="id,handle,title,published_at")
smart  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title,published_at")
all_cols = custom + smart
published = [c for c in all_cols if c.get("published_at")]
unpublished = [c for c in all_cols if not c.get("published_at")]
print(f"  {len(published)} publicadas, {len(unpublished)} no publicadas")

col_counts = {}
prod_to_cols = defaultdict(list)
for col in published:
    prods = paginate(f"collections/{col['id']}/products.json", "products", fields="id,status")
    act = [p for p in prods if p.get("status") == "active"]
    col_counts[col["id"]] = (col["title"], col["handle"], len(act))
    for p in act: prod_to_cols[p["id"]].append(col["handle"])
    time.sleep(0.1)

print("Cargando upsells...")
Q = 'query($cursor: String) { products(first: 250, after: $cursor, query: "status:active") { pageInfo { hasNextPage endCursor } nodes { id title metafield(namespace: "custom", key: "upsell_collection") { value } } } }'
cursor, prod_upsell = None, {}
while True:
    data = graphql(Q, {"cursor": cursor})
    for n in data["products"]["nodes"]:
        gid = n["id"].split("/")[-1]
        has = bool(n.get("metafield") and n["metafield"].get("value"))
        prod_upsell[gid] = (n["title"], has)
    info = data["products"]["pageInfo"]
    if not info["hasNextPage"]: break
    cursor = info["endCursor"]
    time.sleep(0.2)

total_prods = len(prod_upsell)
with_upsell = sum(1 for _, h in prod_upsell.values() if h)

solapadas, seen, col_sets = [], set(), defaultdict(set)
for pid, cols in prod_to_cols.items():
    for c in cols: col_sets[c].add(pid)
handles = list(col_sets.keys())
for i, h1 in enumerate(handles):
    for h2 in handles[i+1:]:
        s1, s2 = col_sets[h1], col_sets[h2]
        if not s1 or not s2: continue
        ov = len(s1 & s2)
        sm = min(len(s1), len(s2))
        if sm > 0 and ov/sm > 0.7 and ov >= 5:
            k = tuple(sorted([h1, h2]))
            if k not in seen:
                seen.add(k)
                solapadas.append((h1, len(s1), h2, len(s2), ov))

sep = "=" * 65
print(f"\n{sep}\nRESUMEN SALUD DE COLECCIONES\n{sep}")
print(f"  Total publicadas             : {len(published):4d}")
print(f"  No publicadas (invisibles)   : {len(unpublished):4d}")
vacias = [(cid,t,h,n) for cid,(t,h,n) in col_counts.items() if n == 0]
pocas  = [(cid,t,h,n) for cid,(t,h,n) in col_counts.items() if 1 <= n <= 2]
print(f"  Colecciones vacias           : {len(vacias):4d}")
print(f"  Con 1-2 productos            : {len(pocas):4d}")
print(f"  Pares solapados (>70%)       : {len(solapadas):4d}")
print(f"\n  Productos con upsell         : {with_upsell:4d} / {total_prods}")
print(f"  Productos SIN upsell         : {total_prods - with_upsell:4d}")
print(f"\nPROBLEMAS CRITICOS: {len(vacias) + (total_prods - with_upsell)}")

if vacias:
    print(f"\n{sep}\nCOLECCIONES VACIAS ({len(vacias)})\n{sep}")
    for _, t, h, n in vacias[:30]: print(f"  {t[:50]:50s}  /collections/{h}")
if pocas:
    print(f"\n{sep}\n1-2 PRODUCTOS ({len(pocas)})\n{sep}")
    for _, t, h, n in pocas[:30]: print(f"  [{n}] {t[:50]:50s}  /collections/{h}")
if unpublished:
    print(f"\n{sep}\nNO PUBLICADAS ({len(unpublished)})\n{sep}")
    for c in unpublished[:20]: print(f"  {c['title'][:55]:55s}  {c['handle']}")
if solapadas:
    print(f"\n{sep}\nSOLAPADAS >70% ({len(solapadas)})\n{sep}")
    for h1,n1,h2,n2,ov in solapadas[:20]: print(f"  {h1} ({n1}) <-> {h2} ({n2})  overlap={ov}")
sin_up = [(gid,t) for gid,(t,h) in prod_upsell.items() if not h]
if sin_up:
    print(f"\n{sep}\nSIN UPSELL ({len(sin_up)}) - primeros 40\n{sep}")
    for gid, t in sin_up[:40]: print(f"  [{gid}] {t[:65]}")
    if len(sin_up) > 40: print(f"  ... y {len(sin_up)-40} mas")
