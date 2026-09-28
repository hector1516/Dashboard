# =============================================================
# instalar-kiosco.ps1 — se corre UNA vez en la TV (Windows 11).
#
# Deja la pantalla compuesta:
#   1. `dashboard.ecc-sa.com.mx` → la IP del ServerVM, en el hosts de Windows.
#      El dominio NO está en Cloudflare a propósito: el kiosco es de la red
#      interna de la oficina, y publicarlo en internet sería exponer nombres de
#      clientes, folios de reportes y fotos en un tracker público.
#   2. Acceso directo "ECCSA Dashboard" que abre Edge en modo kiosco a pantalla
#      completa, con la política de autoplay de audio (sin ella el navegador
#      bloquea el sonido hasta el primer clic, y en una pantalla sin teclado
#      nadie lo haría).
#   3. Autoinicio al encender la TV (registro de Windows).
#   4. Opción de apagar la pantalla fuera de horario (23:00–07:00): el
#      EnergyStar/DPMS de los monitores de la oficina a veces no dispara solo.
#
# Uso (PowerShell como Administrador):
#   powershell -ExecutionPolicy Bypass -File instalar-kiosco.ps1
#   powershell -ExecutionPolicy Bypass -File instalar-kiosco.ps1 -ServerIP 10.188.141.31 -Puerto 8101
# =============================================================
param(
    [string]$ServerIP = "10.188.141.31",
    [int]$Puerto = 8101,
    [string]$Dominio = "dashboard.ecc-sa.com.mx",
    [switch]$SinAutoinicio,
    [switch]$SinApagadoNocturno
)

$ErrorActionPreference = "Stop"
$Url = "http://${Dominio}:${Puerto}/"
$Escritorio = [Environment]::GetFolderPath("Desktop")
$AccesoDirecto = Join-Path $Escritorio "ECCSA Dashboard.lnk"
$Inicio = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"

function Es-Admin {
    return ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
            ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Es-Admin)) {
    Write-Host "ERROR: hay que correrlo como Administrador (clic derecho → Ejecutar como administrador)." -ForegroundColor Red
    exit 1
}

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Kiosco ECCSA · instalador para la TV" -ForegroundColor Cyan
Write-Host "  URL: $Url" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan

# ── 1) hosts ───────────────────────────────────────────────────────────────
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$linea = "$ServerIP`t$Dominio"
$contenido = Get-Content $hostsPath -Raw -ErrorAction SilentlyContinue
if ($contenido -and $contenido -match [regex]::Escape($Dominio)) {
    # Reemplazar la línea si ya estaba (por si cambió la IP del ServerVM).
    $contenido = $contenido -replace "(?m)^.*$([regex]::Escape($Dominio)).*$", $linea
    Set-Content -Path $hostsPath -Value $contenido -Encoding ASCII
    Write-Host "[1/4] hosts: entrada actualizada → $linea" -ForegroundColor Green
} else {
    Add-Content -Path $hostsPath -Value "`n# ECCSA Dashboard (kiosco de la oficina)`n$linea" -Encoding ASCII
    Write-Host "[1/4] hosts: entrada agregada → $linea" -ForegroundColor Green
}

# Comprobación de que el puerto responde ANTES de seguir: si el contenedor no
# está arriba, es mejor enterarse ahora que ver una pantalla en blanco en el
# pasillo a las 8 de la mañana.
try {
    $h = Invoke-RestMethod "http://${ServerIP}:${Puerto}/healthz" -TimeoutSec 8
    Write-Host "      health del servidor: $($h.status) (degradado: $($h.degradado -join ','))" -ForegroundColor Green
} catch {
    Write-Host "      AVISO: no responde http://${ServerIP}:${Puerto}/healthz" -ForegroundColor Yellow
    Write-Host "      (si acabas de desplegar, el snapshotter puede estar en su primer ciclo)" -ForegroundColor Yellow
}

# ── 2) acceso directo en modo kiosco ───────────────────────────────────────
# Las banderas que importan:
#   --kiosk                            sin barra de direcciones ni interfaz
#   --start-fullscreen                 pantalla completa
#   --autoplay-policy=no-user-gesture-required   el audio suena sin que nadie toque nada
#   --disable-pinch                    que el zoom no se active solo
#   --overscroll-history-navigation=0  sin scrolls accidentales
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe" }
if (-not (Test-Path $edge)) {
    Write-Host "ERROR: no se encontró msedge.exe" -ForegroundColor Red
    exit 1
}

$argumentos = "--kiosk --start-fullscreen --autoplay-policy=no-user-gesture-required " +
              "--disable-pinch --overscroll-history-navigation=0 --no-first-run " +
              "--disable-features=Translate,InfiniteSessionRestore " +
              "--user-data-dir=`"$env:LOCALAPPDATA\ECCSA-Kiosco`" `"$Url`""

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($AccesoDirecto)
$sc.TargetPath = $edge
$sc.Arguments = $argumentos
$sc.WorkingDirectory = "C:\"
$sc.IconLocation = "$edge,0"
$sc.Description = "Centro de Operaciones ECCSA (kiosco)"
$sc.Save()
Write-Host "[2/4] acceso directo creado: $AccesoDirecto" -ForegroundColor Green

# ── 3) autoinicio ──────────────────────────────────────────────────────────
if ($SinAutoinicio) {
    Write-Host "[3/4] autoinicio: omitido (con el flag -SinAutoinicio)" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Force -Path $Inicio | Out-Null
    Copy-Item $AccesoDirecto (Join-Path $Inicio "ECCSA Dashboard.lnk") -Force
    Write-Host "[3/4] autoinicio: el kiosco abre al encender la TV" -ForegroundColor Green
}

# ── 4) apagado nocturno (opcional) ─────────────────────────────────────────
# Los monitores de la oficina no siempre cumplen el DPMS solo. Esta tarea
# apaga la pantalla entre las 23:00 y las 07:00 con SendMessage (WM_SYSCOMMAND,
# MonitorPower) y la vuelve a prender.
if ($SinApagadoNocturno) {
    Write-Host "[4/4] apagado nocturno: omitido (con el flag -SinApagadoNocturno)" -ForegroundColor Yellow
} else {
    $script = Join-Path $env:ProgramData "ECCSA-Kiosco\apagar-noche.ps1"
    New-Item -ItemType Directory -Force -Path (Split-Path $script) | Out-Null
    @'
# Apaga/prende el monitor por hora. Lo invoca la tarea programada cada 5 min.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Monitor {
  [DllImport("user32.dll")]
  public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
"@
$ahora = (Get-Date).Hour
$apagado = ($ahora -ge 23 -or $ahora -lt 7)
$h = (Get-Process -Name "msedge" -ErrorAction SilentlyContinue | Where-Object {
      $_.MainWindowHandle -ne 0 } | Select-Object -First 1)
if ($h) {
  $WM_SYSCOMMAND = 0x0112; $SC_MONITORPOWER = 0xF170
  if ($apagado) { [Monitor]::SendMessage($h.MainWindowHandle, $WM_SYSCOMMAND, $SC_MONITORPOWER, 2) | Out-Null }
  else          { [Monitor]::SendMessage($h.MainWindowHandle, $WM_SYSCOMMAND, $SC_MONITORPOWER, -1) | Out-Null }
}
'@ | Set-Content -Path $script -Encoding UTF8

    Unregister-ScheduledTask -TaskName "ECCSA-Kiosco-Noche" -ErrorAction SilentlyContinue
    $accion = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`""
    $disparo = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
        -RepetitionInterval (New-TimeSpan -Minutes 5)
    Register-ScheduledTask -TaskName "ECCSA-Kiosco-Noche" -Action $accion -Trigger $disparo `
        -Description "Apaga el monitor de la TV entre 23:00 y 07:00" `
        -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) | Out-Null
    Write-Host "[4/4] apagado nocturno: tarea ECCSA-Kiosco-Noche (23:00-07:00)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Listo. Para ver la pantalla ahora mismo, abre el acceso directo" -ForegroundColor Cyan
Write-Host "  o ejecuta:  `"$edge`" $argumentos" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Pruebas útiles:" -ForegroundColor Cyan
Write-Host "  · $Url          (la pantalla)"
Write-Host "  · http://${ServerIP}:${Puerto}/healthz   (salud del servidor)"
Write-Host "  · Ctrl+Shift+R   (recarga manual si algo se ve viejo)"
