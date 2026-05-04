# 🚀 Tiendas Lupe — Restructuración Navegación Shopify

Este proyecto crea automáticamente vía API:
- ✅ 6 colecciones automatizadas
- ✅ Menú principal con 8 items + 22 sub-items
- ✅ Redirects 301 para todas las colecciones viejas
- ⚠️ Filtros (manual, 5 min)

---

## 📋 ANTES DE EMPEZAR

Necesitas:
1. ✅ Tu computador con **Python 3.10+** instalado
2. ✅ **Cursor** instalado (https://cursor.com)
3. ✅ **Token API de Shopify** con scopes correctos

---

## 🔑 PASO 1: Crear el Token API en Shopify

1. Shopify admin → **Configuración** → **Aplicaciones y canales de venta**
2. Click **"Desarrollar aplicaciones"** (arriba derecha)
3. Si pregunta "Permitir desarrollo" → **Activar**
4. **"Crear una aplicación"** → Nombre: `Lupe Automation` → **Crear**
5. Pestaña **"Configuración"** → **"Admin API access scopes"** → **"Configurar"**
6. Marcar estos 7 permisos:
   - ✅ `read_products`
   - ✅ `write_products`
   - ✅ `read_publications`
   - ✅ `write_publications`
   - ✅ `read_content`
   - ✅ `write_content`
   - ✅ `read_themes`
7. **Guardar**
8. Pestaña **"Credenciales API"** → **"Instalar aplicación"** → **"Instalar"**
9. **COPIAR** el token (empieza con `shpat_...`) — se muestra UNA SOLA VEZ
10. Pegarlo en un lugar seguro temporalmente

---

## 💻 PASO 2: Abrir el proyecto en Cursor

1. Descarga esta carpeta `lupe-shopify-cursor` y guárdala donde quieras (ej: Escritorio)
2. Abre **Cursor**
3. **File → Open Folder** → selecciona la carpeta `lupe-shopify-cursor`
4. Verás todos los archivos en el panel izquierdo

---

## ⚙️ PASO 3: Configurar el token

1. En Cursor, busca el archivo `.env.example` y **renómbralo a `.env`** (sin el `.example`)
   - Click derecho → Rename → escribe `.env`
2. Abre el archivo `.env`
3. Pega tu token donde dice `PEGA_AQUI_TU_NUEVO_TOKEN`:

```env
SHOP_DOMAIN=0viv7s-w8.myshopify.com
ADMIN_API_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

4. **Guardar** (Ctrl+S / Cmd+S)

---

## 🤖 PASO 4: Pedir a Cursor que ejecute todo

1. En Cursor presiona **Ctrl+L** (Windows) o **Cmd+L** (Mac) para abrir el chat IA
2. Escribe en el chat:

```
Instala las dependencias con pip y ejecuta main.py.
Si pide confirmación para correr comandos, acepta.
```

3. Cursor:
   - Instalará automáticamente `requests` y `python-dotenv`
   - Ejecutará `python main.py`
   - Te mostrará el progreso en vivo

**Si te pide permiso para ejecutar comandos en terminal → click "Allow" o "Run"**

---

## ✅ PASO 5: Validar resultado

Cuando termine verás algo como:

```
======================================================================
✅ EJECUCIÓN COMPLETADA
======================================================================

Tienda: Tiendas Lupe
Colecciones creadas: 6
Redirects creados: N

📄 Log completo: execution_log.json
```

Y un archivo nuevo `execution_log.json` con todos los detalles.

---

## 🔍 PASO 6: Verificar en Shopify

1. Entra a tu tienda online: `tiendaslupe.cl`
2. Verifica:
   - El menú principal tiene **8 items** (Inicio, Máquinas y Repuestos, Herramientas, etc.)
   - Hover sobre "Máquinas y Repuestos" → muestra dropdown con 5 sub-items
   - Click en "Agujas" → te lleva a la colección filtrada

---

## ⚠️ ÚLTIMO PASO MANUAL: Filtros (5 min)

Los filtros laterales NO se pueden automatizar (Shopify no expone API).
Hazlo así:

**Apps → Search & Discovery → pestaña "Filters" → "Add filter"**

Crea estos 7 filtros (uno por uno):

| Source | Label | Behavior |
|---|---|---|
| Metafield: `custom.marca` | Marca | Multiple values |
| Metafield: `custom.uso` | Tipo de uso | Multiple values |
| Metafield: `custom.maquinas_compatibles` | Máquina compatible | Multiple values |
| Metafield: `custom.material` | Material | Multiple values |
| Metafield: `custom.medida` | Medida | Multiple values |
| Metafield: `custom.color` | Color | Multiple values |
| Built-in: Price | Precio | Range |

Después: **Tienda online → Temas → Xtra → Personalizar → Páginas Colección → activar "Habilitar filtrado"**

---

## 🆘 SI ALGO FALLA

- **"Token inválido"** → revisa el token en `.env` (debe empezar con `shpat_`)
- **"Permisos insuficientes"** → revisa los 7 scopes en la app de Shopify
- **"No se conecta"** → verifica el `SHOP_DOMAIN` (debe terminar en `.myshopify.com`)
- **Otro error** → muéstrame el mensaje completo y te ayudo

---

## 🔒 SEGURIDAD POST-EJECUCIÓN

Cuando todo termine y verifiques que funciona:

1. Shopify admin → Configuración → Aplicaciones
2. Buscar **"Lupe Automation"**
3. **Desinstalar** (revoca el token, ya no es útil)

---

## 📁 ESTRUCTURA DEL PROYECTO

```
lupe-shopify-cursor/
├── .env                       ← TÚ pones tu token aquí
├── .env.example               ← Plantilla
├── README.md                  ← Este archivo
├── requirements.txt           ← Dependencias Python
├── config.py                  ← Datos de colecciones, menú, redirects
├── shopify_client.py          ← Cliente HTTP con retry
├── main.py                    ← Ejecuta TODO
└── tasks/
    ├── task1_collections.py   ← Crear 6 colecciones
    ├── task2_menu.py          ← Reconstruir menú
    ├── task3_redirects.py     ← Crear redirects 301
    └── task4_filters_report.py ← Reporte filtros (manual)
```
