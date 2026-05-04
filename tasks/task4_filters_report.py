"""
Tarea 4: checklist manual para filtros (Search & Discovery — sin API pública).
"""


def generate_filters_report() -> str:
    return """
⚠️ FILTROS — CONFIGURACIÓN MANUAL REQUERIDA (no hay Admin API para Search & Discovery)

Ir a: Shopify admin → Apps → Search & Discovery → pestaña Filters → «Add filter»

Crear estos 7 filtros en este orden:

┌───┬───────────────────────────────────────┬─────────────────────────┬──────────────────┬─────────┐
│ # │ Source (Product metafield)            │ Filter Label            │ Behavior         │ Display │
├───┼───────────────────────────────────────┼─────────────────────────┼──────────────────┼─────────┤
│ 1 │ custom.marca                          │ Marca                   │ Multiple values  │ List    │
│ 2 │ custom.uso                            │ Tipo de uso             │ Multiple values  │ List    │
│ 3 │ custom.maquinas_compatibles           │ Máquina compatible      │ Multiple values  │ List    │
│ 4 │ custom.material                       │ Material                │ Multiple values  │ List    │
│ 5 │ custom.medida                         │ Medida                  │ Multiple values  │ List    │
│ 6 │ custom.color                          │ Color                   │ Multiple values  │ List    │
│ 7 │ Built-in: Price                       │ Precio                  │ Range            │ Slider  │
└───┴───────────────────────────────────────┴─────────────────────────┴──────────────────┴─────────┘

Después, arrastrar y reordenar a:
  1. Disponibilidad (built-in)
  2. Precio
  3. Marca
  4. Tipo de uso
  5. Máquina compatible
  6. Material
  7. Medida
  8. Color

Activar el toggle del tema:
  Tienda online → Temas → Xtra → Personalizar →
  Páginas: Colección → Predeterminada →
  Sección «Filtros» o «Cuadrícula de productos» → activar «Mostrar filtros» / «Habilitar filtrado» →
  Posición: Sidebar (escritorio) / Drawer (móvil) → Guardar

Tiempo estimado manual: 5–10 minutos
"""


if __name__ == "__main__":
    print(generate_filters_report())
