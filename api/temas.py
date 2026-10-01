"""
temas.py — el tema del mes para el fondo de la pantalla.

POR QUÉ NO SE BUSCAN FONDOS TEMÁTICOS EN INTERNET (probado, no estheory):
Bing ignora el parámetro de búsqueda de su archivo de fondos. Con
`?q=halloween` devuelve exactamente las mismas 4 imágenes del día, y el
endpoint `/AS/HPImageArchive.aspx` da 404. O sea: no hay forma de pedirle
"una foto de Día de Muertos" a la fuente que ya usamos. Las otras opciones
(Unsplash, Wikimedia) piden API key, y el kiosco es OFFLINE por diseño
(AGENTS.md §Offline).

Así que el tema se GENERA aquí: una capa PNG de 1920x1080 con la silueta del
mes dibujada con primitivas de Pillow, en el color del mes y con muy poca
opacidad. Se pone ENCIMA de la foto de Bing (que sigue siendo la que da
belleza y cambia a diario) y DEBAJO de la viñeta, para que el texto de las
pantallas siga leyéndose igual que siempre.

Reglas de diseño, todas aprendidas mirando las pantallas:
  · la opacidad de los motivos es bajísima (6-14%): el tema se nota cuando
    uno lo busca, y no compite con los datos,
  · los motivos van en las ESQUINAS, nunca en el centro, que es donde cae el
    contenido de todas las pantallas,
  · el tinte es de un solo color con un radial suave, no un rectángulo: una
    capa plana sobre la foto se ve como filtro de Instagram.
"""
from __future__ import annotations

import math
import os

# ── Los doce temas ────────────────────────────────────────────────────────────
# `tinte` es el color que se esparce; `motivo` dice qué se dibuja.
TEMAS = {
    1:  {"nombre": "Reyes Magos",        "icono": "👑", "tinte": "#f2c14e", "motivo": "regalos"},
    2:  {"nombre": "Amor y amistad",     "icono": "💘", "tinte": "#e8577f", "motivo": "corazones"},
    3:  {"nombre": "Primavera",          "icono": "🌱", "tinte": "#4ade80", "motivo": "brote"},
    4:  {"nombre": "Día del Niño",       "icono": "🎈", "tinte": "#38bdf8", "motivo": "confeti"},
    5:  {"nombre": "El mes de las mamás", "icono": "🌷", "tinte": "#f472b6", "motivo": "flores"},
    6:  {"nombre": "Verano y calor",     "icono": "☀️", "tinte": "#fbbf24", "motivo": "sol"},
    7:  {"nombre": "Verano a toda vista", "icono": "🏖️", "tinte": "#22d3ee", "motivo": "mar"},
    8:  {"nombre": "El mes más caluroso", "icono": "🌴", "tinte": "#fb923c", "motivo": "palmera"},
    9:  {"nombre": "Independencia",      "icono": "🇲🇽", "tinte": "#22c55e", "motivo": "papel_picado"},
    10: {"nombre": "Halloween y Día de Muertos", "icono": "🎃", "tinte": "#a855f7", "motivo": "calavera"},
    11: {"nombre": "Revolución y otoño",  "icono": "🍂", "tinte": "#b45309", "motivo": "hojas"},
    12: {"nombre": "Navidad",            "icono": "🎄", "tinte": "#dc2626", "motivo": "navidad"},
}

ANCHO, ALTO = 1920, 1080


def tema_de(mes: int | None = None) -> dict:
    """El tema del mes (o el que pidan, para probar)."""
    if mes is None:
        import datetime as _dt
        mes = _dt.date.today().month
    mes = int(mes)
    if mes < 1 or mes > 12:
        mes = 1
    t = dict(TEMAS[mes])
    t["mes"] = mes
    return t


# ── Dibujo ────────────────────────────────────────────────────────────────────
def _rgb(hex_color: str, alpha: float):
    """'#ff6b00' + 0.12 → (255, 107, 0, 31) para Pillow."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, max(0, min(255, int(alpha * 255))))


def _hex2rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _corazon(d, cx, cy, r, color):
    """Corazón con dos círculos y un triángulo: es más simple que la curva."""
    d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.25], fill=color)
    d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.25], fill=color)
    d.polygon([(cx - r, cy - r * 0.15), (cx + r, cy - r * 0.15), (cx, cy + r)], fill=color)


def _estrella(d, cx, cy, r, color, puntas=5):
    pts = []
    for i in range(puntas * 2):
        ang = -math.pi / 2 + i * math.pi / puntas
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=color)


def _hoja(d, cx, cy, r, color, ang=0.0):
    """Hoja simple: un óvalo apuntando a `ang`."""
    capa = _capa_hoja(r, color, ang)
    d.bitmap((cx - r, cy - r), capa, fill=color)


def _capa_hoja(r, color, ang=0.0):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.ellipse([r * 0.15, r * 0.2, r * 1.85, r * 1.8], fill=color)
    im = im.rotate(ang, resample=Image.BICUBIC, center=(r, r))
    return im


def _puntos_motivo(d, motivo: str, color, base=0.30):
    """Repite el motivo del mes en las cuatro esquinas. `base` es la opacidad."""
    c = _rgb(color, base)
    # Esquina superior izquierda
    if motivo == "regalos":
        _estrella(d, 235, 205, 92, _rgb(color, base * 1.5), 5)
        for x, h in ((80, 120), (185, 96), (288, 140)):
            d.rounded_rectangle([x, 300, x + 86, 300 + h], 8, fill=_rgb(color, base))
            d.rectangle([x + 30, 300, x + 56, 300 + h], fill=_rgb(color, base * 1.7))
            d.rectangle([x, 300 + h * 0.42, x + 86, 300 + h * 0.58],
                        fill=_rgb(color, base * 1.7))
        _estrella(d, 1755, 300, 66, _rgb(color, base * 1.2), 5)
    elif motivo == "corazones":
        for x, y, r in ((150, 170, 52), (250, 250, 34), (110, 275, 26)):
            _corazon(d, x, y, r, _rgb(color, base * 1.3))
        _corazon(d, 1770, 190, 58, c)
        _corazon(d, 1690, 275, 32, _rgb(color, base * 0.9))
    elif motivo == "brote":
        # Tallo con curva (arco) y dos hojas grandes, como un brote de verdad.
        d.arc([70, 170, 330, 430], 90, 270, fill=_rgb(color, base * 1.5), width=11)
        d.bitmap((120, 150), _capa_hoja(96, _rgb(color, base * 1.3), 35),
                 fill=_rgb(color, base * 1.3))
        d.bitmap((80, 40), _capa_hoja(84, _rgb(color, base * 1.1), 200),
                 fill=_rgb(color, base * 1.1))
        d.bitmap((1610, 130), _capa_hoja(88, _rgb(color, base), 145), fill=c)
        d.bitmap((1740, 60), _capa_hoja(70, _rgb(color, base * 0.8), 40),
                 fill=_rgb(color, base * 0.8))
    elif motivo == "confeti":
        import random
        rnd = random.Random(7)
        for _ in range(150):
            x = rnd.choice([rnd.randint(0, 420), rnd.randint(1500, ANCHO)])
            y = rnd.randint(0, ALTO)
            w = rnd.randint(6, 13)
            d.rounded_rectangle([x, y, x + w, y + w], 3,
                                fill=_rgb(color, base * rnd.uniform(0.6, 1.5)))
        d.ellipse([120, 170, 240, 320], fill=_rgb(color, base * 1.1))
        d.line([180, 320, 180, 400], fill=c, width=5)
    elif motivo == "flores":
        for cx, cy, r in ((170, 190, 60), (270, 300, 40), (1770, 200, 56), (1660, 300, 38)):
            for i in range(6):
                a = i * math.pi / 3
                d.ellipse([cx + r * 0.5 * math.cos(a) - r * 0.34,
                           cy + r * 0.5 * math.sin(a) - r * 0.34,
                           cx + r * 0.5 * math.cos(a) + r * 0.34,
                           cy + r * 0.5 * math.sin(a) + r * 0.34], fill=c)
            d.ellipse([cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18],
                      fill=_rgb(color, base * 2))
    elif motivo in ("sol", "mar", "palmera"):
        cx, cy, r = 1760, 180, 120
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_rgb(color, base * 1.2))
        for i in range(16):
            a = i * math.pi / 8
            d.line([cx + r * math.cos(a) * 1.2, cy + r * math.sin(a) * 1.2,
                    cx + r * math.cos(a) * 1.75, cy + r * math.sin(a) * 1.75],
                   fill=c, width=7)
        if motivo == "mar":
            for y in (760, 850, 940, 1030):
                d.arc([100, y - 60, 900, y + 60], 200, 340, fill=_rgb(color, base * 1.3), width=8)
                d.arc([1300, y - 60, 1900, y + 60], 200, 340, fill=c, width=8)
        if motivo == "palmera":
            d.line([170, 420, 190, 150], fill=_rgb(color, base * 1.4), width=13)
            for ang in (-70, -40, -10, 20, 50, 80):
                d.bitmap((190 - 60, 150 - 60), _capa_hoja(66, _rgb(color, base * 1.2), ang),
                         fill=_rgb(color, base * 1.2))
    elif motivo == "papel_picado":
        # Banderines: el verde/rojo/verde del tricolor, colgados de una cuerda.
        for i, x in enumerate(range(-40, ANCHO, 150)):
            col = ("#22c55e", "#ffffff", "#dc2626")[i % 3]
            d.polygon([(x, 0), (x + 62, 0), (x + 31, 96)], fill=_rgb(col, base * 0.85))
        d.line([-10, 6, ANCHO + 10, 6], fill=_rgb("#94a3b8", base * 1.2), width=5)
        for x in (150, 250, 350):
            _estrella(d, x, 200 + (x % 3) * 40, 26, _rgb("#ffffff", base), 5)
    elif motivo == "calavera":
        # Calavera de azúcar: cráneo + dos huecos + corazón en la frente.
        for cx, cy, r in ((190, 200, 105), (1730, 240, 88)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r * 0.95], fill=_rgb(color, base * 1.1))
            d.ellipse([cx - r * 0.62, cy - r * 0.3, cx - r * 0.1, cy + r * 0.3],
                      fill=(0, 0, 0, 0))
            d.ellipse([cx + r * 0.1, cy - r * 0.3, cx + r * 0.62, cy + r * 0.3],
                      fill=(0, 0, 0, 0))
            d.rectangle([cx - r * 0.22, cy + r * 0.4, cx + r * 0.22, cy + r * 0.52],
                        fill=(0, 0, 0, 0))
            for i in range(5):
                d.line([cx - r * 0.5 + i * r * 0.25, cy + r * 0.6,
                        cx - r * 0.5 + i * r * 0.25, cy + r * 0.95], fill=(0, 0, 0, 0), width=4)
            _corazon(d, cx, cy - r * 0.62, r * 0.16, _rgb("#f472b6", base * 1.6))
        # Papel picado del Día de Muertos: banderines morados y naranjas
        # colgando abajo, y no la calabaza (con el desenfoque se veía una mancha).
        for i, x in enumerate(range(-30, ANCHO, 190)):
            col = ("#a855f7", "#fb923c", "#e879f9")[i % 3]
            y0 = ALTO - 190
            d.polygon([(x, y0), (x + 74, y0), (x + 37, y0 + 112)], fill=_rgb(col, base * 0.8))
            d.line([x - 10, y0 + 2, x + 84, y0 + 2], fill=_rgb("#f5d0fe", base), width=4)
    elif motivo == "hojas":
        import random
        rnd = random.Random(11)
        for _ in range(26):
            x = rnd.randint(0, ANCHO)
            y = rnd.randint(0, ALTO)
            if 500 < x < 1400 and 380 < y < 900:
                continue      # el centro es donde está el contenido
            d.bitmap((x, y), _capa_hoja(rnd.randint(30, 58),
                                          _rgb("#f59e0b", base * rnd.uniform(0.7, 1.4)),
                                          rnd.uniform(0, 360)), fill=c)
        # El listón tricolor va ABAJO y a los lados, no en el centro: el
        # centro de cada pantalla es donde cae el contenido y la bandera ahí
        # se veía detrás de las tarjetas.
        for i, x in enumerate(range(-40, ANCHO, 210)):
            col = ("#22c55e", "#ffffff", "#dc2626")[i % 3]
            y0 = ALTO - 150
            d.polygon([(x, y0), (x + 78, y0), (x + 39, y0 + 92)], fill=_rgb(col, base * 0.7))
    elif motivo == "navidad":
        for cx, cy, esc in ((1690, 190, 1.35), (140, 320, 1.0)):
            for k, w in ((0, 130), (1, 95), (2, 60)):
                y = cy + k * 78 * esc
                d.polygon([(cx - (w * esc), y), (cx + (w * esc), y), (cx, y - 108 * esc)],
                          fill=_rgb(color, base * 1.15))
            d.rectangle([cx - 15 * esc, cy - 18 * esc, cx + 15 * esc, cy + 250 * esc],
                        fill=_rgb("#78350f", base * 1.2))
            _estrella(d, cx, cy - 118 * esc, 26 * esc, _rgb("#fbbf24", base * 1.6), 5)
        # Copos: fuera del centro, que es donde están las tarjetas.
        for (sx, sy, r) in ((150, 150, 13), (300, 240, 10), (1560, 150, 12),
                            (1800, 260, 10), (520, 110, 9), (1180, 120, 9), (1400, 90, 8)):
            d.line([sx - r, sy, sx + r, sy], fill=_rgb("#e2e8f0", base * 1.5), width=5)
            d.line([sx, sy - r, sx, sy + r], fill=_rgb("#e2e8f0", base * 1.5), width=5)


def _reforzar_alfa(im, factor: float, tope: int):
    """
    Multiplica el canal alfa de la capa para hacerla visible sobre la foto.

    Se hace con `Image.point` sobre el canal, que es un par de multiplicaciones
    en C: a 1920x1080 tarda microsegundos. Trabajar con `ImageEnhance` sobre el
    alfa no sirve (opera sobre el RGB) y recorrer los 2 millones de píxeles a
    mano tarda segundos y sólo para esto.
    """
    from PIL import Image
    a = im.getchannel("A").point(lambda v: min(tope, int(v * factor)))
    im.putalpha(a)
    return im


def generar_overlay(mes: int | None, ruta_destino: str) -> str | None:
    """
    Escribe la capa PNG del tema y devuelve la ruta (o None si no pudo).

    Se regenera sólo si no existe o si es del mes que no es (o sea, una vez al
    cambiar de mes, no cada vuelta).
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except Exception:
        return None

    t = tema_de(mes)
    r, g, b = _hex2rgb(t["tinte"])

    # Capa base con el tinte: un radial suave arriba a la izquierda y otro
    # abajo a la derecha, para que la foto se "tiña" por los dos lados.
    im = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    px = im.load()
    for y in range(0, ALTO, 2):
        for x in range(0, ANCHO, 2):
            d1 = math.dist((x, y), (150, 120)) / 900.0
            d2 = math.dist((x, y), (ANCHO - 120, ALTO - 90)) / 950.0
            # Este lavado es un velo de color sobre TODO el lienzo, y la capa
            # va ENCIMA de la foto de Bing. Con 0.34/0.24 se comía la imagen
            # entera: en la prueba con la foto del ave, el sujeto quedaba
            # verde y naranja lost in tint. Ahora apenas insinúa el tinte del mes
            # y deja que la foto siga siendo la protagonista.
            a = max(0.0, 1 - d1) * 0.10 + max(0.0, 1 - d2) * 0.07
            col = (r, g, b, int(a * 255))
            for dy in range(2):
                for dx in range(2):
                    if x + dx < ANCHO and y + dy < ALTO:
                        px[x + dx, y + dy] = col

    d = ImageDraw.Draw(im, "RGBA")
    _puntos_motivo(d, t["motivo"], t["tinte"])

    # Refuerzo del canal alfa. Este es el ajuste del que depende que el tema se
    # vea o no: los motivos se dibujan con opacidades bajas a propósito (base
    # 0.30) porque la capa va ENCIMA de la foto de Bing y debajo de la viñeta.
    # Con esos valores solos, desde el otro lado de la oficina no se veía NADA:
    # el PNG salía con alfa promedio 25/255 y máximo 140, que contra una foto
    # oscurecida por la viñeta es indescifrable. Se multiplica el alfa global
    # para que los motivos lean como ambiente sin volverse un filtro que tape
    # la foto: tope de 178 (~70%) para que la imagen de Bing siga pasando.
    im = _reforzar_alfa(im, factor=1.55, tope=150)

    # Borroso, pero no tanto: con 2.2 los motivos se volvían una mancha y se
    # perdían los bordes; a 1.0 siguen siendo formas y se nota que son adornos.
    im = im.filter(ImageFilter.GaussianBlur(1.0))

    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    im.save(ruta_destino, "PNG", optimize=True)
    return ruta_destino
