"""
Orquestador — ejecuta las 4 tareas del PROMPT (colecciones, menú, redirects, informe filtros).
"""
import json
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_LOG_FILE = _ROOT / "execution_log.json"

from shopify_client import validate_token
from tasks.task1_collections import create_all_collections
from tasks.task2_menu import rebuild_menu
from tasks.task3_redirects import create_all_redirects
from tasks.task4_filters_report import generate_filters_report


def _save_log(log: dict) -> None:
    log.setdefault("finished_at", datetime.now().isoformat())
    try:
        with open(_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        print(f"📄 Log guardado: {_LOG_FILE}")
    except OSError as ex:
        print(f"⚠️ No se pudo guardar execution_log.json: {ex}")


def main():
    print("=" * 70)
    print("TIENDAS LUPE — SHOPIFY NAVIGATION RESTRUCTURE")
    print(f"Inicio: {datetime.now().isoformat()}")
    print("=" * 70)

    log: dict = {"started_at": datetime.now().isoformat()}

    print("\n[0/4] Validando token...")
    try:
        shop = validate_token()
        log["shop"] = shop
    except Exception as e:
        print(f"❌ Validación de token falló: {e}")
        log["task0_error"] = str(e)
        _save_log(log)
        sys.exit(1)

    print("\n[1/4] Creando colecciones...")
    try:
        collection_ids = create_all_collections()
        log["collection_ids"] = collection_ids
    except Exception as e:
        print(f"❌ Tarea 1 falló: {e}")
        log["task1_error"] = str(e)
        _save_log(log)
        sys.exit(1)

    print("\n[2/4] Reconstruyendo menú principal...")
    try:
        rebuild_menu()
        log["menu_result"] = "success"
    except Exception as e:
        print(f"⚠️ Tarea 2 falló: {e}")
        log["task2_error"] = str(e)

    print("\n[3/4] Creando redirects 301...")
    try:
        redirect_result = create_all_redirects()
        log["redirects"] = redirect_result
    except Exception as e:
        print(f"⚠️ Tarea 3 falló: {e}")
        log["task3_error"] = str(e)

    print("\n[4/4] Informe de filtros (configuración manual):")
    print(generate_filters_report())
    log["filters"] = "manual_required"

    log["finished_at"] = datetime.now().isoformat()
    _save_log(log)

    print("\n" + "=" * 70)
    print("✅ EJECUCIÓN COMPLETADA — TIENDAS LUPE")
    print("=" * 70)
    print("""
📦 Colecciones: script ejecutado (idempotente; revisa collection_ids en el log)
🧭 Menú principal: reconstruido si la tarea 2 terminó sin error
🔄 Redirects 301: revisa el objeto «redirects» en execution_log.json
⚠️ Filtros laterales: ~5 min de configuración manual (instrucciones arriba)

Próximos pasos:
1. Visitar tiendaslupe.cl y validar navegación
2. Configurar 7 filtros en Search & Discovery (~5 min)
3. Activar «Habilitar filtrado» en tema Xtra
4. Esperar 1–2 semanas antes de borrar colecciones viejas (SEO)
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por el usuario.")
        sys.exit(130)
