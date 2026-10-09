"""
config.py — rutas y ajustes del kiosco.

Una sola fuente para todo lo que es "dónde está algo" y "cada cuánto". Los
secretos NO se leen de aquí: salen de `secretos_local.py` (que genera el
entrypoint desde las variables de entorno del contenedor) o de las variables
`HUB_DB_*`, en ese orden. Ver AGENTS.md §Credenciales.
"""
import os

# ── Rutas (todo el estado vive en un volumen: sobrevive reinicios) ──────────
DATA_DIR = os.environ.get("KIOSKO_DATA", "/data")
SNAPSHOT = os.path.join(DATA_DIR, "snapshot.json")
EVENTOS = os.path.join(DATA_DIR, "eventos.json")
STATE = os.path.join(DATA_DIR, "state.json")
WEATHER = os.path.join(DATA_DIR, "weather.json")
SALUD = os.path.join(DATA_DIR, "salud.json")
# Control remoto de la TV (ver panel.py). El estado vive en el volumen para que
# sobreviva a reinicios; PANEL_PANTALLAS lo publica la propia TV al arrancar.
PANEL = os.path.join(DATA_DIR, "panel.json")
PANEL_PANTALLAS = os.path.join(DATA_DIR, "panel_pantallas.json")
LOG_SINCRONO = os.path.join(DATA_DIR, "sync.log")
MEDIA_DIR = os.path.join(DATA_DIR, "media")
THUMBS_DIR = os.path.join(MEDIA_DIR, "thumbs")
WALLPAPERS_DIR = os.path.join(MEDIA_DIR, "wallpapers")
AVATARS_DIR = os.path.join(MEDIA_DIR, "avatars")
# Fotos REALES de los usuarios (HUB_Users.Foto), aparte de los avatares IA.
# Se usan en Celebraciones y Asistencia; los avatares IA siguen en Legends.
USUARIOS_DIR = os.path.join(MEDIA_DIR, "usuarios")
# Imagen a pantalla completa de la pantalla de portada.
PANEL_DIR = os.path.join(MEDIA_DIR, "panel")
# Capa PNG del tema del mes (generada por api/temas.py, no descargada).
TEMAS_DIR = os.path.join(MEDIA_DIR, "temas")

# El build de la imagen; lo escribe el Dockerfile y lo lee /api/dashboard/version
# para que la pantalla se recargue sola tras un deploy.
BUILD_FILE = os.environ.get("KIOSKO_BUILD_FILE", "/app/BUILD")
# Palanca de operador: tocar este archivo cambia el identificador de build y
# recarga TODAS las pantallas a la vez, sin ir a la oficina a reiniciar Edge.
FORZAR_RECARGA = os.path.join(DATA_DIR, "forzar-recarga")

# ── Ritmo ────────────────────────────────────────────────────────────────────
# El snapshot se recalcula cada 2 min: los datos que muestra la pantalla son de
# cambio lento (semana, día) y martillar la BD cada 30 s no aporta nada. Lo que
# SÍ corre cada 30 s es la lectura del snapshot en el navegador.
INTERVALO_SNAPSHOT = int(os.environ.get("KIOSKO_INTERVALO", "120"))
SEGUNDOS_ESPERA = 20          # entre vuelta y vuelta, para no perder el hilo

# ── Clima ───────────────────────────────────────────────────────────────────
# Monterrey, Nuevo León. API gratis sin key (Open-Meteo).
CLIMA_LAT = float(os.environ.get("KIOSKO_CLIMA_LAT", "25.6866"))
CLIMA_LON = float(os.environ.get("KIOSKO_CLIMA_LON", "-100.3161"))
CLIMA_CACHE_MIN = 15          # el clima no cambia tan rápido
CLIMA_TIMEOUT = 8

# ── Fondos ──────────────────────────────────────────────────────────────────
WALLPAPERS_MAX = 8            # cuántos se guardan en /data/media/wallpapers
WALLPAPERS_ANCHO = 1920       # la pantalla es Full HD
BING_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# ── Medios ──────────────────────────────────────────────────────────────────
THUMB_FOTOS_ANCHO = 960       # fotos de reportes a pantalla completa
# (los tickets van SIN foto: no hay ancho de thumb que generar)
FOTOS_CARRUSEL = 30           # cuántas hay en el carrusel
TICKETS_PANTALLA = 12
MAX_EVENTOS = 100             # historial de avisos que ve la pantalla
MAX_CURSORES = 2000           # techo de seguridad del state.json

# ── Versión del contrato de datos ───────────────────────────────────────────
# Sube cuando el snapshot cambie de forma incompatible: una pantalla vieja
# recibe este número y sabe que no confiar de lo que no reconoce.
SCHEMA_VERSION = 1


def asegurar_directorios():
    """Crea el árbol de /data. Idempotente."""
    for d in (DATA_DIR, MEDIA_DIR, THUMBS_DIR, WALLPAPERS_DIR, AVATARS_DIR,
              USUARIOS_DIR, PANEL_DIR, TEMAS_DIR):
        os.makedirs(d, exist_ok=True)


def leer_build() -> str:
    """
    Identificador del build, con el que la pantalla decide si se recarga sola.

    Son DOS cosas y por eso van las dos: el texto de BUILD_FILE (lo escribe el
    Dockerfile al construir la imagen) Y la fecha de modificación de
    /app/build/index.html.

    Lo de la segunda parte es por un agujero real: cuando se publica un cambio
    sólo del FRONT copiando la carpeta build/ dentro del contenedor (que es lo
    que hace el hotsync, y lo que se puede hacer a mano), /app/BUILD no cambia
    — sólo cambió cuando se reconstruye la imagen — y entonces la pantalla
    comparaba el build del snapshot con el del endpoint, veía el mismo string y
    NO se recargaba. El resultado: se subían cambios y en la TV seguía lo
    anterior, sin ningún aviso. Cuatro horas de cambios invisibles en la sala.

    Con la mtime del index.html, cualquier cambio en build/ da un build distinto
    y la recarga es automática. Los dos lados usan esta MISMA función
    (snapshotter y /api/dashboard/version), así que nunca se contradicen.
    """
    base = "dev"
    try:
        with open(BUILD_FILE, encoding="utf-8") as fh:
            base = fh.read().strip() or "dev"
    except OSError:
        pass
    try:
        m = int(os.path.getmtime(os.path.join(os.path.dirname(BUILD_FILE), "build", "index.html")))
        base = f"{base}.{m}"
    except OSError:
        pass
    # `touch /data/forzar-recarga` → cambia el build → todas las pantallas
    # recargan. Hace falta porque hay cambios que el navegador no puede detectar
    # solo: cuando el JS que corre ya es el nuevo, nada cambia en el servidor y
    # la pantalla no tiene por qué recargar.
    try:
        base = f"{base}+{int(os.path.getmtime(FORZAR_RECARGA))}"
    except OSError:
        pass
    return base


# ── Base de datos ───────────────────────────────────────────────────────────
def load_db_config():
    """
    Credenciales en este orden (igual que el resto del ecosistema):
      1. variables de entorno `HUB_DB_*` (las inyecta `docker run --env-file`),
      2. `secretos_local.py`, que el entrypoint genera al arrancar,
      3. valores por defecto de la red interna.

    La contraseña NUNCA está en el repo: si no viene de (1) ni de (2), el
    proceso falla al primer uso en vez de adivinar.
    """
    user = os.environ.get("HUB_DB_USER")
    password = os.environ.get("HUB_DB_PASSWORD")
    if (not user or not password):
        try:
            import secretos_local
            user = user or getattr(secretos_local, "DB_USER", None)
            password = password or getattr(secretos_local, "DB_PASSWORD", None)
        except Exception:
            pass
    if not password:
        raise RuntimeError(
            "Falta la contraseña de la BD: pasala en HUB_DB_PASSWORD o en "
            "secretos_local.py (ver AGENTS.md §Credenciales)."
        )
    return {
        "server": os.environ.get("HUB_DB_SERVER", "10.188.141.15"),
        "user": user or "sa",
        "password": password,
        "database": os.environ.get("HUB_DB_DATABASE", "ECCSA_Admon"),
    }
