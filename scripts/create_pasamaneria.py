"""
Crea productos de pasamaneria en Shopify como borradores.
Variantes: Color (Dorado / Plateado) x Presentacion (Metro / Pieza 27 metros)
Uso: python scripts/create_pasamaneria.py
"""
import sys, time
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from shopify_client import REST_BASE, HEADERS
import requests

COLLECTION_HANDLE = "pasamaneria"

PRODUCTS = [
    dict(ref="001", titulo="Galon Trenzado Decorativo Ref. 001",
         desc="Galon trenzado dorado de alta calidad para decoracion de prendas, cortinas y manualidades.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="002", titulo="Galon Dorado con Detalle Central Ref. 002",
         desc="Galon decorativo dorado con detalle central texturado, ideal para cenefas, uniformes y decoracion textil.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="003", titulo="Galon Dorado Bicolor Ref. 003",
         desc="Galon dorado con tono bicolor, efecto relieve. Apto para confeccion de disfraces, uniformes y decoracion.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="004", titulo="Galon Dorado con Patron Floral Ref. 004",
         desc="Galon decorativo dorado con patron floral en relieve. Ideal para cortinas, tapicerias y manualidades.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon"),
    dict(ref="005", titulo="Galon Dorado con Relieve Ref. 005",
         desc="Galon dorado de acabado brillante con textura en relieve. Uso en confeccion de ropa de gala y artesanias.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon"),
    dict(ref="006", titulo="Galon Dorado Geometrico Ref. 006",
         desc="Galon dorado con patron geometrico repetitivo. Resistente y flexible, apto para tapiceria y vestuario.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon"),
    dict(ref="007", titulo="Galon Dorado Festoneado Ref. 007",
         desc="Galon dorado festoneado de acabado uniforme. Ideal para bordes de cortinas, cojines y costura creativa.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon"),
    dict(ref="008", titulo="Galon Dorado Delgado Ref. 008",
         desc="Galon dorado delgado y flexible, facil de coser. Perfecto para detalles finos en prendas y manualidades.",
         colores=["Dorado"], ancho_cm=1.0, tipo="Galon"),
    dict(ref="2325", titulo="Encaje Ondulado Decorativo Ref. 2325",
         desc="Encaje ondulado metalizado disponible en dorado y plateado. Textura suave y flexible para prendas y accesorios.",
         colores=["Dorado", "Plateado"], ancho_cm=1.5, tipo="Encaje"),
    dict(ref="5599", titulo="Galon con Flecos Dorado Ref. 5599",
         desc="Galon dorado con flecos laterales, aspecto elegante y festivo. Ideal para disfraces, cortinas y tapicerias.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon con Flecos"),
    dict(ref="5598", titulo="Galon con Flecos Texturado Ref. 5598",
         desc="Galon dorado texturado con terminacion en flecos. Acabado firme y uniforme para vestuario y decoracion.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon con Flecos"),
    dict(ref="8544-1cm", titulo="Ric-Rac Metalizado 1 cm Ref. 931/8544",
         desc="Cinta ric-rac metalizada de 1 cm, disponible en dorado y plateado. Ideal para bordes de manualidades y prendas.",
         colores=["Dorado", "Plateado"], ancho_cm=1.0, tipo="Ric-Rac"),
    dict(ref="8544-0.8cm", titulo="Ric-Rac Metalizado 0.8 cm Ref. 941/8544",
         desc="Cinta ric-rac metalizada de 0.8 cm, disponible en dorado y plateado. Perfecta para detalles finos en costura.",
         colores=["Dorado", "Plateado"], ancho_cm=0.8, tipo="Ric-Rac"),
    dict(ref="132515", titulo="Galon Floral Metalizado Ref. 132515",
         desc="Galon con patron floral metalizado en dorado y plateado. Ideal para prendas de fiesta y accesorios.",
         colores=["Dorado", "Plateado"], ancho_cm=2.0, tipo="Galon Floral"),
    dict(ref="137525", titulo="Encaje Festoneado Dorado Ref. 137525",
         desc="Encaje dorado festoneado de acabado brillante. Ideal para detalles decorativos en prendas y manualidades.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Encaje"),
    dict(ref="134104", titulo="Galon Dorado con Bolitas Ref. 134104",
         desc="Galon dorado con aplicaciones de bolitas decorativas. Acabado elegante para prendas de fiesta y accesorios.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="Nok3", titulo="Galon Especial Metalizado Ref. Nok3",
         desc="Galon metalizado especial de diseno exclusivo. Alta calidad para proyectos de costura creativa y decoracion.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="133895", titulo="Cinta con Dijes Gota Metalizada Ref. 133895",
         desc="Cinta metalizada con dijes colgantes en forma de gota, en dorado y plateado holografico. Para prendas de fiesta.",
         colores=["Dorado", "Plateado"], ancho_cm=3.0, tipo="Cinta con Dijes"),
    dict(ref="8445", titulo="Galon Tejido Calado Dorado Ref. 8445",
         desc="Galon dorado tejido con efecto calado, textura firme y aspecto elegante. Para bordes de prendas y cortinas.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="132258", titulo="Galon Dorado con Arabescos Ref. 132258",
         desc="Galon dorado con patron de arabescos, acabado brillante y resistente. Para tapiceria y vestuario de gala.",
         colores=["Dorado"], ancho_cm=2.0, tipo="Galon"),
    dict(ref="131589", titulo="Galon Trenzado Fino Dorado Ref. 131589",
         desc="Galon trenzado fino dorado, flexible y de facil aplicacion. Apto para prendas, accesorios y proyectos creativos.",
         colores=["Dorado"], ancho_cm=1.5, tipo="Galon"),
    dict(ref="13246", titulo="Galon Cadena Metalizado Ref. 13246",
         desc="Galon con efecto cadena metalizada en dorado y plateado. Acabado rigido y decorativo para prendas de fiesta.",
         colores=["Dorado", "Plateado"], ancho_cm=1.5, tipo="Galon Cadena"),
    dict(ref="10280", titulo="Galon Ondulado Rizado Metalizado Ref. 10280",
         desc="Galon ondulado rizado metalizado en dorado y plateado. Textura decorativa para prendas y manualidades.",
         colores=["Dorado", "Plateado"], ancho_cm=1.0, tipo="Galon Ondulado"),
]

def paginate(path, key, **params):
    items, params["limit"] = [], 250
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

def add_metafield(product_id, namespace, key, value):
    requests.post(f"{REST_BASE}/products/{product_id}/metafields.json", headers=HEADERS,
        json={"metafield": {"namespace": namespace, "key": key,
                            "value": str(value), "type": "single_line_text_field"}}, timeout=30)

print(f"Buscando coleccion '{COLLECTION_HANDLE}'...")
col_list = (paginate("custom_collections.json", "custom_collections",
                     handle=COLLECTION_HANDLE, fields="id,title") +
            paginate("smart_collections.json", "smart_collections",
                     handle=COLLECTION_HANDLE, fields="id,title"))
if not col_list:
    print(f"  ERROR: no existe la coleccion '{COLLECTION_HANDLE}'. Creala primero en Shopify Admin.")
    sys.exit(1)
col_id = col_list[0]["id"]
print(f"  Coleccion: {col_list[0]['title']} (id={col_id})")

created = 0
errors = 0

for p in PRODUCTS:
    titulo  = p["titulo"]
    colores = p["colores"]

    if len(colores) > 1:
        options = [
            {"name": "Color",        "values": colores},
            {"name": "Presentacion", "values": ["Metro", "Pieza de 27 metros"]},
        ]
        variants = [
            {"option1": color, "option2": pres, "price": "0.00",
             "sku": f"{p['ref']}-{color[:3].upper()}-{'M' if pres == 'Metro' else '27M'}",
             "inventory_management": None, "requires_shipping": True}
            for color in colores
            for pres in ["Metro", "Pieza de 27 metros"]
        ]
    else:
        options = [
            {"name": "Presentacion", "values": ["Metro", "Pieza de 27 metros"]},
        ]
        variants = [
            {"option1": pres, "price": "0.00",
             "sku": f"{p['ref']}-{colores[0][:3].upper()}-{'M' if pres == 'Metro' else '27M'}",
             "inventory_management": None, "requires_shipping": True}
            for pres in ["Metro", "Pieza de 27 metros"]
        ]

    tags = f"pasamaneria,{p['tipo'].lower().replace(' ','-')},metalizado"
    if "Dorado" in colores: tags += ",dorado"
    if "Plateado" in colores: tags += ",plateado"

    payload = {"product": {
        "title": titulo,
        "body_html": f"<p>{p['desc']}</p><ul><li><b>Ref:</b> {p['ref']}</li><li><b>Tipo:</b> {p['tipo']}</li><li><b>Ancho:</b> {p['ancho_cm']} cm</li><li><b>Material:</b> Poliester metalizado</li><li><b>Colores:</b> {', '.join(colores)}</li><li><b>Presentacion:</b> Metro / Pieza de 27 metros</li></ul>",
        "vendor": "Tiendas Lupe",
        "product_type": "Pasamaneria",
        "status": "draft",
        "tags": tags,
        "options": options,
        "variants": variants,
    }}

    r = requests.post(f"{REST_BASE}/products.json", headers=HEADERS, json=payload, timeout=30)
    if r.status_code not in (200, 201):
        print(f"  ERROR {r.status_code}: {titulo[:50]} - {r.text[:100]}")
        errors += 1
        continue

    prod_id = r.json()["product"]["id"]
    requests.post(f"{REST_BASE}/collects.json", headers=HEADERS,
        json={"collect": {"product_id": prod_id, "collection_id": col_id}}, timeout=30)
    add_metafield(prod_id, "custom", "referencia",   p["ref"])
    add_metafield(prod_id, "custom", "ancho_cm",     str(p["ancho_cm"]))
    add_metafield(prod_id, "custom", "material",     "Poliester metalizado")
    add_metafield(prod_id, "custom", "presentacion", "Metro / Pieza de 27 metros")
    add_metafield(prod_id, "custom", "largo_pieza",  "27 metros")
    add_metafield(prod_id, "custom", "colores",      ", ".join(colores))
    print(f"  OK [{p['ref']}] {titulo[:55]} (id={prod_id})")
    created += 1
    time.sleep(0.3)

print(f"\n{created} productos creados / {errors} errores")
print("Estado BORRADOR. Agrega fotos desde Shopify Admin -> Productos.")
