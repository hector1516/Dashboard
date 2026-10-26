"""
Zona horaria estándar del ecosistema ECCSA: Monterrey, Nuevo León, México.

México abolió el horario de verano en 2022 para la mayoría del país
(incluyendo Nuevo León). Por lo tanto, Monterrey es UTC-6 todo el año,
sin cambios de DST.

REGLA: nunca usar datetime.now() sin zona, datetime.utcnow() - N, ni
depender de la variable de entorno TZ del contenedor. Siempre usar
now_mx() de este módulo.

Uso:
    from tz_mx import now_mx, TZ_MX, to_mx

    ahora = now_mx()                    # datetime naive en hora Monterrey
    dt_local = to_mx(dt_con_tz)         # convierte cualquier datetime a Monterrey
"""
from datetime import datetime, timezone, timedelta

# Monterrey, NL, México: UTC-6 fijo (sin horario de verano desde 2022)
TZ_MX = timezone(timedelta(hours=-6))


def now_mx() -> datetime:
    """Hora actual de Monterrey como datetime naive (sin tzinfo)."""
    return datetime.now(TZ_MX).replace(tzinfo=None)


def to_mx(dt: datetime) -> datetime:
    """Convierte cualquier datetime (con o sin tz) a hora Monterrey naive."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_MX).replace(tzinfo=None)
