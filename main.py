"""
Orquestador principal - ejecuta las 4 tareas en orden.
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


def _flush_log(log: dict) -> None:
    """Guarda execution_log.json siempre en la carpeta del proyecto (junto a main.py)."""
    log.setdefault("finished_at", datetime.now().isoformat())
    try:
        with open(_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Se guardo el archivo: {_LOG_FILE}")
    except OSError as ex:
        print(f"[WARN] No se pudo guardar execution_log.json: {ex}")


def main():
    print("=" * 70)
    print("TIENDAS LUPE - RESTRUCTURACION DE NAVEGACION")
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    log = {
        "started_at": datetime.now().isoformat(),
        "tasks": {}
    }
    
    # ── 0. Validar token ─────────────────────────
    print("\n[0/4] Validando token...")
    try:
        shop = validate_token()
        log["shop"] = shop
    except SystemExit as e:
        msg = str(e)
        print(msg)
        log["tasks"]["validation"] = {"status": "error", "message": msg}
        _flush_log(log)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Validacion fallo: {e}")
        log["tasks"]["validation"] = {"status": "error", "error": str(e)}
        _flush_log(log)
        sys.exit(1)
    
    # ── 1. Crear colecciones ─────────────────────
    print("\n[1/4] Creando colecciones automatizadas...")
    print("-" * 70)
    try:
        ids = create_all_collections()
        log["tasks"]["collections"] = {"status": "ok", "ids": ids}
    except Exception as e:
        print(f"[ERROR] Tarea 1 fallo: {e}")
        log["tasks"]["collections"] = {"status": "error", "error": str(e)}
        _flush_log(log)
        sys.exit(1)
    
    # ── 2. Reconstruir menú ──────────────────────
    print("\n[2/4] Reconstruyendo menu principal...")
    print("-" * 70)
    try:
        rebuild_menu()
        log["tasks"]["menu"] = {"status": "ok"}
    except Exception as e:
        print(f"[WARN] Tarea 2 fallo: {e}")
        log["tasks"]["menu"] = {"status": "error", "error": str(e)}
    
    # ── 3. Crear redirects ───────────────────────
    print("\n[3/4] Creando redirects 301...")
    print("-" * 70)
    try:
        result = create_all_redirects()
        log["tasks"]["redirects"] = {"status": "ok", **result}
    except Exception as e:
        print(f"[WARN] Tarea 3 fallo: {e}")
        log["tasks"]["redirects"] = {"status": "error", "error": str(e)}
    
    # ── 4. Reporte de filtros ────────────────────
    print("\n[4/4] Reporte de filtros (configuracion manual):")
    print(generate_filters_report())
    log["tasks"]["filters"] = {"status": "manual_required"}
    
    log["finished_at"] = datetime.now().isoformat()
    
    _flush_log(log)
    
    # Reporte final
    print("\n" + "=" * 70)
    print("[OK] EJECUCION COMPLETADA")
    print("=" * 70)
    print(f"\nTienda: {log['shop']['name']}")
    print(f"Colecciones creadas: {len(log['tasks'].get('collections', {}).get('ids', {}))}")
    
    redirects = log['tasks'].get('redirects', {})
    if redirects.get('status') == 'ok':
        print(f"Redirects creados: {redirects.get('created', 0)}")
    
    print(f"\nLog completo: {_LOG_FILE}")
    print("\nProximos pasos:")
    print(f"   1. Abrir tu tienda y validar el menu nuevo")
    print(f"   2. Configurar los 7 filtros en Search & Discovery (5 min)")
    print(f"   3. Activar 'Habilitar filtrado' en tema Xtra")
    print(f"   4. Esperar 1-2 semanas antes de borrar colecciones viejas")
    print()


if __name__ == "__main__":
    main()
