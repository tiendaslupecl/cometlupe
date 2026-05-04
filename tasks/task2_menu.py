"""
Tarea 2: Reconstruir el menu principal.
1) Intenta REST (requiere permiso de API para menus - a veces 403).
2) Si falla, usa GraphQL menuUpdate (requiere read/write Online Store navigation).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_client import graphql, rest
from config import MENU_STRUCTURE

MENUS_GQL = """
query menusList {
  menus(first: 25) {
    nodes { id handle title }
  }
}
"""

MENU_UPDATE = """
mutation menuUpdateMain(
  $id: ID!
  $title: String!
  $handle: String!
  $items: [MenuItemUpdateInput!]!
) {
  menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
    menu { id handle }
    userErrors { field message }
  }
}
"""


def find_main_menu() -> dict:
    """Busca el menu con handle 'main-menu' (REST)."""
    data = rest("GET", "/menus.json")
    for menu in data.get("menus", []):
        if menu["handle"] == "main-menu":
            return menu
    raise RuntimeError("Menu 'main-menu' no encontrado")


def find_page_id(handle: str) -> int | None:
    data = rest("GET", f"/pages.json?handle={handle}")
    pages = data.get("pages", [])
    return pages[0]["id"] if pages else None


def find_collection_id_numeric(handle: str) -> int | None:
    q = """
    query($handle: String!) {
      collectionByHandle(handle: $handle) { id }
    }
    """
    data = graphql(q, {"handle": handle})
    if data.get("collectionByHandle"):
        gid = data["collectionByHandle"]["id"]
        return int(str(gid).split("/")[-1])
    return None


def find_collection_gid(handle: str) -> str | None:
    q = """
    query($handle: String!) {
      collectionByHandle(handle: $handle) { id }
    }
    """
    data = graphql(q, {"handle": handle})
    col = data.get("collectionByHandle")
    return col["id"] if col else None


def find_page_gid(handle: str) -> str | None:
    q = """
    query($q: String!) {
      pages(first: 1, query: $q) {
        nodes { id handle }
      }
    }
    """
    data = graphql(q, {"query": f"handle:{handle}"})
    nodes = data.get("pages", {}).get("nodes", [])
    return nodes[0]["id"] if nodes else None


def _store_base_url() -> str:
    """URL base del escaparate para enlaces HTTP (submenus)."""
    env = (os.getenv("STORE_PRIMARY_URL") or "").strip().rstrip("/")
    if env:
        return env
    q = """
    query {
      shop { primaryDomain { url } }
    }
    """
    data = graphql(q)
    url = data.get("shop", {}).get("primaryDomain", {}).get("url") or ""
    return str(url).rstrip("/")


def build_menu_items_rest(structure: list) -> list:
    items = []
    for entry in structure:
        if entry["type"] == "FRONTPAGE":
            item = {"title": entry["title"], "type": "frontpage", "subject": ""}
        elif entry["type"] == "COLLECTION":
            cid = find_collection_id_numeric(entry["handle"])
            if cid is None:
                print(f"[WARN] Coleccion '{entry['handle']}' no existe, saltando")
                continue
            item = {"title": entry["title"], "type": "collection", "subject": str(cid)}
        elif entry["type"] == "PAGE":
            pid = find_page_id(entry["page_handle"])
            if pid is None:
                print(f"[WARN] Pagina '{entry['page_handle']}' no existe, saltando")
                continue
            item = {"title": entry["title"], "type": "page", "subject": str(pid)}
        else:
            continue

        if "items" in entry:
            item["items"] = [
                {"title": title, "type": "http", "subject": url}
                for title, url in entry["items"]
            ]
        items.append(item)
    return items


def build_menu_items_graphql(structure: list, base_url: str) -> list:
    """MenuItemUpdateInput para menuUpdate (submenus como HTTP con URL absoluta)."""
    items: list = []
    for entry in structure:
        if entry["type"] == "FRONTPAGE":
            items.append({"title": entry["title"], "type": "FRONT_PAGE", "items": []})
        elif entry["type"] == "COLLECTION":
            rid = find_collection_gid(entry["handle"])
            if rid is None:
                print(f"[WARN] Coleccion '{entry['handle']}' no existe, saltando")
                continue
            node = {
                "title": entry["title"],
                "type": "COLLECTION",
                "resourceId": rid,
                "items": [],
            }
            if entry.get("items"):
                path_urls = []
                for title, path in entry["items"]:
                    path = path.strip()
                    if path.startswith("http"):
                        full = path
                    else:
                        full = f"{base_url}{path}" if path.startswith("/") else f"{base_url}/{path}"
                    path_urls.append(
                        {"title": title, "type": "HTTP", "url": full, "items": []}
                    )
                node["items"] = path_urls
            items.append(node)
        elif entry["type"] == "PAGE":
            pid = find_page_gid(entry["page_handle"])
            if pid is None:
                print(f"[WARN] Pagina '{entry['page_handle']}' no existe, saltando")
                continue
            items.append(
                {
                    "title": entry["title"],
                    "type": "PAGE",
                    "resourceId": pid,
                    "items": [],
                }
            )
    return items


def rebuild_menu_rest() -> None:
    menu = find_main_menu()
    print(f"[INFO] Menu encontrado (REST): {menu['title']} (ID: {menu['id']})")
    print(f"   Items actuales: {len(menu.get('items', []))}")

    new_items = build_menu_items_rest(MENU_STRUCTURE)
    payload = {
        "menu": {
            "id": menu["id"],
            "title": menu["title"],
            "handle": menu["handle"],
            "items": new_items,
        }
    }
    rest("PUT", f"/menus/{menu['id']}.json", payload)
    sub_count = sum(len(i.get("items", [])) for i in new_items)
    print(f"[OK] Menu reconstruido (REST): {len(new_items)} items + {sub_count} sub-items")


def rebuild_menu_graphql() -> None:
    data = graphql(MENUS_GQL)
    nodes = data.get("menus", {}).get("nodes", [])
    target = next((m for m in nodes if m.get("handle") == "main-menu"), None)
    if not target:
        raise RuntimeError("No se encontro menu con handle main-menu (GraphQL)")

    base = _store_base_url()
    if not base:
        raise RuntimeError(
            "No se pudo obtener la URL de la tienda. Agrega en .env una linea como:\n"
            "STORE_PRIMARY_URL=https://www.tiendaslupe.cl"
        )

    gql_items = build_menu_items_graphql(MENU_STRUCTURE, base)
    result = graphql(
        MENU_UPDATE,
        {
            "id": target["id"],
            "title": target["title"],
            "handle": target["handle"],
            "items": gql_items,
        },
    )
    payload = result.get("menuUpdate") or {}
    errs = payload.get("userErrors") or []
    if errs:
        raise RuntimeError(f"menuUpdate userErrors: {errs}")

    sub_count = sum(len(i.get("items", [])) for i in gql_items)
    print(
        f"[OK] Menu reconstruido (GraphQL): {len(gql_items)} items + {sub_count} sub-items"
    )


def rebuild_menu() -> None:
    """
    Primero REST; si 403 (scopes menus) o fallo, GraphQL.
    Necesitas en la app de Shopify permisos de navegacion, por ejemplo:
    read_online_store_navigation, write_online_store_navigation
    (en Admin suele llamarse 'Online Store navigation').
    """
    try:
        rebuild_menu_rest()
        return
    except Exception as e:
        msg = str(e)
        print(f"[WARN] REST no disponible o fallo: {msg[:400]}")
        if "403" in msg or "menus" in msg.lower() or "Scope" in msg:
            print("[INFO] Probando GraphQL menuUpdate (mismo permiso de navegacion tienda online)...")
        else:
            print("[INFO] Probando GraphQL menuUpdate como respaldo...")

    rebuild_menu_graphql()


if __name__ == "__main__":
    print("=" * 60)
    print("TAREA 2: Reconstruir menu principal")
    print("=" * 60)
    rebuild_menu()
