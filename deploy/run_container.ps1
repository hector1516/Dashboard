# =============================================================
# run_container.ps1 — levanta (o recrea) el contenedor `dashboard`
# en el ServerVM. Es el mismo patrón que el de WorkersAdmon: un
# `docker run` explícito para que quede claro qué puertos y
# volúmenes tiene, en vez de un compose que nadie recuerda.
#
#   powershell -ExecutionPolicy Bypass -File deploy\run_container.ps1
#
# Las credenciales salen de deploy/env.local (gitignored) y se
# pasan con un --env-file temporal que se BORRA al terminar
# (PowerShell serializa mal los hashes en los argumentos -e).
#
# NO reinicia Docker Desktop: solo hace `docker run`. Si algún día
# hay que reconstruir la imagen, eso lo hace deploy/build.ps1.
# =============================================================
$ErrorActionPreference = "Continue"

$Nombre    = "dashboard"
$Puerto    = 8101          # puerto del host → 80 del contenedor
$Red       = "dashboard_net"
$Volumen   = "dashboard_data"
$EnvLocal  = Join-Path $PSScriptRoot "env.local"

# ── 1) Credenciales ────────────────────────────────────────────────────────
# Fuente 1: deploy/env.local (propia, estable).
# Fuente 2 (respaldo): los secrets del contenedor hub_python.
$vars = @{}
if (Test-Path $EnvLocal) {
    foreach ($line in (Get-Content $EnvLocal)) {
        if ($line -match '^\s*([A-Za-z0-9_]+)=(.*)$') { $vars[$Matches[1]] = $Matches[2] }
    }
    Write-Host "ENV: desde $EnvLocal"
} else {
    Write-Host "ENV: no hay env.local; se lee de hub_python"
    $json = docker exec -w /app hub_python python3 -c "import json,secretos_local;print(json.dumps(secretos_local.DB_CONFIG_LOCAL))"
    if ($LASTEXITCODE -ne 0 -or -not $json) { Write-Host "ERROR: no se pudieron leer las credenciales"; exit 1 }
    $cfg = $json | ConvertFrom-Json
    $vars["HUB_DB_SERVER"]   = $cfg.server
    $vars["HUB_DB_USER"]     = $cfg.user
    $vars["HUB_DB_PASSWORD"] = $cfg.password
    $vars["HUB_DB_DATABASE"] = $cfg.database
}

if (-not $vars["HUB_DB_PASSWORD"]) { Write-Host "ERROR: contraseña de BD vacía"; exit 1 }

# Secreto del panel remoto (api/panel.py). Sin esto nadie puede mover la
# pantalla desde Admon, a propósito: escribir exige token y el token no se
# inventa solo. Si falta, se avisa y se deja el panel deshabilitado en vez de
# correr con un token en blanco que cualquiera podría mandar.
if (-not $vars["HUB_PANEL_TOKEN"]) {
  Write-Host "AVISO: no hay HUB_PANEL_TOKEN en env.local; el panel remoto de la TV quedará deshabilitado (403)."
}

# Env-file en UTF-8 SIN BOM: el BOM rompe la primera variable.
$envFile = Join-Path $env:TEMP "dashboard.env"
$lines = @(
  "HUB_DB_SERVER=$($vars['HUB_DB_SERVER'])",
  "HUB_DB_USER=$($vars['HUB_DB_USER'])",
  "HUB_DB_PASSWORD=$($vars['HUB_DB_PASSWORD'])",
  "HUB_DB_DATABASE=$($vars['HUB_DB_DATABASE'])",
  "HUB_PANEL_TOKEN=$($vars['HUB_PANEL_TOKEN'])",
  "TZ=America/Mexico_City"
)
[System.IO.File]::WriteAllLines($envFile, $lines, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "ENV: db=$($vars['HUB_DB_DATABASE']) user=$($vars['HUB_DB_USER']) pass_len=$($vars['HUB_DB_PASSWORD'].Length)"

# ── 2) Red y volumen ───────────────────────────────────────────────────────
docker network inspect $Red *> $null
if ($LASTEXITCODE -ne 0) { docker network create $Red | Out-Null; Write-Host "red $Red creada" }

# El volumen NO se borra al recrear el contenedor: ahí vive el snapshot y los
# thumbs. `docker rm -v` lo borraría y la pantalla arrancaría sin datos.
docker volume inspect $Volumen *> $null
if ($LASTEXITCODE -ne 0) { docker volume create $Volumen | Out-Null; Write-Host "volumen $Volumen creado" }

# ── 3) Recrear el contenedor ───────────────────────────────────────────────
docker rm -f $Nombre 2>$null | Out-Null

$id = docker run -d --name $Nombre --restart unless-stopped --network $Red `
  -p ${Puerto}:80 `
  -v ${Volumen}:/data `
  --env-file $envFile `
  $Nombre

Remove-Item $envFile -ErrorAction SilentlyContinue    # no dejar credenciales en disco
if (-not $id) { Write-Host "ERROR: docker run falló"; exit 1 }

Write-Host "CONTENEDOR: $id"
Write-Host ""
Write-Host "  Pantalla : http://dashboard.ecc-sa.com.mx:$Puerto/"
Write-Host "  Health   : http://localhost:$Puerto/healthz"
Write-Host "  Logs     : docker logs -f $Nombre"
Write-Host ""

Start-Sleep -Seconds 8
docker ps --filter "name=$Nombre" --format "{{.Names}} | {{.Status}} | {{.Ports}}"
try {
    $h = Invoke-RestMethod "http://localhost:$Puerto/healthz" -TimeoutSec 10
    Write-Host "HEALTH: $($h.status) · degradado=$($h.degradado -join ',') · generado=$($h.generado_en)"
} catch {
    Write-Host "HEALTH: sin respuesta todavía (el snapshotter corre su primer ciclo)"
}
