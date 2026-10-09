"""
medios.py — todo lo binario del kiosco, en disco local.

Regla de oro del proyecto: la pantalla NO pide nada a internet. Por eso:

  · los fondos se BAJAN una vez a /data/media/wallpapers y se sirven desde
    ahí (en el dashboard de Field venía una URL de Bing y el navegador la
    descargaba: sin red, el kiosco perdía el fondo),
  · las fotos y los tickets se reescalan a thumbs aquí y se sirven como
    archivos (las fotos originales pesan ~1 MB),
  · el clima se lee de Open-Meteo pero se guarda en disco para poder seguir
    mostrando la ÚLTIMA lectura cuando la red se cae.
"""
import io
import json
import os
import time
import urllib.request

import config as C

try:
    from PIL import Image
    HAY_PIL = True
except Exception:
    HAY_PIL = False


# ── Thumbs ──────────────────────────────────────────────────────────────────
# Algunos blobs de `HUB_OxxoGasTickets.ImagenTicket` vienen con 15 bytes de
# basura ANTES del JPEG (mismo prefijo `75ab5a8a66a07bf8e97a06dab1eeb8ff` en
# todos: parece que algo del camino de subida del sync offline los prependeó).
# PIL no los abre, pero la imagen sí está: empieza en el offset 15. En vez de
# dejar el ticket sin foto (que es lo que se ve HOY en el dashboard de Field),
# los rescatamos: si PIL falla, se busca la firma de la imagen y se reintenta.
_FIRMAS = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF89a", b"RIFF")


def _recuperar_firma(crudo: bytes) -> bytes | None:
    """Devuelve el recorte que empieza en una firma de imagen, o None."""
    for firma in _FIRMAS:
        i = crudo.find(firma)
        if 0 < i <= 64:          # casi siempre son 15 bytes de prefijo
            return crudo[i:]
    return None


def _thumb(raw: bytes, ancho: int) -> bytes | None:
    if not HAY_PIL or not raw:
        return None
    for intento in (raw, _recuperar_firma(raw)):
        if not intento:
            continue
        try:
            img = Image.open(io.BytesIO(intento))
            if img.mode != "RGB":
                img = img.convert("RGB")
            if img.width > ancho:
                ratio = ancho / float(img.width)
                img = img.resize((ancho, max(1, int(img.height * ratio))), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=80, optimize=True, progressive=True)
            return out.getvalue()
        except Exception:
            continue
    return None


def _es_fresco(ruta: str, ttl_dias: int = 7) -> bool:
    try:
        return (time.time() - os.path.getmtime(ruta)) < ttl_dias * 86400
    except OSError:
        return False


def thumbs_de_fotos(fotos: list) -> tuple[list, bool]:
    """
    Genera (o reutiliza) el thumb de cada foto del carrusel.
    Devuelve (rutas, ok). Si Pillow no está o la BD falla, `ok` es False y la
    pantalla simplemente no muestra fotos: el resto sigue.
    """
    rutas = []
    ok = True
    conn = None
    try:
        from db import get_connection
        conn = get_connection()
        with conn.cursor(as_dict=True) as cur:
            for f in fotos:
                destino = os.path.join(C.THUMBS_DIR, f"rep_{f['IdReporte']}_{f['Orden']}_w{C.THUMB_FOTOS_ANCHO}.jpg")
                if not _es_fresco(destino):
                    cur.execute(
                        "SELECT FotoComprimida FROM ReportesServicioFotos WHERE IdReporte = %s AND Orden = %s",
                        (f["IdReporte"], f["Orden"]),
                    )
                    fila = cur.fetchone()
                    if not fila or not fila.get("FotoComprimida"):
                        continue
                    thumb = _thumb(fila["FotoComprimida"], C.THUMB_FOTOS_ANCHO)
                    if thumb:
                        _escribir(destino, thumb)
                if os.path.isfile(destino):
                    rutas.append(f"/media/thumbs/{os.path.basename(destino)}")
                else:
                    ok = False
    except Exception:
        ok = False
    return rutas, ok


def _decodificar_b64(valor) -> bytes:
    """
    Devuelve los bytes de la imagen, venga como venga: `bytes` crudos
    (`HUB_UsuariosFotos.Archivo` es VARBINARY), un data URL
    (`data:image/jpeg;base64,...`) o base64 pelado (`HUB_UserAvatars`).
    """
    import base64
    if isinstance(valor, bytes):
        return valor
    s = (valor or "").strip()
    if s.startswith("data:") and "," in s:
        s = s.split(",", 1)[1]
    return base64.b64decode(s)


def _guardar_fotos(fotos: dict, carpeta: str, ancho: int, ttl_dias: int) -> bool:
    """Común a avatares y fotos: decodifica base64 y escribe u<Id>.jpg."""
    ok = True
    for id_usuario, b64 in (fotos or {}).items():
        destino = os.path.join(carpeta, f"u{id_usuario}.jpg")
        if _es_fresco(destino, ttl_dias=ttl_dias):
            continue
        try:
            thumb = _thumb(_decodificar_b64(b64), ancho)
            if thumb:
                _escribir(destino, thumb)
        except Exception:
            ok = False
    return ok


def guardar_avatares(avs: dict) -> bool:
    """
    Los avatares de HUB_UserAvatars vienen como base64. Se escriben una vez como
    /media/avatars/u<Id>.jpg y el snapshot lleva la ruta: mandar 20 avatares en
    el JSON infla la respuesta sin necesidad.
    """
    return _guardar_fotos(avs, C.AVATARS_DIR, 256, ttl_dias=30)


def guardar_fotos_usuarios(fotos: dict) -> bool:
    """
    Fotos REALES de los usuarios (`HUB_UsuariosFotos.Archivo`), aparte de los
    avatares IA. Se escriben como /media/usuarios/u<Id>.jpg. El front las
    prefiere en Celebraciones y Asistencia, con el avatar IA como respaldo.
    """
    return _guardar_fotos(fotos, C.USUARIOS_DIR, 256, ttl_dias=30)


def guardar_imagen_panel(clave: str, crudo: bytes, content_type: str, id_img) -> str:
    """
    Escribe la imagen a pantalla completa (la de la portada) en
    /data/media/panel/ y devuelve la ruta para el snapshot.

    Por qué al disco y no en el snapshot: son 200-400 KB por imagen y la
    pantalla pide el snapshot cada 30 s. Meter los bytes ahí serían ~10 MB/s de
    red interna para bytes que no cambian. En el disco, nginx los sirve como
    cualquier otra foto y el snapshot sólo lleva la ruta.

    **El nombre lleva el Id de la fila a propósito.** Con un nombre fijo
    (`portada.jpg`) la TV nunca veía la imagen nueva: el navegador la tenía
    cacheada y, como la URL no cambiaba, se quedaba con la vieja para siempre.
    Es un bug que en la TV no se nota (la imagen "de la oficina" parece la de
    siempre) y sólo aparece cuando alguien sube la portada del mes nuevo.

    Se borran las anteriores de esa misma clave para que la carpeta no crezca
    400 KB por cada subida.
    """
    ext = {"image/png": ".png", "image/webp": ".webp", "image/jpeg": ".jpg"}.get(
        (content_type or "").lower(), ".img"
    )
    base = f"{clave.lower()}-{id_img}{ext}"
    destino = os.path.join(C.PANEL_DIR, base)
    _escribir(destino, crudo)
    # Limpieza de las versiones anteriores de ESTA clave.
    try:
        for viejo in os.listdir(C.PANEL_DIR):
            if viejo.startswith(f"{clave.lower()}-") and viejo != base:
                os.remove(os.path.join(C.PANEL_DIR, viejo))
    except OSError:
        # Que quede un archivo viejo de más no rompe nada; no vale la pena
        # fallar la subida por limpiar una carpeta.
        pass
    return f"/media/panel/{base}"


def _escribir(destino: str, datos: bytes) -> None:
    """Escritura atómica: tmp + replace, para que nginx nunca lea medio archivo."""
    tmp = destino + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(datos)
    os.replace(tmp, destino)


# ── Wallpapers ──────────────────────────────────────────────────────────────
def _bing_urls(limite: int = 8) -> list:
    """
    URLs de los wallpapers del día. El `id` de la URL es lo que identifica la
    imagen (OHR.Nombre_ROW<hash>_<res>); de ahí se saca el nombre del archivo.
    Ojo: NO usar el path de la URL para el nombre — todas empiezan con /th, y
    los archivos acababan llamándose "bing-th.jpg".
    """
    import urllib.parse
    url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=%d" % limite
    req = urllib.request.Request(url, headers={"User-Agent": C.BING_UA})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out = []
    for img in data.get("images", []):
        path = img.get("url", "")
        if not path.startswith("/th"):
            continue
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        ident = (qs.get("id") or [""])[0]
        if not ident:
            continue
        out.append({
            "url": "https://www.bing.com" + path,
            "id": ident.split(".")[-1] if "." in ident else ident,
            "nombre": f"bing-{ident.rsplit('.', 1)[0] if ident.endswith('.jpg') else ident}.jpg",
        })
    return out[:limite]


def actualizar_fondos() -> tuple[list, bool]:
    """
    Baja UN wallpaper nuevo por ciclo y rota el directorio a `WALLPAPERS_MAX`.
    Los que ya están no se vuelven a bajar.

    Devuelve (rutas_locales, ok). Si no hay red, `ok` es False pero las rutas
    que ya había siguen sirviéndose: el fondo no se pierde nunca.
    """
    ok = True
    try:
        for item in _bing_urls(2):
            destino = os.path.join(C.WALLPAPERS_DIR, item["nombre"])
            if os.path.isfile(destino):
                continue
            req = urllib.request.Request(item["url"], headers={"User-Agent": C.BING_UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                crudo = resp.read()
            # Se reescala a Full HD: el original de Bing viene a 1920x1080 o más.
            jpg = _thumb(crudo, C.WALLPAPERS_ANCHO) or crudo
            _escribir(destino, jpg)
    except Exception as exc:
        ok = False
        print(f"[fondos] no se pudo bajar: {exc}", flush=True)

    # Rotación: quedarse con los últimos N por fecha de modificación.
    try:
        archivos = sorted(
            (os.path.join(C.WALLPAPERS_DIR, f) for f in os.listdir(C.WALLPAPERS_DIR)
             if f.endswith(".jpg")),
            key=os.path.getmtime, reverse=True)
        for viejo in archivos[C.WALLPAPERS_MAX:]:
            os.remove(viejo)
    except Exception:
        pass

    return _fondos_locales(), ok


def _fondos_locales() -> list:
    try:
        archivos = sorted(
            (f for f in os.listdir(C.WALLPAPERS_DIR) if f.endswith(".jpg")),
            key=lambda f: os.path.getmtime(os.path.join(C.WALLPAPERS_DIR, f)), reverse=True)
        return [f"/media/wallpapers/{f}" for f in archivos]
    except Exception:
        return []


# ── Clima ───────────────────────────────────────────────────────────────────
def _wmo_desc(code: int) -> str:
    return {
        0: "Despejado", 1: "Mayormente despejado", 2: "Parcial nublado", 3: "Nublado",
        45: "Niebla", 48: "Niebla con escarcha",
        51: "Lluvia ligera", 53: "Lluvia moderada", 55: "Lluvia intensa",
        61: "Llovizna", 63: "Lluvia moderada", 65: "Lluvia fuerte",
        71: "Nevada ligera", 73: "Nevada moderada", 75: "Nevada fuerte",
        80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos fuertes",
        95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta fuerte con granizo",
    }.get(code, f"Código {code}")


def _wmo_icon(code: int, es_dia: int) -> str:
    if code == 0:
        return "☀️" if es_dia else "🌙"
    if code <= 2:
        return "⛅" if es_dia else "☁️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if 51 <= code <= 67:
        return "🌦️" if code <= 57 else "🌧️"
    if 71 <= code <= 77:
        return "❄️"
    if 80 <= code <= 99:
        return "⛈️"
    return "🌤️"


def leer_clima() -> tuple[dict, bool]:
    """
    Última lectura del clima + si esta lectura es fresca.

    Ante cualquier fallo devuelve la última guardada con `leido_en` viejo y
    `ok=False`: es exactamente el caso "sin internet" y la pantalla lo muestra
    como "Clima no disponible · último dato de hace 2 h", en vez de mostrar 0°.
    """
    guardada = None
    try:
        with open(C.WEATHER, encoding="utf-8") as fh:
            guardada = json.load(fh)
    except Exception:
        guardada = None

    fresca = False
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={C.CLIMA_LAT}&longitude={C.CLIMA_LON}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            "&timezone=America%2FMexico_City&forecast_days=3"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ECCSA-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=C.CLIMA_TIMEOUT) as resp:
            raw = json.loads(resp.read())

        actual = raw.get("current", {})
        diario = raw.get("daily", {})
        wmo = actual.get("weather_code", 0)
        es_dia = actual.get("is_day", 1)
        tmax = diario.get("temperature_2m_max") or []
        tmin = diario.get("temperature_2m_min") or []
        lluvia = diario.get("precipitation_probability_max") or []

        datos = {
            "actual": {
                "temperatura": actual.get("temperature_2m"),
                "humedad": actual.get("relative_humidity_2m"),
                "viento": actual.get("wind_speed_10m"),
                "codigo_clima": wmo,
                "descripcion": _wmo_desc(wmo),
                "icono": _wmo_icon(wmo, es_dia),
                "es_dia": bool(es_dia),
            },
            "hoy": {"max": tmax[0] if tmax else None, "min": tmin[0] if tmin else None,
                    "prob_lluvia": lluvia[0] if lluvia else None},
            "manana": {"max": tmax[1] if len(tmax) > 1 else None,
                       "min": tmin[1] if len(tmin) > 1 else None,
                       "prob_lluvia": lluvia[1] if len(lluvia) > 1 else None},
            "leido_en": _ahora_iso(),
        }
        _escribir_json(C.WEATHER, datos)
        return datos, True
    except Exception:
        if guardada:
            return guardada, False
        return {
            "actual": {"temperatura": None, "humedad": None, "viento": None,
                       "codigo_clima": 0, "descripcion": "Sin datos", "icono": "❓", "es_dia": True},
            "hoy": {"max": None, "min": None, "prob_lluvia": None},
            "manana": {"max": None, "min": None, "prob_lluvia": None},
            "leido_en": None,
        }, False


def _ahora_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _escribir_json(ruta: str, datos) -> None:
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, default=str)
    os.replace(tmp, ruta)
