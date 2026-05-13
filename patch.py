from pathlib import Path

p = Path("scripts/audit_404_full.py")
src = p.read_text(encoding="utf-8")

src = src.replace("for attempt in range(3):", "for attempt in range(5):")
src = src.replace("# 2s, 4s, 8s", "# 2s, 4s, 8s, 16s, 32s")
src = src.replace("if attempt < 2:", "if attempt < 4:")
src = src.replace("time.sleep(0.3)", "time.sleep(0.5)")
src = src.replace("issues = []\nok = 0", "issues = []\nthrottled = []\nok = 0")

old_block = '''    if isinstance(status, int) and status < 400:
        ok += 1
    else:
        issues.append((path, title, status))
        print(f"  [{status}] {path}  ({title[:50]})")'''

new_block = '''    if isinstance(status, int) and status < 400:
        ok += 1
    elif status == 429:
        throttled.append((path, title))
        ok += 1
    else:
        issues.append((path, title, status))
        print(f"  [{status}] {path}  ({title[:50]})")'''

src = src.replace(old_block, new_block)

old_resumen = '''print(f"RESUMEN: {ok}/{len(urls)} OK, {len(issues)} con problemas")
print(f"{'='*60}")'''

new_resumen = '''print(f"RESUMEN: {ok}/{len(urls)} OK, {len(issues)} con problemas")
if throttled:
    print(f"  ({len(throttled)} URLs throttled - 429, no es 404 real)")
print(f"{'='*60}")'''

src = src.replace(old_resumen, new_resumen)

p.write_text(src, encoding="utf-8")
print("Parche aplicado OK")