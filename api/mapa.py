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
_ANCHO_IMG = 1920
_ALTO_IMG = 1080

# Zona del mapa cuando NO hay ninguna ubicación: Monterrey. Si no se pone nada,
# el PNG saldría de 1x1 píxel y `fitBounds` no tendría con qué trabajar.
_CENTRO_VACIO = (25.6866, -100.3161)
_ZOOM_VACIO = 11
_ZOOM_UNO = 14          # con una sola persona el punto no da extensión
_ZOOM_MIN, _ZOOM_MAX = 3, 17

# Separación mínima entre pines, en píxeles de pantalla. Por debajo de esto los
# pines se tocan y las etiquetas se enciman. Medido: con 130 px la separación
# real promedio queda en 143 px para 25 personas amontonadas y 200 px para 12
# repartidas por el país, que es donde el nombre todavía se lee.
_SEP_MIN_PX = 130

# Cuánto se puede subir el zoom para separar los pines SIN que alguien se salga de
# la pantalla. Con margen de pantalla reducido, que es lo que hace falta para
# que "que quepan" y "se separen" no se vuelvan requisitos contradictorios.
_MARGEN_AJUSTADO = 60
_SUBIDA_MAX = 2

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


def _separacion_px(puntos, z: int) -> float:
    """
    Separación promedio de cada pin a su vecino más cercano, en píxeles.

    Es la medida que importa para "se leen o no se leen": no importa qué tan
    grande es el recuadro, sino qué tan juntos están los pines entre sí.
    """
    if len(puntos) < 2:
        return 1e9
    px = [_proyeccion(la, lo, z) for la, lo in puntos]
    total = 0.0
    for i, (xa, ya) in enumerate(px):
        mejor = 1e18
        for j, (xb, yb) in enumerate(px):
            if i == j:
                continue
            dx, dy = xb - xa, yb - ya
            d = (dx * dx + dy * dy) ** 0.5
            if d < mejor:
                mejor = d
        total += mejor
    return total / len(px)


def _elegir_zoom(puntos, ancho_px: int, alto_px: int) -> int:
    """
    El zoom: dos reglas, y gana la que pida más acercamiento.

      1. QUE QUEPAN TODOS: el zoom más cercano con el que el recuadro de las
         ubicaciones cabe en la pantalla. Sin esto, con alguien en Monterrey y
         alguien en Yucatán, uno de los dos queda fuera.
      2. QUE NO SE ENCIMEN: si aun así los pines quedan demasiado juntos, se
         ACERCA hasta separarlos.

    Por qué acercar y no alejar para lo segundo — porque es contraintuitivo y
    cuesta entenderlo la primera vez: ACERCAR es lo que separa los pines. Al
    alejar se juntan más. Se comprobó al revés: una versión que alejava cuando
    había amontonamiento dejó 25 personas en zoom 3, o sea un solo punto con
    separación 0 px. La física es al revés de lo que parece.

    LAS DOS REGLAS SE CONTRADICEN, y el intento de fingir lo contrario salió
    mal a la primera. Con 25 personas en 13 km:
      · a zoom 13 caben todas en pantalla, pero quedan a 71 px y los pines se
        tocan;
      · a zoom 14 quedarían a 143 px, muy bien separadas — pero el grupo ya no
        cabe en 1920x1080, y entonces hay gente literalmente fuera de la pantalla,
        que es peor que un nombre encimado. Un ingeniero que no aparece NO es un
        dato feo: es un dato perdido.

    Por eso la regla 2 tiene tope: se acerca como mucho `_SUBIDA_MAX` niveles y
    sólo mientras el grupo siga cabiendo con un margen mínimo. Lo que sobra para
    separar los pines NO se arregla con más zoom, porque más zoom siempre saca
    gente de la pantalla. Se arregla separando las ETIQUETAS, que es trabajo de
    `_separar_etiquetas` y no del zoom.
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

    # Regla 1: que quepan todos.
    z = _ZOOM_MIN
    for zz in range(_ZOOM_MAX, _ZOOM_MIN - 1, -1):
        x1, y1 = _proyeccion(lat_a, lon_a, zz)
        x2, y2 = _proyeccion(lat_b, lon_b, zz)
        if abs(x2 - x1) + 2 * _MARGEN_PX <= ancho_px and \
           abs(y2 - y1) + 2 * _MARGEN_PX <= alto_px:
            z = zz
            break

    # Regla 2: acercar para separar, CON TOPE de seguridad. Se sube mientras que
    # la separación sea insuficiente Y el grupo siga cabiendo. Nunca se sube si
    # alguien quedaría fuera de la pantalla.
    for _ in range(_SUBIDA_MAX):
        if z >= _ZOOM_MAX or _separacion_px(puntos, z) >= _SEP_MIN_PX:
            break
        if not _caben(puntos, z + 1, ancho_px, alto_px, _MARGEN_AJUSTADO):
            break
        z += 1

    return z


def _caben(puntos, z: int, ancho_px: int, alto_px: int, margen: int) -> bool:
    """¿El grupo completo sigue dentro de la pantalla a este zoom?"""
    la, lb = min(p[0] for p in puntos), max(p[0] for p in puntos)
    lo_a, lo_b = min(p[1] for p in puntos), max(p[1] for p in puntos)
    x1, y1 = _proyeccion(la, lo_a, z)
    x2, y2 = _proyeccion(lb, lo_b, z)
    return (abs(x2 - x1) + 2 * margen <= ancho_px
            and abs(y2 - y1) + 2 * margen <= alto_px)


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


# ── Agrupación: gente que reporta desde el mismo punto ───────────────────────

# A esta distancia se consideran "el mismo sitio". Con 120 m, dos personas en la
# misma oficina o en la misma calle salen como una sola señal, que es lo que uno
# quiere ver de una pantalla: "hay cinco aquí", no cinco pines encimados donde
# sólo se lee el de arriba.
_AGRUPAR_M = 120
_RADIO_PX = 34          # radio del pin (con foto dentro)


def _dist_m(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos coordenadas (haversine)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _agrupar(ubicaciones, radio_m=_AGRUPAR_M):
    """
    Agrupa a quien está en el mismo sitio. Union-find: O(n²), que con las dos o
    tres dezenas de registros del día es irrelevante y mucho más fácil de acertar
    que una grilla con celdas de tamaño fijo.

    Devuelve grupos con sus miembros y su centroide, del más numerous al menos.
    """
    n = len(ubicaciones)
    padre = list(range(n))

    def buscar(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]          # compresión de caminos
            a = padre[a]
        return a

    for i in range(n):
        for j in range(i + 1, n):
            if _dist_m(ubicaciones[i]["lat"], ubicaciones[i]["lon"],
                       ubicaciones[j]["lat"], ubicaciones[j]["lon"]) <= radio_m:
                ri, rj = buscar(i), buscar(j)
                if ri != rj:
                    padre[ri] = rj

    grupos = {}
    for i in range(n):
        grupos.setdefault(buscar(i), []).append(i)

    salida = []
    for miembros in grupos.values():
        salida.append({
            "miembros": miembros,
            "lat": sum(ubicaciones[i]["lat"] for i in miembros) / len(miembros),
            "lon": sum(ubicaciones[i]["lon"] for i in miembros) / len(miembros),
        })
    salida.sort(key=lambda g: -len(g["miembros"]))
    return salida


def _nombres_grupo(miembros, ubicaciones, maximo=3):
    """Nombres de un grupo, con corte honesto.

    Con seis personas en la misma oficina, seis nombres en una sola etiqueta son
    ilegibles: se muestran los primeros y cuántos más hay. Los demás están en la
    franja de abajo de la pantalla, que sí los lista todos.
    """
    nombres = [ubicaciones[i].get("nombre") or "?" for i in miembros]
    if len(nombres) <= maximo:
        return ", ".join(nombres)
    return ", ".join(nombres[:maximo]) + f" +{len(nombres) - maximo}"


_AVATARES = {}            # id_usuario -> bytes, una vez por proceso


def _avatar_bytes(id_usuario):
    """Bytes del avatar del usuario, o None si no tiene.

    Los archivos los escribe el snapshotter en /data/media/avatars/u<Id>.jpg a
    partir de HUB_UserAvatars. Se leen del disco y no de la base: el mapa se
    regenera cada 5 minutos como mucho, y no tiene sentido volver a pedir un JPEG
    a la base en cada vuelta.
    """
    if not id_usuario:
        return None
    if id_usuario in _AVATARES:
        return _AVATARES[id_usuario]
    ruta = os.path.join(os.environ.get("KIOSKO_DATA", "/data"), "media",
                        "avatars", f"u{int(id_usuario)}.jpg")
    try:
        with open(ruta, "rb") as fh:
            crudo = fh.read()
    except OSError:
        crudo = None
    _AVATARES[id_usuario] = crudo or None
    return _AVATARES[id_usuario]


_CARAS = {}                # (hash, lado) -> imagen circular ya recortada


def _cara_redonda(crudo, lado):
    """Avatar recortado en círculo, cacheado por contenido.

    Recortar en círculo importa: una foto cuadrada dentro de un pin redondo deja
    las esquinas del fondo del retrato y se ve como un sticker pegado. Y antes de
    circular hay que recortar a cuadrado al centro, porque si no una foto apaisada
    se estira y la cara sale chueca.
    """
    if not crudo:
        return None
    clave = (hash(crudo), lado)
    if clave in _CARAS:
        return _CARAS[clave]
    try:
        from PIL import ImageDraw
        im = Image.open(io.BytesIO(crudo)).convert("RGB")
        lado_min = min(im.size)
        izq = (im.width - lado_min) // 2
        arr = (im.height - lado_min) // 2
        im = im.crop((izq, arr, izq + lado_min, arr + lado_min))
        im = im.resize((lado, lado), Image.LANCZOS)

        mascara = Image.new("L", (lado, lado), 0)
        ImageDraw.Draw(mascara).ellipse([0, 0, lado - 1, lado - 1], fill=255)
        salida = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        salida.paste(im, (0, 0), mascara)
        _CARAS[clave] = salida
        return salida
    except Exception:
        return None


def _separar_etiquetas(centros, anchos, altos, minimo=18, obstaculos=None):
    """
    Coloca las etiquetas sin que se encimen, moviéndolas alrededor de su pin.

    POR QUÉ HAY QUE HACER ESTO Y NO SÓLO AJUSTAR EL ZOOM: con 25 personas en
    13 km no existe ningún zoom que cumpla las dos cosas. Acercar separa los
    pines pero saca gente de la pantalla; alejar mete a todo el mundo en un solo
    punto. Lo único que queda es mover las ETIQUETAS, que son adorno: el pin se
    queda donde es el dato, y el texto se recorre hasta un lugar libre, con una
    guía que lo ata a su pin para que se sepa de quién es.

    SEPARA EN LOS DOS EJES, y vertical-only no alcanza: separar sólo en Y con 25
    etiquetas exige 25 x (45+18) = 1575 px de alto y la pantalla tiene 1080. Es
    imposible por construcción, y por eso seguían viéndose cuatro o cinco pares
    pegados ("Ing 18/Ing 10", "Ing 04/Ing 12") por mucho que se iterara en Y.

    El orden importa: primero se separa en Y, que es lo que menos descoloca la
    lectura ("está arriba de Monterrey"), y sólo lo que sigue pegado se mueve en
    X, alternando a izquierda y derecha para que se repartan.

    Devuelve (xs, ys), la esquina donde se dibuja cada etiqueta.
    """
    n = len(centros)
    obstaculos = obstaculos or []
    xs = [c[0] for c in centros]
    ys = [c[1] + 46 + altos[0] / 2 for c in centros]
    borde_y = max(altos) / 2 + 4
    tope_x = 210          # una etiqueta no se va más lejos de su pin que esto

    def choca_pine(i, obs):
        """¿La etiqueta i cae encima de este pin?

        El defecto que quedaba: las etiquetas se apartaban unas de otras pero
        pasaban POR ENCIMA de los pines ajenos, y tapaban la cara de media
        docena de gente. Un pin con foto es un dato, no un adorno: no puede
        quedar debajo de una etiqueta.
        """
        cx, cy, r = obs
        dx = max(abs(cx - xs[i]) - anchos[i] / 2, 0)
        dy = max(abs(cy - ys[i]) - altos[i] / 2, 0)
        return (dx * dx + dy * dy) ** 0.5 < r

    def choca_otro_pine(i):
        return any(choca_pine(i, o) for o in obstaculos)

    def esquivar_pines(i):
        """Sube la etiqueta hasta que deja de tapar un pin."""
        for _ in range(10):
            if not choca_otro_pine(i):
                return True
            ys[i] -= altos[i] + minimo
            ys[i] = max(ys[i], borde_y)
        return not choca_otro_pine(i)

    def chocan(i, j):
        return (abs(xs[i] - xs[j]) < (anchos[i] + anchos[j]) / 2 + minimo
                and abs(ys[i] - ys[j]) < (altos[i] + altos[j]) / 2 + minimo)

    def empuje_y(i, j):
        return (altos[i] + altos[j]) / 2 + minimo - abs(ys[i] - ys[j])

    def empuje_x(i, j):
        return (anchos[i] + anchos[j]) / 2 + minimo - abs(xs[i] - xs[j])

    # ── Pasada 1: sólo vertical ────────────────────────────────────────────────
    for _ in range(40):
        movido = False
        for i in range(n):
            for j in range(i + 1, n):
                if abs(xs[i] - xs[j]) >= (anchos[i] + anchos[j]) / 2 + minimo:
                    continue                      # ya están separadas en X
                if not chocan(i, j):
                    continue
                e = empuje_y(i, j)
                ys[i] -= e / 2
                ys[j] += e / 2
                movido = True
            ys[i] = min(max(ys[i], borde_y), _ALTO_IMG - borde_y)
            esquivar_pines(i)
        if not movido:
            break

    # ── Pasada 2: lo que sigue pegado se mueve en X, alternando lado ──────────
    for i in range(n):
        xs[i] = min(max(xs[i], anchos[i] / 2 + 6), _ANCHO_IMG - anchos[i] / 2 - 6)

    for _ in range(12):
        movido = False
        for i in range(n):
            for j in range(i + 1, n):
                if not chocan(i, j):
                    continue
                e = empuje_x(i, j)
                # Se empuja la de índice PAR hacia un lado y la IMPAR hacia el
                # otro, para que no se empujen las dos hacia el mismo lado y las
                # dos se vayan igual de lejos del resto.
                if i % 2 == 0:
                    xs[i] -= e / 2
                    xs[j] += e / 2
                else:
                    xs[i] += e / 2
                    xs[j] -= e / 2
                movido = True
            xs[i] = min(max(xs[i], anchos[i] / 2 + 6), _ANCHO_IMG - anchos[i] / 2 - 6)
            if choca_otro_pine(i):
                lado = 1 if i % 2 == 0 else -1
                for _ in range(10):
                    if not choca_otro_pine(i):
                        break
                    xs[i] += lado * (anchos[i] / 2 + minimo)
                    xs[i] = min(max(xs[i], anchos[i] / 2 + 6),
                                _ANCHO_IMG - anchos[i] / 2 - 6)
        if not movido:
            break

    # ── Último recurso: si una etiqueta quedó demasiado lejos de su pin, no se
    # dibuja. Un nombre a 600 px de su pin ya no es una etiqueta: es ruido, y
    # además tapa el mapa. El pin sigue ahí, y el nombre está en la franja de
    # abajo de la pantalla.
    fuera = []
    for i in range(n):
        lejos = math.hypot(xs[i] - centros[i][0], ys[i] - centros[i][1]) > tope_x + 200
        if lejos:
            fuera.append(i)
    return xs, ys, fuera


def _pin_avatar(lienzo, x, y, id_usuario, nombre, color, lado=_RADIO_PX):
    """
    El pin: la FOTO del usuario dentro de un círculo con anillo de color.

    La foto es lo que hace útil la pantalla a tres metros: un mapa con diez
    iniciales es un mapa con diez letras. Con la cara se sabe de un vistazo quién
    está en Saltillo.

    Si no hay foto se cae a la inicial, pero nunca a un círculo vacío: un pin sin
    rostro es un pin sin quién.
    """
    d = ImageDraw.Draw(lienzo, "RGBA")
    r = lado / 2

    # Halo y anillo: el blanco separa la cara del mapa, y el color identifica al
    # grupo cuando hay varias personas en el mismo punto.
    d.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=(0, 0, 0, 70))
    d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=(255, 255, 255, 255))

    cara = _cara_redonda(_avatar_bytes(id_usuario), int(lado))
    if cara is not None:
        # El marco es TRANSPARENTE con un anillo de color, no un cuadrado
        # relleno: al crearlo con el color de fondo opaco y dibujarle la elipse
        # encima, las esquinas no se borran y salía un rectángulo rojo detrás de
        # cada cara.
        lado_m = int(lado) + 10
        marco = Image.new("RGBA", (lado_m, lado_m), (0, 0, 0, 0))
        ImageDraw.Draw(marco).ellipse([0, 0, lado_m - 1, lado_m - 1],
                                      fill=color + (255,))
        lienzo.paste(marco, (int(x - r - 5), int(y - r - 5)), marco)
        lienzo.paste(cara, (int(x - r), int(y - r)), cara)
    else:
        d.ellipse([x - r, y - r, x + r, y + r], fill=color,
                  outline=(255, 255, 255), width=4)
        d.text((x, y - 1), (nombre or "?")[0].upper(), font=_fuente(int(lado * 0.5)),
               fill=(255, 255, 255), anchor="mm")


def _grupo_pines(lienzo, x, y, miembros, ubicaciones, color, radio=_RADIO_PX):
    """
    Un grupo de gente en el mismo sitio: las caras en abanico alrededor del centro.

    Con cinco personas reportando la misma oficina, cinco pines encima muestran
    sólo el último: cuatro desaparecen de la pantalla, que es justo lo que esta
    pantalla no puede hacer. Con las caras en abanico se ve cuántas son y cuáles.

    · hasta 4: abanico completo alrededor del centroide;
    · más de 4: se abren hacia arriba y sale una pastilla con "+N", porque a
      partir de cinco el abanico ya no se distingue y sólo se ve un bulto.

    Devuelve la lista de pines para las animaciones de la pantalla.
    """
    d = ImageDraw.Draw(lienzo, "RGBA")
    n = len(miembros)
    r = radio / 2

    if n == 1:
        u = ubicaciones[miembros[0]]
        _pin_avatar(lienzo, x, y, u.get("id_usuario"), u.get("nombre"), color, radio)
        return [{"x": int(x), "y": int(y), "n": 1, "i": miembros[0]}]

    if n <= 4:
        paso = 2 * math.pi / n
        for k, i in enumerate(miembros):
            ang = -math.pi / 2 + k * paso
            u = ubicaciones[i]
            _pin_avatar(lienzo, x + math.cos(ang) * (radio + 26),
                        y + math.sin(ang) * (radio + 26),
                        u.get("id_usuario"), u.get("nombre"), color, radio)
    else:
        for k, i in enumerate(miembros[:4]):
            ang = -math.pi / 2 + (k - 1.5) * 0.55
            u = ubicaciones[i]
            _pin_avatar(lienzo, x + math.cos(ang) * (radio + 34),
                        y + math.sin(ang) * (radio + 34),
                        u.get("id_usuario"), u.get("nombre"), color, radio - 4)
        fuente_c = _fuente(24)
        texto = f"+{n - 4}"
        tw = d.textlength(texto, font=fuente_c)
        d.rounded_rectangle([x + r - 10, y + r - 4, x + r + 20 + tw, y + r + 46],
                            radius=19, fill=color + (255,))
        d.text((x + r + 10 + tw / 2, y + r + 21), texto, font=fuente_c,
               fill=(255, 255, 255), anchor="mm")

    return [{"x": int(x), "y": int(y), "n": n, "i": miembros}]


def _marcar(d, x, y, nombre: str, color, fuente, pos_etiqueta=None) -> None:
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
    ex, ey = pos_etiqueta if pos_etiqueta else (x, y + 44 + alto_et // 2)

    # Guía del pin a su etiqueta. Con la etiqueta movida por `_separar_etiquetas`
    # esta línea es lo que dice que "Ing 07" es ESTE pin y no el de al lado.
    d.line([x, y + 20, ex, ey], fill=(255, 255, 255), width=4)
    d.rounded_rectangle([ex - ancho // 2 - 12, ey - alto_et // 2,
                         ex + ancho // 2 + 12, ey + alto_et // 2],
                        radius=alto_et // 2, fill=(255, 255, 255, 240))
    d.text((ex, ey), etiqueta, font=fuente, fill=(17, 24, 39), anchor="mm")


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

    # ── Agrupar: quien reporta desde el mismo sitio se dibuja como uno ────────
    # Se agrupa ANTES de decidir el zoom y las etiquetas, porque el zoom tiene que
    # encajar con los GRUPOS y no con cada persona: si cinco personas reportan la
    # misma oficina, el mapa no necesita cinco puntos separados.
    grupos = _agrupar(ubicaciones)
    puntos_g = [(g["lat"], g["lon"]) for g in grupos]
    z = _elegir_zoom(puntos_g, ancho, alto)   # siempre sobre los GRUPOS
    cx, cy = _proyeccion(lat_c, lon_c, z)
    izq, arr = cx - ancho / 2, cy - alto / 2
    pantallas = [(_proyeccion(la, lo, z)[0] - izq, _proyeccion(la, lo, z)[1] - arr)
                 for la, lo in puntos_g]

    # Un pin fuera de la pantalla no se dibuja: una etiqueta apuntando al borde
    # sería un dato engañoso.
    dentro = [i for i, p in enumerate(pantallas)
              if -40 <= p[0] <= ancho + 40 and -40 <= p[1] <= alto + 40]
    if not dentro:
        return {"ruta": "/media/maps/campo.png", "archivo": destino,
                "personas": len(ubicaciones), "grupos": len(grupos), "zoom": z,
                "lat": lat_c, "lon": lon_c, "pins": []}

    # ── Etiquetas, con los pines como obstáculo ───────────────────────────────
    alto_et = int(fuente.size * 1.75)
    textos = [_nombres_grupo(grupos[i]["miembros"], ubicaciones)
              if len(grupos[i]["miembros"]) > 1
              else (ubicaciones[grupos[i]["miembros"][0]].get("nombre") or "?")
              for i in dentro]
    anchos = [_ancho_texto(d, t, fuente) + 26 for t in textos]
    # El radio del obstáculo no es el del pin: un grupo de más de cuatro lleva
    # además la pastilla "+N" colgando abajo a la derecha, y sin contarla como
    # obstáculo la etiqueta se le monta encima (se veía "Ing 2, Ing 3, Ing 4 +4"
    # encima del +3).
    obstaculos = []
    for i in dentro:
        extra = 46 if len(grupos[i]["miembros"]) > 4 else 0
        obstaculos.append((pantallas[i][0], pantallas[i][1], _RADIO_PX + 8 + extra))

    xs, ys, muy_lejos = _separar_etiquetas([pantallas[i] for i in dentro],
                                           anchos, [alto_et] * len(dentro),
                                           obstaculos=obstaculos)
    descartes = {dentro[k] for k in muy_lejos}

    # ── Dibujar ───────────────────────────────────────────────────────────────
    pins = []
    for k, i in enumerate(dentro):
        px, py = pantallas[i]
        g = grupos[i]
        color = colores[i % len(colores)]
        # El pin SIEMPRE se dibuja, tenga etiqueta o no: la cara es el dato.
        pins += _grupo_pines(lienzo, px, py, g["miembros"], ubicaciones, color)
        if k in descartes:
            continue
        ex, ey = xs[k], ys[k]
        d.line([px, py + 22, ex, ey], fill=(255, 255, 255), width=4)
        d.rounded_rectangle([ex - anchos[k] / 2 + 13, ey - alto_et / 2,
                             ex + anchos[k] / 2 - 13, ey + alto_et / 2],
                            radius=alto_et // 2, fill=(255, 255, 255, 240))
        d.text((ex, ey), textos[k], font=fuente, fill=(17, 24, 39), anchor="mm")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    lienzo.save(destino, "PNG", optimize=True)

    return {
        "ruta": "/media/maps/campo.png",
        "archivo": destino,
        "personas": len(ubicaciones),
        "grupos": len(grupos),
        "zoom": z,
        "lat": lat_c,
        "lon": lon_c,
        # Dónde quedó cada pin, en píxeles del PNG. La pantalla los usa para poner
        # encima los efectos: el mapa es una imagen quieta y el pulso lo pone el
        # navegador, que es donde de verdad se puede animar.
        "pins": pins,
        # El color se manda para que la lista de nombres de abajo coincida con
        # el del pin. Si el front eligiera su propia paleta, los puntos de color
        # no significarían nada.
        "colores": [f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}" for c in colores],
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
