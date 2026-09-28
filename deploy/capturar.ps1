# =============================================================
# capturar.ps1 — capturas de las 10 pantallas con el Edge del
# ServerVM (el MISMO navegador que corre en la TV).
#
# Sirve para dos cosas: revisar el diseño sin tener que ir a la
# pantalla, y comprobar que Edge + las banderas del modo kiosco
# funcionan (autoplay, pantalla completa, 1920×1080).
#
#   powershell -ExecutionPolicy Bypass -File deploy\capturar.ps1
#   powershell -ExecutionPolicy Bypass -File deploy\capturar.ps1 -Pantalla legends
#
# NO reinicia Docker Desktop. Solo abre Edge en headless.
# =============================================================
param(
    [int]$Puerto = 8101,
    [string]$Pantalla = "",
    [int]$EsperaMs = 4000
)

$ErrorActionPreference = "Continue"
$Edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$Salida = "C:\Dashboard\capturas"
New-Item -ItemType Directory -Force -Path $Salida | Out-Null

# Las mismas banderas que deja el instalador de la TV, más --headless para
# capturar sin abrir ventana.
$Banderas = @(
    "--headless=new",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--force-device-scale-factor=1",
    "--autoplay-policy=no-user-gesture-required",
    "--hide-scrollbars",
    "--no-first-run",
    "--user-data-dir=C:\Dashboard\.edge-capturas"
)

$Pantallas = if ($Pantalla) { @($Pantalla) } else {
    @("pulso","combustible","legends","reportes","tickets","celebraciones","metricas","fotos","clima","notas")
}

foreach ($p in $Pantallas) {
    # sinanim=1: sin animaciones de entrada, si no la foto sale a medio camino
    # y parece que faltan elementos que sí están.
    $url = "http://localhost:$Puerto/?pantalla=$p&sinanim=1"
    $png = Join-Path $Salida "$p.png"
    if (Test-Path $png) { Remove-Item $png -Force }

    $args = @($Banderas) + @("--screenshot=$png", "--virtual-time-budget=$EsperaMs", $url)
    $proc = Start-Process -FilePath $Edge -ArgumentList $args -PassThru -WindowStyle Hidden
    $proc.WaitForExit(45000) | Out-Null

    if (Test-Path $png) {
        $kb = [math]::Round((Get-Item $png).Length / 1KB)
        Write-Host ("{0,-15} {1,4} KB  {2}" -f $p, $kb, $png) -ForegroundColor Green
    } else {
        Write-Host ("{0,-15} SIN CAPTURA" -f $p) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Capturas en $Salida" -ForegroundColor Cyan
