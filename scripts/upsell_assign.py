"""
Asigna custom.upsell_collection a cada producto basÃƒÂ¡ndose en las colecciones
a las que ya pertenece (no en palabras del tÃƒÂ­tulo).

Uso:
    python scripts/upsell_assign.py --dry-run    # muestra el plan sin tocar nada
    python scripts/upsell_assign.py --apply      # aplica los cambios
"""
import sys
import time
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from shopify_client import REST_BASE, HEADERS
import requests

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# GRUPOS DE TÃƒâ€°CNICA Ã¢â‚¬â€ cross-sell solo dentro del mismo grupo
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 1: Costura MÃƒÂ¡quina Casera Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# aguja casera Ã¢â€ â€ hilos caseros Ã¢â€ â€ prensatelas caseros Ã¢â€ â€ repuestos

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 2: Costura MÃƒÂ¡quina Industrial Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# aguja industrial Ã¢â€ â€ hilo overlock Ã¢â€ â€ prensatelas industriales

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 3: Bordado Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# hilos bordar Ã¢â€ â€ bastidores Ã¢â€ â€ agujas mano

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 4: Tejido / Crochet Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# lanas Ã¢â€ â€ agujas crochet/palillos Ã¢â€ â€ trapillo

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 5: Insumos ConfecciÃƒÂ³n Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# cierres Ã¢â€ â€ entretelas Ã¢â€ â€ elasticos Ã¢â€ â€ botones Ã¢â€ â€ sesgo Ã¢â€ â€ broches

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 6: Herramientas de Corte Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# tijeras Ã¢â€ â€ herramientas Ã¢â€ â€ cortadoras Ã¢â€ â€ repuestos cortadoras

# Ã¢â€â‚¬Ã¢â€â‚¬ Grupo 7: DecoraciÃƒÂ³n / Manualidades Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
# bisuterÃƒÂ­a Ã¢â€ â€ lentejuelas Ã¢â€ â€ pasamanerÃƒÂ­a Ã¢â€ â€ cordones Ã¢â€ â€ tinturas

# Prioridad: colecciÃƒÂ³n mÃƒÂ¡s especÃƒÂ­fica gana cuando un producto pertenece a varias
PRIORITY = [
    # G1 - Casera (hilos primero para que un hilo no sea confundido con aguja)
    "hilo-5000",
    "hilo-2000",
    "aguja-maquina-casera",
    "prensatelas-caseros",
    "prensatelas-para-maquina-de-cos",
    # G2 - Industrial
    "hilo-overlock",
    "hilo-poliamida",
    "hilo-de-saco",
    "aguja-maquina-industrial",
    "prensatelas-industriales-1",
    "prensatelas-industriales",
    # G3 - Bordado
    "hilos-bordar-profesionales",
    "bastidores-bordado",
    "agujas-mano",
    # G4 - Tejido / Crochet
    "lanas-ovillos-crochet-tejido",
    "agujas-crochet-y-tejido",
    "crochet-accessories-ganchillos",
    "trapillo-telas-crochet",
    # G5 - Insumos confecciÃƒÂ³n
    "cierres",
    "entretelas",
    "elasticos-costura",
    "botones",
    "sesgo-bies",
    "broches",
    "hebillas",
    "velcro",
    "adhesivos-telas",
    "cintas-algodon",
    "cintas-satin",
    "huincha-mochila",
    "alfileres",
    # G6 - Herramientas
    "cortadoras-de-tela-circulares",
    "repuestos-de-cortadoras-de-telas",
    "tijeras-profesionales-para-costura",
    "herramientas-de-costura",
    "herramientas-costura",
    "herramientas",
    # G7 - DecoraciÃƒÂ³n / Manualidades
    "bisuteria-y-decoracion",
    "bisuteria-decoracion",
    "lentejuelas-y-strass",
    "pasamaneria",
    "flecos-decorativos",
    "cascabeles-costura-manualidades",
    "argollas-manualidades",
    "cuencas-madera",
    "macrame-cordon-trenzado",
    "cordones-zapatos-costura-manualidades",
    "tinturas",
    "tinturas-y-pegamentos",
    "tinturas-pegamentos",
    # MÃƒÂ¡quinas / repuestos / planchas
    "maquinas-y-repuestos",
    "accesorios-maquina",
    "repuestos-maquinas-de-coser",
    "planchas-a-vapor-industrial",
]

CROSS_SELL = {
    # Ã¢â€â‚¬Ã¢â€â‚¬ G1: Costura MÃƒÂ¡quina Casera Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "hilo-2000":                        "aguja-maquina-casera",
    "hilo-5000":                        "aguja-maquina-casera",
    "aguja-maquina-casera":             "hilo-2000",
    "prensatelas-caseros":              "aguja-maquina-casera",
    "prensatelas-para-maquina-de-cos":  "hilo-2000",
    "repuestos-maquinas-de-coser":      "aguja-maquina-casera",
    "accesorios-maquina":               "aguja-maquina-casera",
    "maquinas-y-repuestos":             "repuestos-maquinas-de-coser",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G2: Costura MÃƒÂ¡quina Industrial Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "hilo-overlock":                    "aguja-maquina-industrial",
    "hilo-poliamida":                   "aguja-maquina-industrial",
    "hilo-de-saco":                     "aguja-maquina-industrial",
    "aguja-maquina-industrial":         "hilo-jeans",
    "prensatelas-industriales":         "aguja-maquina-industrial",
    "prensatelas-industriales-1":       "hilo-overlock",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G3: Bordado Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "hilos-bordar-profesionales":       "bastidores-bordado",
    "bastidores-bordado":               "hilos-bordar-profesionales",
    "agujas-mano":                      "hilos-bordar-profesionales",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G4: Tejido / Crochet Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "lanas-ovillos-crochet-tejido":     "agujas-crochet-y-tejido",
    "agujas-crochet-y-tejido":          "lanas-ovillos-crochet-tejido",
    "crochet-accessories-ganchillos":   "lanas-ovillos-crochet-tejido",
    "trapillo-telas-crochet":           "agujas-crochet-y-tejido",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G5: Insumos ConfecciÃƒÂ³n Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "cierres":                          "entretelas",
    "entretelas":                       "cierres",
    "adhesivos-telas":                  "entretelas",
    "elasticos-costura":                "botones",
    "botones":                          "elasticos-costura",
    "broches":                          "botones",
    "hebillas":                         "elasticos-costura",
    "velcro":                           "elasticos-costura",
    "sesgo-bies":                       "cierres",
    "cintas-algodon":                   "sesgo-bies",
    "cintas-satin":                     "sesgo-bies",
    "huincha-mochila":                  "elasticos-costura",
    "alfileres":                        "herramientas-de-costura",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G6: Herramientas de Corte Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "cortadoras-de-tela-circulares":    "repuestos-de-cortadoras-de-telas",
    "repuestos-de-cortadoras-de-telas": "cortadoras-de-tela-circulares",
    "tijeras-profesionales-para-costura": "herramientas-de-costura",
    "herramientas-de-costura":          "tijeras-profesionales-para-costura",
    "herramientas-costura":             "tijeras-profesionales-para-costura",
    "herramientas":                     "tijeras-profesionales-para-costura",
    "planchas-a-vapor-industrial":      "herramientas-de-costura",

    # Ã¢â€â‚¬Ã¢â€â‚¬ G7: DecoraciÃƒÂ³n / Manualidades Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
    "bisuteria-y-decoracion":           "lentejuelas-y-strass",
    "bisuteria-decoracion":             "lentejuelas-y-strass",
    "lentejuelas-y-strass":             "bisuteria-y-decoracion",
    "flecos-decorativos":               "pasamaneria",
    "pasamaneria":                      "flecos-decorativos",
    "cascabeles-costura-manualidades":  "bisuteria-y-decoracion",
    "argollas-manualidades":            "bisuteria-y-decoracion",
    "cuencas-madera":                   "bisuteria-y-decoracion",
    "macrame-cordon-trenzado":          "materiales-para-manualidades",
    "cordones-zapatos-costura-manualidades": "materiales-para-manualidades",
    "tinturas":                         "herramientas-de-costura",
    "tinturas-y-pegamentos":            "tinturas",
    "tinturas-pegamentos":              "tinturas",
}

# Sin match especÃƒÂ­fico Ã¢â€ â€™ no asignar (evita mezclar catÃƒÂ¡logo completo)
DEFAULT_UPSELL = None

# Colecciones genÃƒÂ©ricas que no sirven para cross-sell Ã¢â‚¬â€ ignorar al hacer match
EXCLUDE_FROM_MATCHING = {
    "top-65-favoritos",
    "catalogo-completo",
    "insumos-de-confeccion",
    "insumos-confeccion",
    "materiales-para-manualidades",
    "tejido-y-manualidades",
    "tejido-manualidades",
}


# Ã¢â€â‚¬Ã¢â€â‚¬ Helpers Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

def paginate(path, key, **params):
    items = []
    params.setdefault("limit", 250)
    url = f"{REST_BASE}/{path}"
    while url:
        r = requests.get(url, headers=HEADERS, params=params, timeout=45)
        r.raise_for_status()
        items += r.json().get(key, [])
        link = r.headers.get("Link", "")
        url = None
        params = {}
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return items


# Ã¢â€â‚¬Ã¢â€â‚¬ Fetch data Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

print("Ã°Å¸â€Â Obteniendo colecciones...")
custom_cols = paginate("custom_collections.json", "custom_collections", fields="id,handle,title")
smart_cols  = paginate("smart_collections.json",  "smart_collections",  fields="id,handle,title")
all_cols    = custom_cols + smart_cols
cols_by_handle = {c["handle"]: c for c in all_cols}
cols_by_id     = {c["id"]: c for c in all_cols}
print(f"   {len(all_cols)} colecciones")

print("Ã°Å¸â€Â Obteniendo productos...")
products = paginate("products.json", "products", fields="id,title,handle")
print(f"   {len(products)} productos")

# collects.json solo cubre colecciones manuales; para smart collections
# hay que consultar cada colecciÃƒÂ³n individualmente.
print("Ã°Å¸â€Â Mapeando productos por colecciÃƒÂ³n (manual + smart)...")
from collections import defaultdict
prod_cols: dict[int, list[str]] = defaultdict(list)
total_rels = 0
for col in all_cols:
    col_products = paginate(
        f"collections/{col['id']}/products.json", "products",
        fields="id", limit=250,
    )
    for p in col_products:
        prod_cols[p["id"]].append(col["handle"])
        total_rels += 1
    time.sleep(0.15)  # evitar rate limit
print(f"   {total_rels} relaciones (manual + smart)")


# Ã¢â€â‚¬Ã¢â€â‚¬ Asignar upsell Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

# Override por tÃƒÂ­tulo: mÃƒÂ¡s especÃƒÂ­fico que colecciÃƒÂ³n (ej: bordadora dentro de industrial)
TITLE_OVERRIDES = [
    (["jeans", "coser jeans", "hilo de pesca"], "hilo-jeans"),
    (["plancha de aguja", "plancha aguja", "guarda aguja", "devanadora", "ampolleta"], "repuestos-maquinas-de-coser"),
    (["llave allen", "pinza de preci", "lubricador", "zurcido", "protector de dedo"], "repuestos-maquinas-de-coser"),
    (["crochet para m", "siruba"], "repuestos-maquinas-de-coser"),
    (["correa dentada", "correa para maquina", "cana para prensatela", "guia de hilo"], "repuestos-maquinas-de-coser"),
    (["bissel", "aguja doble"], "aguja-maquina-casera"),
    (["f6000", "pegamento para tela", "adhesivo para tela"], "materiales-para-manualidades"),
    (["bordadora", "bordado", "dbk"], "hilos-bordar-profesionales"),
    (["schmetz", "singer"], "hilo-2000"),
    (["groz", "beckert", "gb "], "hilo-overlock"),
    (["macram"], "macrame-cordon-trenzado"),
    (["palillo", "circular de acero"], "lanas-ovillos-crochet-tejido"),
    (["lana "], "lanas-ovillos-crochet-tejido"),
    (["hilo coser", "industrial gris"], "hilo-2000"),
]

def best_upsell_handle(product_id: int, title: str = "") -> str | None:
    t = title.lower()
    # 1. Override por tÃƒÂ­tulo (mÃƒÂ¡s especÃƒÂ­fico)
    for keywords, handle in TITLE_OVERRIDES:
        if any(k in t for k in keywords) and handle in cols_by_handle:
            return handle
    # 2. Por colecciÃƒÂ³n con prioridad
    handles = set(prod_cols.get(product_id, [])) - EXCLUDE_FROM_MATCHING
    ordered = [h for h in PRIORITY if h in handles] + [h for h in handles if h not in PRIORITY]
    for h in ordered:
        target = CROSS_SELL.get(h)
        if target and target in cols_by_handle:
            return target
    if DEFAULT_UPSELL and DEFAULT_UPSELL in cols_by_handle:
        return DEFAULT_UPSELL
    return None


# Sugerencia de colecciÃƒÂ³n para los sin asignar (por palabras en el tÃƒÂ­tulo)
TITLE_SUGGESTIONS = [
    (["palillo"],                                   "agujas-crochet-y-tejido"),
    (["aceitera", "aceite", "ampolleta", "foco"],   "repuestos-maquinas-de-coser"),
    (["bobina", "lanzadera", "canilla"],             "repuestos-maquinas-de-coser"),
    (["bastidor"],                                   "bastidores-bordado"),
    (["macramÃƒÂ©", "macram", "cordÃƒÂ³n trenzado", "cordon trenzado"], "macrame-cordon-trenzado"),
    (["cordÃƒÂ³n", "cordon"],                           "cordones-zapatos-costura-manualidades"),
    (["tijera", "descosedor"],                       "herramientas-de-costura"),
    (["cinta", "sesgo", "bies"],                     "cierres"),
    (["elÃƒÂ¡stico", "elastico"],                       "elasticos-costura"),
    (["botÃƒÂ³n", "boton"],                             "botones"),
    (["hilo overlock", "overlock"],                  "hilo-overlock"),
    (["hilo bordar", "bordar"],                      "hilos-bordar-profesionales"),
    (["hilo"],                                       "hilo-2000"),
    (["aguja mano", "aguja a mano"],                 "agujas-mano"),
    (["schmetz", "singer"],                          "aguja-maquina-casera"),
    (["groz", "beckert", "industrial"],              "aguja-maquina-industrial"),
    (["aguja"],                                      "aguja-maquina-casera"),
    (["lana", "ovillo"],                             "lanas-ovillos-crochet-tejido"),
    (["cierre", "cremallera"],                       "cierres"),
    (["entretela"],                                  "entretelas"),
    (["tintura", "anilina"],                         "tinturas"),
    (["broche"],                                     "broches"),
    (["hebilla"],                                    "hebillas"),
    (["repuesto", "accesorio maquina"],              "repuestos-maquinas-de-coser"),
]

def suggest_by_title(title: str) -> str:
    t = title.lower()
    for keywords, handle in TITLE_SUGGESTIONS:
        if any(k in t for k in keywords):
            if handle in cols_by_handle:
                return handle
    return "Ã¢â‚¬â€ sin sugerencia Ã¢â‚¬â€"


plan = []
unmatched = []
for p in products:
    target_handle = best_upsell_handle(p["id"], p.get("title", ""))
    if target_handle:
        plan.append((p, cols_by_handle[target_handle]))
    else:
        unmatched.append(p)

print(f"Ã°Å¸â€œÂ¦ Plan: {len(plan)} productos asignados / {len(unmatched)} sin colecciÃƒÂ³n upsell")
print()

# Muestra muestra del plan
for p, col in plan[:40]:
    src_handles = ", ".join(prod_cols.get(p["id"], ["?"]))
    print(f"   {p['title'][:42]:42s} [{src_handles[:30]}] Ã¢â€ â€™ {col['handle']}")
if len(plan) > 40:
    print(f"   ... y {len(plan)-40} mÃƒÂ¡s")
print()

if unmatched:
    print(f"Ã¢Å¡Â Ã¯Â¸Â  Sin asignar ({len(unmatched)}) Ã¢â‚¬â€ agregar a la colecciÃƒÂ³n sugerida en Shopify Admin:")
    print(f"   {'Producto':50s}  {'ColecciÃƒÂ³n sugerida'}")
    print(f"   {'-'*50}  {'-'*35}")
    for p in unmatched:
        suggestion = suggest_by_title(p["title"])
        print(f"   {p['title'][:50]:50s}  {suggestion}")
    print()

# Ã¢â€â‚¬Ã¢â€â‚¬ Aplicar Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply",   action="store_true")
args = parser.parse_args()

if args.dry_run or not args.apply:
    print("Ã¢â€žÂ¹Ã¯Â¸Â  Modo dry-run. Corre con --apply para guardar los cambios.")
    sys.exit(0)

print("Ã°Å¸Å¡â‚¬ Aplicando metafields...")
ok = err = 0
for p, col in plan:
    col_handle = col["handle"]

    # Buscar si ya existe el metafield
    existing = requests.get(
        f"{REST_BASE}/products/{p['id']}/metafields.json",
        headers=HEADERS,
        params={"namespace": "custom", "key": "upsell_collection"},
        timeout=30,
    ).json().get("metafields", [])

    if existing:
        mf_id = existing[0]["id"]
        r = requests.put(
            f"{REST_BASE}/products/{p['id']}/metafields/{mf_id}.json",
            headers=HEADERS,
            json={"metafield": {"id": mf_id, "value": col_handle, "type": "single_line_text_field"}},
            timeout=30,
        )
        verb = "Ã¢â€ Â©Ã¯Â¸Â "
    else:
        r = requests.post(
            f"{REST_BASE}/products/{p['id']}/metafields.json",
            headers=HEADERS,
            json={"metafield": {
                "namespace": "custom",
                "key": "upsell_collection",
                "type": "single_line_text_field",
                "value": col_handle,
                "owner_id": p["id"],
                "owner_resource": "product",
            }},
            timeout=30,
        )
        verb = "Ã¢Å“â€¦ "

    if r.status_code in (200, 201):
        print(f"  {verb}{p['title'][:45]:45s} Ã¢â€ â€™ {col['handle']}")
        ok += 1
    else:
        print(f"  Ã¢ÂÅ’ {p['title'][:45]} Ã¢â‚¬â€ HTTP {r.status_code}: {r.text[:120]}")
        err += 1

    time.sleep(0.25)

print()
print(f"Ã¢Å“â€¦ {ok} asignados / Ã¢ÂÅ’ {err} errores")


