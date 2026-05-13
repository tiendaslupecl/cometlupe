Set-Location C:\Users\cpich\cometlupe

# Borrar blank.yml
Remove-Item -Force .github\workflows\blank.yml -ErrorAction SilentlyContinue

# audit-daily.yml
@'
name: Audit Diario
on:
  schedule:
    - cron: '0 13 * * 1-5'
  workflow_dispatch:
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Run audits
        env:
          SHOP_DOMAIN: ${{ secrets.SHOP_DOMAIN }}
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
        run: |
          set +e
          python scripts/audit_404_full.py | tee audit-404.log
          python scripts/audit_collection_intruders.py | tee audit-intruders.log
          python scripts/verify_product_collections.py | tee audit-verify.log
          fail=0
          grep -qE "TOTAL: [1-9][0-9]* productos potencialmente" audit-intruders.log && fail=1
          grep -qE "RESUMEN: [0-9]+/[0-9]+ OK, [1-9][0-9]* con problemas" audit-404.log && fail=1
          grep -qE "FALTA agregar a coleccion sugerida: [1-9]" audit-verify.log && fail=1
          grep -qE "SIN coleccion especifica: +[1-9]" audit-verify.log && fail=1
          exit $fail
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: audit-reports
          path: audit-*.log
          retention-days: 30
'@ | Set-Content -Encoding utf8 .github\workflows\audit-daily.yml

# auto-categorize-hourly.yml
@'
name: Auto-categorizar productos nuevos
on:
  schedule:
    - cron: '5 11,14,17,20,23,2 * * *'
  workflow_dispatch:
jobs:
  categorize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Auto-categorize
        id: categorize
        env:
          SHOP_DOMAIN: ${{ secrets.SHOP_DOMAIN }}
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
        run: |
          python scripts/auto_categorize.py --since-hours 4 --apply | tee auto-categorize.log
          grep -qE "^[1-9][0-9]* acciones aplicadas" auto-categorize.log && echo "changed=true" >> $GITHUB_OUTPUT || echo "changed=false" >> $GITHUB_OUTPUT
      - uses: actions/upload-artifact@v4
        if: steps.categorize.outputs.changed == 'true'
        with:
          name: auto-categorize-${{ github.run_id }}
          path: auto-categorize.log
          retention-days: 14
'@ | Set-Content -Encoding utf8 .github\workflows\auto-categorize-hourly.yml

# auto-upsell-manual.yml
@'
name: Reasignar Upsells
on:
  workflow_dispatch:
  schedule:
    - cron: '0 15 * * 0,3'
jobs:
  upsell:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Run upsell assign
        env:
          SHOP_DOMAIN: ${{ secrets.SHOP_DOMAIN }}
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
        run: |
          python scripts/upsell_assign.py --apply | tee upsell.log
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: upsell-${{ github.run_id }}
          path: upsell.log
          retention-days: 14
'@ | Set-Content -Encoding utf8 .github\workflows\auto-upsell-manual.yml

# healthcheck-weekly.yml
@'
name: Healthcheck Semanal
on:
  schedule:
    - cron: '0 14 * * 0'
  workflow_dispatch:
jobs:
  healthcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Audit completo
        env:
          SHOP_DOMAIN: ${{ secrets.SHOP_DOMAIN }}
          ADMIN_API_TOKEN: ${{ secrets.ADMIN_API_TOKEN }}
        run: |
          set +e
          python scripts/audit_store_404.py | tee weekly-store.log
          python scripts/audit_404_full.py | tee weekly-404.log
          fail=0
          grep -qE "RESUMEN: [0-9]+/[0-9]+ OK, [1-9][0-9]* con problemas" weekly-404.log && fail=1
          grep -qE "Total vacias: [1-9]" weekly-store.log && fail=1
          grep -qE "[1-9][0-9]* problemas en menus" weekly-store.log && fail=1
          exit $fail
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: healthcheck-reports
          path: weekly-*.log
          retention-days: 60
'@ | Set-Content -Encoding utf8 .github\workflows\healthcheck-weekly.yml

Write-Host "Workflows actualizados"

git add -A
git commit -m "Mejorar workflows: pip cache, horarios diurnos, checks adicionales"
git push origin main