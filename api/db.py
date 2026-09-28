"""
db.py — conexión a SQL Server (misma base que Field, Admon y HUB: ECCSA_Admon).

Patrón idéntico al de `field/api/db.py`: una conexión por hilo, con prueba de
vida y reconexión perezosa. Acá lo usa solo el `snapshotter` (un proceso), pero
se deja igual para que la API pueda consultarla después sin cambiar de patrón.
"""
import os
import threading

import pymssql

from config import load_db_config

DB_CONFIG = load_db_config()
_local = threading.local()


def get_connection():
    """Conexión viva del hilo, reconectando sola si se cayó."""
    conn = getattr(_local, "conn", None)
    try:
        if conn is not None:
            conn.cursor().execute("SELECT 1")
            return conn
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        _local.conn = None
        conn = None
    if conn is None:
        conn = pymssql.connect(**DB_CONFIG, login_timeout=10, timeout=30)
        _local.conn = conn
    return conn


def ping() -> bool:
    """True si la base responde. Lo usa /healthz."""
    try:
        with get_connection().cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone() is not None
    except Exception:
        return False


def cargar_secretos_desde_archivo():
    """
    Lee `secretos_local.py` si existe (lo genera el entrypoint del contenedor a
    partir de las variables de entorno). Se llama ANTES de `load_db_config` en
    el entrypoint; aquí solo se deja la función para que el orden sea explícito
    en quien la use.
    """
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secretos_local.py")
    if os.path.isfile(ruta):
        with open(ruta, encoding="utf-8") as fh:
            exec(compile(fh.read(), ruta, "exec"), globals())
