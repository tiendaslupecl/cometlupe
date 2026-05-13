"""
Genera flows corregidos a partir del ZIP exportado de Shopify Flow.
Uso: python scripts/fix_flows.py workflows_export_*.zip
"""
import json, copy, re, sys, zipfile
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python scripts/fix_flows.py <archivo.zip>")
    sys.exit(1)

zpath = sys.argv[1]
out_dir = Path("flows_fixed")
out_dir.mkdir(exist_ok=True)

def load(zf, name):
    raw = zf.read(name).decode("utf-8")
    start = raw.find("{")
    prefix = raw[:start]
    return prefix, json.loads(raw[start:])

def save(prefix, d, path):
    path.write_text(prefix + json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(f"  Guardado: {path}")

with zipfile.ZipFile(zpath) as zf:
    names = zf.namelist()

    # 1. Carrito: quitar mención de fecha expiración
    carrito_name = next(n for n in names if "carrito" in n.lower() and "descuento" in n.lower())
    prefix, d = load(zf, carrito_name)
    raw_str = json.dumps(d)
    fixed = re.sub(r'\\n\\nEste c[^"]*?2026[^"]*?pasar\.', '', raw_str)
    if fixed == raw_str:
        fixed = re.sub(r'\\n\\nEste c[^"]*?expira[^"]*?\.', '', raw_str)
    d2 = json.loads(fixed)
    d2["root"]["workflow_name"] = "Recuperar carritos abandonados con descuento"
    save(prefix, d2, out_dir / "carrito_sin_expiry.flow")

    # 2. Stock bajo: unificar 2 flujos en 1
    stock_names = [n for n in names if "stock" in n.lower() and "bajo" in n.lower()]
    stock_names.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
    prefix, d = load(zf, stock_names[0])
    root = d["root"]
    email_step = next(s for s in root["steps"] if any(
        f.get("config_field_id") == "address" for f in s.get("config_field_values", [])
    ))
    email2 = copy.deepcopy(email_step)
    email2["step_id"] = "f1a2b3c4-d5e6-7890-abcd-ef1234567891"
    email2["step_position"] = [email_step["step_position"][0], email_step["step_position"][1] + 160]
    for f in email2["config_field_values"]:
        if f["config_field_id"] == "address":
            f["value"] = "contacto@tiendaslupe.cl"
    root["steps"].append(email2)
    root["links"].append({
        "from_step_id": email_step["step_id"],
        "from_port_id": "output",
        "to_step_id": email2["step_id"],
        "to_port_id": "input"
    })
    root["workflow_name"] = "Alerta de Stock Bajo (ventas + contacto)"
    save(prefix, d, out_dir / "alerta_stock_bajo_unificado.flow")

    # 3. Categorización: consolidar 4 flujos en 1
    org_name = next(n for n in names if "organizaci" in n.lower() and "colecciones" in n.lower()
                    and "agujas" not in n.lower() and "hilos" not in n.lower() and "lanas" not in n.lower())
    asig_name = next(n for n in names if "asignaci" in n.lower() and "tag" in n.lower())
    prefix, d_org = load(zf, org_name)
    _, d_asig = load(zf, asig_name)
    trigger_id = d_org["root"]["steps"][0]["step_id"]
    asig_trigger_id = d_asig["root"]["steps"][0]["step_id"]
    extra_steps = [s for s in d_asig["root"]["steps"] if s["step_id"] != asig_trigger_id]
    extra_links = []
    for lnk in d_asig["root"]["links"]:
        l2 = copy.deepcopy(lnk)
        if l2["from_step_id"] == asig_trigger_id:
            l2["from_step_id"] = trigger_id
        extra_links.append(l2)
    for s in extra_steps:
        s["step_position"] = [s["step_position"][0] + 500, s["step_position"][1]]
    d_org["root"]["steps"].extend(extra_steps)
    d_org["root"]["links"].extend(extra_links)
    d_org["root"]["workflow_name"] = "Auto-Organización en Colecciones (Consolidado)"
    save(prefix, d_org, out_dir / "auto_organizacion_consolidado.flow")

print("\nListo. Archivos en flows_fixed/")
print("Importa cada uno en Shopify Flow y desactiva los flujos originales.")
