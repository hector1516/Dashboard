"""
mapa.py
=======
Genera la imagen del mapa "Ingenieros en Campo" con Pillow, en el SERVIDOR.

POR QUÉ SE GENERA AQUÍ Y NO EN EL NAVEGADOR
Se podría hacer con Leaflet en la pantalla (marcadores, `fitBounds` y el zoom
sale solo), pero esa opción depende de que la TV tenga salida a internet para
bajar las teselas, y no hay garantía de eso: el fondo de Bing, el clima y las
fotos los baja la API, no el navegador. Si la TV no tiene internet, un mapa
client-side se ve gris y vacío, que es el peor resultado posible en una pantalla
de 6 metros.

Aquí la API (que sí sale) arma un PNG de 1920x1080 y la TV sólo la muestra. Es
el mismo patrón que las capas de los temas y que la portada: bytes en
/data/media/, y al snapshot sólo llega la ruta.

EL ZOOM
Sale del recuadro que abarcan las ubicaciones, que es justo lo pedido: con una
sola persona se acerca mucho (un punto no tiene extensión, así que se usa un
zoom fijo alto), y conforme se reparten entre Monterrey y el resto del país se
aleja hasta que quepan todas. Se calcula con la fórmula estándar de zoom por
píxel de pantalla, no con constantes inventadas.

TESELAS
OpenStreetMap, que no pide clave ni tarjeta. Si alguien mete una clave de
Google Maps Static API, cambiar `TESELAS_URL` y `_descargar_tesela` es todo lo
que hay que tocar: la geometría no depende del proveedor.

CADUCIDAD
La imagen se regenera cuando cambia el conjunto de ubicaciones y, en el peor
caso, cada `_CADUCIDAD_S` (5 min). Es lo que evita estar bajando teselas cada
2 min aunque nadie se haya movido.
"""

from __future__ import annotations

import io
import math
import os
import threading
import time
import urllib.error
import urllib.request

from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 1920, 1080

# Zona del mapa cuando NO hay ninguna ubicación: Monterrey. Si no se pone nada,
# el PNG saldría de 1x1 píxel y `fitBounds` no tendría con qué trabajar.
_CENTRO_VACIO = (25.6866, -100.3161)
_ZOOM_VACIO = 11
_ZOOM_UNO = 14          # con una sola persona el punto no da extensión
_ZOOM_MIN, _ZOOM_MAX = 3, 17

# Teselas de OSM. El `User-Agent` no es opcional: su política de uso exige
# identificarse, y sin él devuelven 429 con bastante facilidad.
TESELAS_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
_USER_AGENT = "ECCSA-Kiosco/1.0 (mapa Ingenieros en Campo; contacto: administracion@ecc-sa.com.mx)"
_TIMEOUT = 8

_CADUCIDAD_S = 300

_TILE = 256          # lado de una tesela en píxeles, por definición del esquema
_MARGEN_PX = 140      # aire alrededor del recuadro, para que los marcadores no
                      # queden pegados al borde

_candado = threading.Lock()
_cache: dict = {"clave": None, "ruta": None, "ts": 0}


def _ruta_destino() -> str:
    d = os.path.join(os.environ.get("KIOSKO_DATA", "/data"), "media", "maps")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "campo.png")


def _descargar_tesela(z: int, x: int, y: int) -> Image.Image | None:
    """Una tesela, o None si no se pudo. Un mapa a medias es mejor que nada."""
    url = TESELAS_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            crudo = r.read()
        return Image.open(io.BytesIO(crudo)).convert("RGB")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _proyeccion(lat: float, lon: float, z: int):
    """Web Mercator a píxeles del mundo, como la usa Leaflet."""
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n * _TILE
    sinlat = math.sin(math.radians(max(-85.0511, min(85.0511, lat))))
    y = (0.5 - math.log((1 + sinlat) / (1 - sinlat)) / (4 * math.pi)) * n * _TILE
    return x, y


def _latlon_a_px(lat: float, lon: float, z: int):
    """Alias en nombre de servidor, porque hay dos sentidos posibles."""
    return _proyeccion(lat, lon, z)


def _elegir_zoom(puntos, ancho_px: int, alto_px: int) -> int:
    """
    El zoom más cercano que hace que TODOS los puntos quepan.

    Se empieza en el máximo y se baja hasta que el recuadro cabe. Con una sola
    ubicación no hay recuadro que ajustar, así que se queda en `_ZOOM_UNO`: es el
    único caso donde "ajustar al contenido" no significa nada.
    """
    if not puntos:
        return _ZOOM_VACIO
    if len(puntos) == 1:
        return _ZOOM_UNO

    # El recuadro es el mínimo y el máximo de TODOS los puntos, no el primero y
    # el último: con tres o más ubicaciones, desempaquetar dos rompía con
    # "too many values to unpack".
    lat_a = min(p[0] for p in puntos)
    lat_b = max(p[0] for p in puntos)
    lon_a = min(p[1] for p in puntos)
    lon_b = max(p[1] for p in puntos)

    for z in range(_ZOOM_MAX, _ZOOM_MIN - 1, -1):
        x1, y1 = _proyeccion(lat_a, lon_a, z)
        x2, y2 = _proyeccion(lat_b, lon_b, z)
        ancho_requerido = abs(x2 - x1) + 2 * _MARGEN_PX
        alto_requerido = abs(y2 - y1) + 2 * _MARGEN_PX
        if ancho_requerido <= ancho_px and alto_requerido <= alto_px:
            return z
    return _ZOOM_MIN


def _fuente(tam: int):
    """La fuente del mapa; si no hay ninguna cargable, la de Pillow."""
    for nombre in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _etiquetas_para(n: int, z: int) -> int:
    """
    Tamaño de la letra, según cuánta gente hay Y cuánta gente cabe en pantalla.

    Las dos cosas cuentan. Con 25 personas en Monterrey el mapa está cerca y los
    nombres grandes se enciman; con 3 personas repartidas por el país el mapa se
    aleja a zoom 7 y un nombre de 40 px se come media pantalla. O sea: el tamaño
    tiene que bajar en los dos casos, por motivos distintos.
    """
    base = 40 if n <= 6 else 32 if n <= 14 else 26 if n <= 28 else 22
    if z >= 12:
        return base
    if z >= 9:
        return int(base * 0.78)
    return int(base * 0.58)      # mapa muy alejado: letrero de estación


def _ancho_texto(d, texto: str, fuente) -> int:
    return int(d.textlength(texto, font=fuente))


def _marcar(d, x, y, nombre: str, color, fuente, idx: int = 0) -> None:
    """
    Un pin con la inicial y el nombre en una etiqueta.

    El offset de la etiqueta ALTERNA arriba/abajo según el índice. Con 25 personas
    apretadas en la ciudad, poner todas las etiquetas debajo hacía que se
    encimaran ("Ing 12/Ing 07" ilegible). Alternando y con una guía que une el pin
    con su etiqueta, la mitad de los choques desaparecen y los que quedan se
    ven como lo que son.

    Además va sobre una pastilla blanca: el mapa puede salir claro o oscuro según
    la zona, y un texto suelto encima de calles y parques no se lee en ninguno de
    los dos casos.
    """
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=(0, 0, 0, 60))
    d.ellipse([x - 21, y - 21, x + 21, y + 21], fill=color, outline=(255, 255, 255), width=5)

    inicial = (nombre or "?")[0].upper()
    d.text((x, y - 1), inicial, font=fuente, fill=(255, 255, 255), anchor="mm")

    etiqueta = nombre or "?"
    ancho = _ancho_texto(d, etiqueta, fuente)
    alto_et = int(fuente.size * 1.75)
    # Abajo para los pares, arriba para los impares.
    arriba = idx % 2 == 1
    cy = (y - 44 - alto_et // 2) if arriba else (y + 44 + alto_et // 2)

    d.line([x, y - 22 if not arriba else y + 22, x, cy + (alto_et // 2 if arriba else -alto_et // 2)],
           fill=(255, 255, 255), width=4)
    d.rounded_rectangle([x - ancho // 2 - 12, cy - alto_et // 2,
                         x + ancho // 2 + 12, cy + alto_et // 2],
                        radius=alto_et // 2, fill=(255, 255, 255, 235))
    d.text((x, cy), etiqueta, font=fuente, fill=(17, 24, 39), anchor="mm")


def generar_mapa(ubicaciones, destino: str | None = None,
                 ancho: int = ANCHO, alto: int = ALTO) -> dict:
    """
    Escribe el PNG del mapa y devuelve el resumen.

    `ubicaciones` es la lista que devuelve `datos.ubicaciones_hoy()`: dicts con
    `nombre`, `lat`, `lon` y opcionalmente `precision`.
    """
    destino = destino or _ruta_destino()
    ubicaciones = [u for u in (ubicaciones or []) if u.get("lat") is not None
                   and u.get("lon") is not None]

    if not ubicaciones:
        return _mapa_vacio(destino, ancho, alto, 0)

    puntos = [(float(u["lat"]), float(u["lon"])) for u in ubicaciones]
    lat_c = sum(p[0] for p in puntos) / len(puntos)
    lon_c = sum(p[1] for p in puntos) / len(puntos)
    z = _elegir_zoom(puntos, ancho, alto)

    # Centro y recuadro en píxeles del mundo, ya en la escala elegida.
    cx, cy = _proyeccion(lat_c, lon_c, z)
    izq, arr = cx - ancho / 2, cy - alto / 2

    lienzo = Image.new("RGB", (ancho, alto), (226, 226, 226))
    d = ImageDraw.Draw(lienzo, "RGBA")

    _pegar_teselas(lienzo, z, ancho, alto, izq, arr)
    d = ImageDraw.Draw(lienzo, "RGBA")

    fuente = _fuente(_etiquetas_para(len(ubicaciones), z))
    colores = [(220, 38, 38), (37, 99, 235), (22, 163, 74), (217, 119, 6),
               (147, 51, 234), (13, 148, 136), (219, 39, 119), (101, 163, 13)]
    for i, (u, (lat, lon)) in enumerate(zip(ubicaciones, puntos)):
        px, py = _proyeccion(lat, lon, z)
        _marcar(d, px - izq, py - arr, u.get("nombre") or "?",
                colores[i % len(colores)], fuente, idx=i)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    lienzo.save(destino, "PNG", optimize=True)

    return {
        "ruta": "/media/maps/campo.png",
        "archivo": destino,
        "personas": len(ubicaciones),
        "zoom": z,
        "lat": lat_c,
        "lon": lon_c,
    }


def _pegar_teselas(lienzo, z: int, ancho: int, alto: int, izq: float, arr: float) -> int:
    """
    Trae las teselas que tocan el recuadro y las pega en su lugar.

    EN PARALELO, a propósito: un mapa de 1920x1080 son del orden de 20 teselas, y
    bajadas en serie tardó 25 s medidos — demasiado para meterlo en el ciclo del
    snapshotter, que es de 2 minutos. Con 8 hilos baja a unos 4 s.

    Se baja la cantidad, no la calidad: si una tesela falla, el hueco se ve y se
    nota, en vez de inventarse un cuadro liso.
    """
    n = 2 ** z
    x0 = int(math.floor(izq / _TILE))
    x1 = int(math.floor((izq + ancho) / _TILE))
    y0 = int(math.floor(arr / _TILE))
    y1 = int(math.floor((arr + alto) / _TILE))

    pendientes = [(tx, ty) for ty in range(max(0, y0), min(n - 1, y1) + 1)
                             for tx in range(max(0, x0), min(n - 1, x1) + 1)]
    if not pendientes:
        return 0

    import concurrent.futures as cf
    pegadas = 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for (tx, ty), t in zip(pendientes, ex.map(
                lambda xy: _descargar_tesela(z, xy[0], xy[1]), pendientes)):
            if t is None:
                continue
            lienzo.paste(t, (int(tx * _TILE - izq), int(ty * _TILE - arr)))
            pegadas += 1
    return pegadas


def _mapa_vacio(destino: str, ancho: int, alto: int, personas: int = 0) -> dict:
    """Sin ubicaciones: un mapa del centro de la ciudad y un aviso. Nunca un PNG
    en blanco, porque en la TV un blanco no dice si falló o si no hay nadie."""
    z = _ZOOM_VACIO
    cx, cy = _proyeccion(_CENTRO_VACIO[0], _CENTRO_VACIO[1], z)
    izq, arr = cx - ancho / 2, cy - alto / 2
    lienzo = Image.new("RGB", (ancho, alto), (226, 226, 226))
    _pegar_teselas(lienzo, z, ancho, alto, izq, arr)

    d = ImageDraw.Draw(lienzo, "RGBA")
    d.rectangle([0, alto / 2 - 150, ancho, alto / 2 + 150], fill=(15, 23, 42, 205))
    grande = _fuente(74)
    d.text((ancho / 2, alto / 2 - 34), "Sin reportes de ubicación hoy",
           font=grande, fill=(255, 255, 255), anchor="mm")
    d.text((ancho / 2, alto / 2 + 46),
           "Cada ingeniero publica la suya con el botón «Aquí estoy» de la app",
           font=_fuente(34), fill=(203, 213, 225), anchor="mm")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    lienzo.save(destino, "PNG", optimize=True)
    return {"ruta": "/media/maps/campo.png", "archivo": destino,
            "personas": 0, "zoom": z, "lat": _CENTRO_VACIO[0], "lon": _CENTRO_VACIO[1]}


def mapa_ingenieria(ubicaciones) -> dict:
    """
    Punto de entrada del snapshotter: regenera sólo si hace falta.

    La clave de caché es el conjunto de (persona, lat, lon) redondeados. Con eso
    una persona que se mueve milímetro no obliga a bajar 40 teselas, y alguien
    que sí se movió rehace el mapa aunque dentro de los 5 minutos.
    """
    ubicaciones = [u for u in (ubicaciones or []) if u.get("lat") is not None
                   and u.get("lon") is not None]
    clave = tuple(sorted(
        (u.get("nombre") or "", round(float(u["lat"]), 5), round(float(u["lon"]), 5))
        for u in ubicaciones))
    destino = _ruta_destino()

    with _candado:
        ahora = time.time()
        if (_cache["clave"] == clave and _cache["ruta"] and ahora - _cache["ts"] < _CADUCIDAD_S
                and os.path.exists(destino)):
            r = dict(_cache["ruta"])
            r["cache"] = True
            return r

        info = generar_mapa(ubicaciones, destino=destino)
        _cache.update({"clave": clave, "ruta": info, "ts": ahora})
        info["cache"] = False
        return info
