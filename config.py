"""
Configuración de Tiendas Lupe — Reestructuración de navegación.
Contiene todas las colecciones, menú y mapping de redirects.
"""

# ════════════════════════════════════════════════════════════
# 6 COLECCIONES MADRE A CREAR
# ════════════════════════════════════════════════════════════
COLLECTIONS = [
    {
        "title": "Máquinas y Repuestos",
        "handle": "maquinas-y-repuestos",
        "description": "Encuentra todo para tu máquina de coser: agujas industriales y caseras, prensatelas de máquina recta y overlock, repuestos originales, cuchillos para cortadoras, planchas industriales y más. Marcas Singer, Schmetz, Groz Beckert, Yamato, Siruba, Brother, Eastman.",
        "tags": [
            "cat-agujas-maquina", "cat-prensatelas", "cat-repuestos",
            "cat-cuchillos", "cat-planchas-aguja", "cat-planchas-ropa",
            "cat-accesorios-maquina", "cat-cortadoras"
        ],
        "rule_relation": "EQUALS",
        "expected_count": 272,
        "seo_title": "Máquinas de Coser y Repuestos | Tiendas Lupe",
        "seo_description": "Compra agujas, prensatelas, repuestos y accesorios para máquina industrial y casera. Marcas premium Singer, Schmetz, Groz Beckert, Yamato.",
    },
    {
        "title": "Herramientas de Costura",
        "handle": "herramientas-costura",
        "description": "Herramientas profesionales para costureras y modistas: tijeras Mundial, Pin y Reach, alfileres, pinzas, descosedores, lápices marcadores y tizas para tela.",
        "tags": [
            "cat-tijeras", "cat-alfileres", "cat-herramientas-costura",
            "cat-herramientas-marcado", "cat-herramientas-manuales"
        ],
        "rule_relation": "EQUALS",
        "expected_count": 40,
        "seo_title": "Herramientas de Costura Profesionales | Tiendas Lupe",
        "seo_description": "Tijeras Mundial, Pin, Reach, alfileres, descosedores y herramientas de marcado. Calidad profesional para costureras y modistas.",
    },
    {
        "title": "Insumos de Confección",
        "handle": "insumos-confeccion",
        "description": "Todo lo necesario para confeccionar prendas profesionales: hilos de costura y bordado, elásticos, cierres, broches, velcros, cintas bies y entretelas. Marcas Lama, Samurai, Durafill.",
        "tags": [
            "cat-elasticos", "cat-cierres", "cat-broches",
            "cat-velcros", "cat-cintas-bies", "cat-cintas", "cat-entretelas"
        ],
        # Shopify no permite TAG CONTAINS en colecciones inteligentes.
        # Para aproximar el universo esperado (~453), complementamos tags exactos
        # con reglas por título para hilos/insumos comunes.
        "extra_rules": [
            {"column": "TAG", "relation": "EQUALS", "condition": "hilo"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "hilo"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "cierre"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "elastico"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "broche"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "velcro"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "cinta"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "bies"},
            {"column": "TITLE", "relation": "CONTAINS", "condition": "entretela"},
        ],
        "rule_relation": "EQUALS",
        "expected_count": 453,
        "seo_title": "Insumos de Confección | Hilos, Elásticos, Cierres | Tiendas Lupe",
        "seo_description": "Hilos Lama, Samurai, Durafill. Elásticos, cierres, broches, velcros, cintas y entretelas. Todo para tu confección profesional.",
    },
    {
        "title": "Tejido y Manualidades",
        "handle": "tejido-manualidades",
        "description": "Para tejedoras y artesanas: lanas Modista La Económica, Lanaquil, trapillo, bastidores de bambú, agujas crochet, palillos y pasamanería decorativa.",
        "tags": [
            "cat-lanas", "cat-trapillo", "cat-bastidores",
            "cat-agujas-tejido", "cat-agujas-mano", "cat-pasamaneria"
        ],
        "rule_relation": "EQUALS",
        "expected_count": 60,
        "seo_title": "Lanas, Trapillo y Bastidores | Tejido y Manualidades",
        "seo_description": "Lanas Modista, Lanaquil, trapillo, bastidores y todo para tejer crochet, palillo y bordar.",
    },
    {
        "title": "Bisutería y Decoración",
        "handle": "bisuteria-decoracion",
        "description": "Insumos para bisutería y proyectos decorativos: cordones SPESSO macramé, argollas metálicas, cuentas de madera, perlas, strass hotfix y cascabeles.",
        "tags": [
            "cat-cordones"
        ],
        "rule_relation": "EQUALS",
        "expected_count": 25,
        "seo_title": "Bisutería y Cordones de Macramé | Tiendas Lupe",
        "seo_description": "Cordones SPESSO, argollas, perlas, strass y todo para bisutería y manualidades decorativas.",
    },
    {
        "title": "Tinturas y Pegamentos",
        "handle": "tinturas-pegamentos",
        "description": "Tinturas Montblanc para teñir telas en todos los colores y pegamentos especializados Dritz para textiles y manualidades.",
        "tags": ["cat-tinturas"],
        "extra_rules": [
            {"column": "TITLE", "relation": "CONTAINS", "condition": "pegamento"},
        ],
        "rule_relation": "EQUALS",
        "expected_count": 13,
        "seo_title": "Tinturas Montblanc y Pegamentos | Tiendas Lupe",
        "seo_description": "Anilinas Montblanc para teñir telas y ropa. Pegamentos Dritz para textiles. Calidad profesional para tus proyectos.",
    },
]


# ════════════════════════════════════════════════════════════
# ESTRUCTURA DEL MENÚ PRINCIPAL
# ════════════════════════════════════════════════════════════
MENU_STRUCTURE = [
    {"title": "Inicio", "type": "FRONTPAGE", "url": "/"},
    {
        "title": "Máquinas y Repuestos",
        "type": "COLLECTION",
        "handle": "maquinas-y-repuestos",
        "items": [
            ("Agujas", "/collections/maquinas-y-repuestos?filter.p.tag=cat-agujas-maquina"),
            ("Prensatelas", "/collections/maquinas-y-repuestos?filter.p.tag=cat-prensatelas"),
            ("Repuestos", "/collections/maquinas-y-repuestos?filter.p.tag=cat-repuestos"),
            ("Cuchillos y Cortadoras", "/collections/maquinas-y-repuestos?filter.p.tag=cat-cuchillos"),
            ("Planchas Industriales", "/collections/maquinas-y-repuestos?filter.p.tag=cat-planchas-ropa"),
        ],
    },
    {
        "title": "Herramientas",
        "type": "COLLECTION",
        "handle": "herramientas-costura",
        "items": [
            ("Tijeras", "/collections/herramientas-costura?filter.p.tag=cat-tijeras"),
            ("Alfileres y Pinzas", "/collections/herramientas-costura?filter.p.tag=cat-alfileres"),
            ("Marcadores y Tizas", "/collections/herramientas-costura?filter.p.tag=cat-herramientas-marcado"),
        ],
    },
    {
        "title": "Insumos de Confección",
        "type": "COLLECTION",
        "handle": "insumos-confeccion",
        "items": [
            ("Hilos", "/collections/insumos-confeccion?filter.p.tag=hilo"),
            ("Elásticos", "/collections/insumos-confeccion?filter.p.tag=cat-elasticos"),
            ("Cierres", "/collections/insumos-confeccion?filter.p.tag=cat-cierres"),
            ("Broches y Velcros", "/collections/insumos-confeccion?filter.p.tag=cat-broches"),
            ("Cintas y Bies", "/collections/insumos-confeccion?filter.p.tag=cat-cintas-bies"),
            ("Entretelas", "/collections/insumos-confeccion?filter.p.tag=cat-entretelas"),
        ],
    },
    {
        "title": "Tejido y Manualidades",
        "type": "COLLECTION",
        "handle": "tejido-manualidades",
        "items": [
            ("Lanas", "/collections/tejido-manualidades?filter.p.tag=cat-lanas"),
            ("Trapillo", "/collections/tejido-manualidades?filter.p.tag=cat-trapillo"),
            ("Bastidores", "/collections/tejido-manualidades?filter.p.tag=cat-bastidores"),
            ("Pasamanería", "/collections/tejido-manualidades?filter.p.tag=cat-pasamaneria"),
        ],
    },
    {
        "title": "Bisutería",
        "type": "COLLECTION",
        "handle": "bisuteria-decoracion",
        "items": [
            ("Cordones", "/collections/bisuteria-decoracion?filter.p.tag=cat-cordones"),
            ("Argollas y Aros", "/collections/bisuteria-decoracion?filter.p.tag=cat-argollas"),
            ("Cuentas y Perlas", "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria"),
            ("Strass y Cascabeles", "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria"),
        ],
    },
    {"title": "Tinturas", "type": "COLLECTION", "handle": "tinturas-pegamentos"},
    # HTTP evita 404 si la página no existe o no está publicada; override con CONTACT_PAGE_PATH en .env
    {"title": "Contacto", "type": "HTTP", "path": "/pages/contacto"},
]


# ════════════════════════════════════════════════════════════
# MAPPING DE REDIRECTS — handle viejo → URL nueva
# ════════════════════════════════════════════════════════════
REDIRECT_MAP = {
    "aguja": "/collections/maquinas-y-repuestos?filter.p.tag=cat-agujas-maquina",
    "prensatela": "/collections/maquinas-y-repuestos?filter.p.tag=cat-prensatelas",
    "repuesto": "/collections/maquinas-y-repuestos?filter.p.tag=cat-repuestos",
    "cuchillo": "/collections/maquinas-y-repuestos?filter.p.tag=cat-cuchillos",
    "cortadora": "/collections/maquinas-y-repuestos?filter.p.tag=cat-cuchillos",
    "plancha": "/collections/maquinas-y-repuestos?filter.p.tag=cat-planchas-ropa",
    "tijera": "/collections/herramientas-costura?filter.p.tag=cat-tijeras",
    "alfiler": "/collections/herramientas-costura?filter.p.tag=cat-alfileres",
    "hilo": "/collections/insumos-confeccion?filter.p.tag=hilo",
    "elastico": "/collections/insumos-confeccion?filter.p.tag=cat-elasticos",
    "cierre": "/collections/insumos-confeccion?filter.p.tag=cat-cierres",
    "broche": "/collections/insumos-confeccion?filter.p.tag=cat-broches",
    "velcro": "/collections/insumos-confeccion?filter.p.tag=cat-broches",
    "cinta": "/collections/insumos-confeccion?filter.p.tag=cat-cintas-bies",
    "bies": "/collections/insumos-confeccion?filter.p.tag=cat-cintas-bies",
    "entretela": "/collections/insumos-confeccion?filter.p.tag=cat-entretelas",
    "lana": "/collections/tejido-manualidades?filter.p.tag=cat-lanas",
    "trapillo": "/collections/tejido-manualidades?filter.p.tag=cat-trapillo",
    "bastidor": "/collections/tejido-manualidades?filter.p.tag=cat-bastidores",
    "pasamaneria": "/collections/tejido-manualidades?filter.p.tag=cat-pasamaneria",
    "cordon": "/collections/bisuteria-decoracion?filter.p.tag=cat-cordones",
    "argolla": "/collections/bisuteria-decoracion?filter.p.tag=cat-argollas",
    "bisuteria": "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria",
    "cuenca": "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria",
    "perla": "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria",
    "strass": "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria",
    "tintura": "/collections/tinturas-pegamentos?filter.p.tag=cat-tinturas",
    "anilina": "/collections/tinturas-pegamentos?filter.p.tag=cat-tinturas",
    "pegamento": "/collections/tinturas-pegamentos?filter.p.tag=cat-pegamentos",
    # Mapeos adicionales detectados en tienda real (colecciones sin match)
    "top-65-favoritos": "/collections/maquinas-y-repuestos",
    "botones": "/collections/insumos-confeccion",
    "catalogo-completo": "/collections/maquinas-y-repuestos",
    "hebillas": "/collections/bisuteria-decoracion?filter.p.tag=cat-argollas",
    "ganchillo": "/collections/tejido-manualidades?filter.p.tag=cat-agujas-tejido",
    "manualidades": "/collections/tejido-manualidades",
    "adhesivo": "/collections/tinturas-pegamentos?filter.p.tag=cat-pegamentos",
    "cascabel": "/collections/bisuteria-decoracion?filter.p.tag=cat-bisuteria",
    "fleco": "/collections/tejido-manualidades?filter.p.tag=cat-pasamaneria",
    "accesorios-maquina": "/collections/maquinas-y-repuestos?filter.p.tag=cat-accesorios-maquina",
    "herramientas-de-costura": "/collections/herramientas-costura",
    "herramientas": "/collections/herramientas-costura",
    "huincha": "/collections/insumos-confeccion?filter.p.tag=cat-cintas",
    "insumos-de-confeccion": "/collections/insumos-confeccion",
    "tejido-y-manualidades": "/collections/tejido-manualidades",
}

# Colecciones que NO se deben redirigir (ya existentes o nuevas)
PROTECTED_HANDLES = {
    "all", "frontpage",
    "prensatelas-industriales", "prensatelas-caseros",
    "maquinas-y-repuestos", "herramientas-costura", "insumos-confeccion",
    "tejido-manualidades", "bisuteria-decoracion", "tinturas-pegamentos",
}
