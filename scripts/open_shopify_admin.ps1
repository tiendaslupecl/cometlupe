# Abre pestañas del admin de Shopify según SHOP_DOMAIN en .env (solo lee esa línea).
$root = Split-Path -Parent $PSScriptRoot

$envFile = Join-Path $root '.env'
$handle = '0viv7s-w8'

if (Test-Path $envFile) {
    Get-Content $envFile -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_ -match '^\s*SHOP_DOMAIN\s*=\s*(.+)\s*$') {
            $domain = $matches[1].Trim() -replace '^https?://', '' -replace '/.*', ''
            $handle = ($domain -split '\.')[0]
        }
    }
}

$base = "https://admin.shopify.com/store/$handle"
Write-Host "Tienda (handle): $handle"
Write-Host "Abriendo panel en el navegador..."

Start-Process "$base/settings/apps/development"
Start-Sleep -Milliseconds 400
Start-Process "$base/themes"
Start-Sleep -Milliseconds 400
Start-Process "$base/pages"
