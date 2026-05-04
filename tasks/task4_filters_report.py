"""
Tarea 4: Reporte para configurar filtros (manual, no hay API publica).
"""

REPORT = """
----------------------------------------------------------------------
[AVISO] FILTROS - CONFIGURACION MANUAL REQUERIDA
----------------------------------------------------------------------

Search & Discovery NO expone API publica para configurar filtros.
Necesitas hacerlo manualmente (5 minutos):

PASO 1: Ir a Apps -> Search & Discovery -> pestana Filters -> Add filter

Crear estos 7 filtros:

  # | Source                              | Filter Label          | Behavior
  --+-------------------------------------+-----------------------+----------------
  1 | Metafield: custom.marca             | Marca                 | Multiple values
  2 | Metafield: custom.uso               | Tipo de uso           | Multiple values
  3 | Metafield: custom.maquinas_compatibles | Maquina compatible | Multiple values
  4 | Metafield: custom.material          | Material              | Multiple values
  5 | Metafield: custom.medida            | Medida                | Multiple values
  6 | Metafield: custom.color             | Color                 | Multiple values
  7 | Built-in: Price                     | Precio                | Range

PASO 2: Reordenar los filtros (drag & drop) en este orden:
  1. Disponibilidad (built-in)
  2. Precio
  3. Marca
  4. Tipo de uso
  5. Maquina compatible
  6. Material
  7. Medida
  8. Color

PASO 3: Activar el toggle del tema:
  Tienda online -> Temas -> Xtra -> Personalizar
  -> Paginas: Coleccion -> Predeterminada
  -> Seccion "Filtros" o "Cuadricula de productos"
  -> Activar "Habilitar filtrado"
  -> Posicion: Sidebar (desktop) / Drawer (movil)
  -> Guardar

----------------------------------------------------------------------
"""


def generate_filters_report() -> str:
    return REPORT


if __name__ == "__main__":
    print(generate_filters_report())
