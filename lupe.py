"""CLI unificado para tiendaslupe.cl"""
import sys, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"

COMMANDS = {
 ("audit","404"):          ("audit_404_full.py",            "404s reales en productos/colecciones/paginas"),
 ("audit","catalog"):      ("catalog_audit.py",             "Duplicados y colecciones vacias"),
 ("audit","intruders"):    ("audit_collection_intruders.py","Productos mal categorizados por coleccion"),
 ("audit","products"):     ("verify_product_collections.py","Cada producto en su coleccion correcta"),
 ("audit","store"):        ("audit_store_404.py",           "Audit integral menu/colecciones/paginas"),
 ("fix","404"):            ("fix_404s.py",                  "Arregla 404s del menu"),
 ("fix","duplicates"):     ("fix_duplicate_collections.py", "Elimina colecciones duplicadas"),
 ("fix","maquinas"):       ("fix_maquinas_repuestos.py",    "Redistribuye catch-all maquinas-y-repuestos"),
 ("fix","agujas"):         ("reorg_agujas_products.py",     "Reorganiza agujas casera/industrial"),
 ("fix","agujas-extra"):   ("fix_agujas_followup.py",       "Follow-up agujas"),
 ("fix","accesorios"):     ("fix_accesorios_maquina_rule.py","Smart rule de accesorios-maquina"),
 ("fix","smart-rules"):    ("fix_smart_collection_rules.py","Reglas smart de prensatelas/agujas-mano"),
 ("fix","expand-rules"):   ("expand_smart_rules.py",        "Expande reglas smart"),
 ("fix","products"):       ("fix_product_collections.py",   "Fixes de productos puntuales"),
 ("fix","menu-urls"):      ("fix_menu_filter_urls.py",      "Reemplaza filter.p.tag por colecciones"),
 ("fix","agujas-tag"):     ("clean_agujas_tag.py",          "Limpia tag cat-agujas-maquina"),
 ("fix","snippets"):       ("fix_snippet_injection.py",     "Reinyecta snippets en el tema"),
 ("menu","add-manualidades"):("add_manualidades_menu.py",   "Agrega Manualidades al menu"),
 ("menu","aguja-mano"):    ("add_aguja_mano_to_herramientas.py","Aguja de mano en herramientas-de-costura"),
 ("check","tags"):         ("check_tags.py",                "Tags por producto"),
 ("check","navigation"):   ("check_navigation.py",          "Estructura del menu principal"),
 ("check","agujas-filter"):("check_agujas_filter.py",       "Que muestra el filtro de agujas"),
 ("check","deliverytime"): ("check_deliverytime.py",        "Productos sin tiempo de entrega"),
 ("check","injection"):    ("check_injection.py",           "Verifica inyeccion de snippets"),
 ("check","contact"):      ("find_contact_page.py",         "Pagina de contacto"),
 ("check","mixed-stock"):  ("find_mixed_inventory_product.py","Stock mixto"),
 ("theme","push-snippets"):("theme_push_snippets_only.py",  "Sube snippets al tema live"),
 ("theme","push-live"):    ("theme_push_live_id.py",        "Sube tema live por ID"),
 ("theme","inject-whatsapp"):("theme_inject_whatsapp.py",   "Inyecta widget WhatsApp"),
}

def list_all():
    print("Comandos disponibles:\n")
    groups = {}
    for (g,c),(_,d) in COMMANDS.items():
        groups.setdefault(g,[]).append((c,d))
    for g in ("audit","fix","menu","check","theme"):
        if g not in groups: continue
        print(f"  {g.upper()}")
        for c,d in sorted(groups[g]):
            print(f"    python lupe.py {g} {c:20s}  {d}")
        print()
    print("Tip: agrega --apply a los comandos fix (sin eso es dry-run).")

def main():
    if len(sys.argv)<2 or sys.argv[1] in ("list","-h","--help","help"):
        list_all(); return 0
    if len(sys.argv)<3:
        print("Uso: python lupe.py <grupo> <comando>"); return 1
    g,c = sys.argv[1], sys.argv[2]
    key = (g,c)
    if key not in COMMANDS:
        print(f"Comando desconocido: {g} {c}. Corre 'python lupe.py list'."); return 1
    script,desc = COMMANDS[key]
    sp = SCRIPTS / script
    if not sp.exists():
        print(f"Script no existe: {sp}"); return 2
    print(f"==> {g} {c}: {desc}\n    ejecutando scripts/{script}\n")
    return subprocess.call([sys.executable, str(sp), *sys.argv[3:]])

if __name__=="__main__":
    sys.exit(main())
