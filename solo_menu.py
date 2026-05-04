"""
Solo actualiza el menu (tarea 2). No toca colecciones ni redirects.
Uso: doble clic en SOLO_MENU.bat o: python solo_menu.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shopify_client import validate_token
from tasks.task2_menu import rebuild_menu


def main() -> None:
    print("=" * 60)
    print("SOLO MENU - Tiendas Lupe")
    print("=" * 60)
    print("\n[0] Validando token...")
    validate_token()
    print("\n[1] Reconstruyendo menu principal...")
    rebuild_menu()
    print("\n[OK] Proceso de menu finalizado. Revisa la tienda en el navegador.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise SystemExit(1) from e
