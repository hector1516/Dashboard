"""
datos.py — todo lo que se lee de SQL Server para armar el snapshot.

Una función por bloque de la pantalla y UNA conexión por ciclo. Las consultas
son las mismas que usaba el dashboard de Field (misma base de datos), más tres
cosas nuevas y baratas:

  · `serie_7dias`    → km por día, para la sparkline de la pantalla ⛽
  · `pulso`          → eventos por (día de la semana, hora), para el heatmap 📈
  · `cumpleanos.hoy` → los de HOY, que en Field no se separaban de los del mes

Importante: el kiosco NO escribe nada en la base. Es estrictamente de lectura
(las notas se editan en otro lado; ver AGENTS.md §Alcance).
"""
import datetime as _dt
import json

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tz_mx import TZ_MX as _TZ_MX

import temas
from db import get_connection
# Cálculo puro del bloque `pendientes` (sin BD): su corte de temporada lo usan
# también `combustible()` y `pendientes_snapshot()` para no tener dos ventanas.
from pendientes import armar_pendientes, corte_temporada

DIAS_SEMANA = 7


# Minutos que se le restan a la hora de ENTRADA para acercarse a la real. La MAC
# de una persona aparece en la red hasta varios minutos después de que cruzó la
# puerta, así que la hora de detección siempre llega "tarde". Ver el docstring
# de asistencia_hoy() para por qué el ajuste va aquí y no en el snapshotter.
AJUSTE_ENTRADA_MIN = 4

# Los meses en español, para el título de la pantalla de portada ("ECCSA en
# Octubre"). Van aquí y no en el front porque el backend arma el título cuando
# nadie lo escribe, y el front sólo lo muestra.
_MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
          "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def domingo_de_hoy(hoy: _dt.date = None) -> _dt.date:
    """
    Domingo de la semana en curso. La semana de ECCSA arranca en domingo (lo
    fijó el módulo de Legends); con esta fórmula, si hoy es domingo, devuelve
    hoy mismo.
    """
    hoy = hoy or _dt.date.today()
    return hoy - _dt.timedelta(days=(hoy.weekday() + 1) % 7)


def _s(fecha, hora=False) -> str:
    """Fecha (o fecha+hora) como texto para el JSON de la pantalla."""
    if fecha is None:
        return ""
    if isinstance(fecha, str):
        return fecha.replace("T", " ")
    if hora:
        return fecha.strftime("%Y-%m-%d %H:%M")
    return fecha.strftime("%Y-%m-%d")


# ── REPORTES ────────────────────────────────────────────────────────────────
def reportes(sunday: str, hoy: str) -> dict:
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("SELECT COUNT(*) AS total FROM ReportesServicio WHERE Fecha >= %s", (sunday,))
        total = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM ReportesServicio WHERE Estatus = 'Firmado' AND Fecha >= %s", (sunday,))
        firmados = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM ReportesServicio WHERE CAST(Fecha AS DATE) = %s", (hoy,))
        hoy_r = cur.fetchone()["total"]

        cur.execute("""
            SELECT TOP 8 Folio, Cliente, Tecnico AS ingeniero,
                CAST(Fecha AS VARCHAR(10)) AS fecha, Estatus
            FROM ReportesServicio
            ORDER BY IdReporte DESC
        """)
        ultimos = cur.fetchall()

        cur.execute("""
            SELECT TOP 10 Tecnico AS nombre,
                SUM(CASE WHEN Estatus = 'Firmado' THEN 1 ELSE 0 END) AS firmados,
                SUM(CASE WHEN Estatus = 'Borrador' THEN 1 ELSE 0 END) AS pendientes,
                COUNT(*) AS total
            FROM ReportesServicio
            WHERE Fecha >= %s
            GROUP BY Tecnico
            ORDER BY total DESC
        """, (sunday,))
        por_ingeniero = cur.fetchall()

    return {
        "total": total,
        "firmados": firmados,
        "pendientes": total - firmados,
        "hoy": hoy_r,
        "esta_semana": total,
        "por_ingeniero": por_ingeniero,
        "ultimos": ultimos,
    }


# ── KILÓMETROS ──────────────────────────────────────────────────────────────
def kilometros(sunday: str, hoy: str) -> dict:
    conn = get_connection()
    # OJO: aquí NO se hace SUM(Kilometros). Esa columna es el ODOMETRO y sumarla
    # da un número sin sentido (en producción daba 594.362 km en un solo día;
    # ver AGENTS.md bug #9). El total de la semana y el de hoy se calculan abajo
    # con la misma resta por vehículo que la serie de 7 días.
    with conn.cursor(as_dict=True) as cur:
        # Consumo = última lectura de ESTA semana − última lectura ANTERIOR.
        # Si falta cualquiera de las dos, el vehículo no se muestra: es la
        # misma regla del dashboard de Field y evita restas sin sentido.
        #
        # PERO la pantalla ⛽ no se queda con eso: la semana de ECCSA arranca en
        # domingo, así que cada domingo la pantalla quedaría vacía hasta que
        # alguien registre kilómetros. Por eso además se calcula una ventana
        # MÓVIL de 7 días (`consumo_7d`), que es la que se dibuja: responde
        # "¿cuánto se movió la flota?", que no depende del día de la semana.
        cur.execute("""
            SELECT a.Id, a.MarcaModelo, a.Placas,
                this_week.km AS km_esta_semana,
                prev_week.km AS km_semana_pasada,
                CASE WHEN this_week.km IS NOT NULL THEN 1 ELSE 0 END AS registrado_semana,
                ult7.km AS km_7d,
                prev7.km AS previo_7d,
                ultimo.km_fecha AS ultimo_registro
            FROM HUB_Automoviles a
            OUTER APPLY (
                SELECT TOP 1 k.Kilometros AS km
                FROM HUB_RegistroKilometros k
                WHERE k.IdAutomovil = a.Id AND CAST(k.FechaHora AS DATE) >= %s
                ORDER BY k.FechaHora DESC
            ) this_week
            OUTER APPLY (
                SELECT TOP 1 k.Kilometros AS km
                FROM HUB_RegistroKilometros k
                WHERE k.IdAutomovil = a.Id AND CAST(k.FechaHora AS DATE) < %s
                ORDER BY k.FechaHora DESC
            ) prev_week
            OUTER APPLY (
                SELECT TOP 1 k.Kilometros AS km
                FROM HUB_RegistroKilometros k
                WHERE k.IdAutomovil = a.Id AND k.FechaHora >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                ORDER BY k.FechaHora DESC
            ) ult7
            OUTER APPLY (
                SELECT TOP 1 k.Kilometros AS km
                FROM HUB_RegistroKilometros k
                WHERE k.IdAutomovil = a.Id AND k.FechaHora < DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
                ORDER BY k.FechaHora DESC
            ) prev7
            OUTER APPLY (
                SELECT TOP 1 CONVERT(VARCHAR(16), k.FechaHora, 120) AS km_fecha
                FROM HUB_RegistroKilometros k
                WHERE k.IdAutomovil = a.Id
                ORDER BY k.FechaHora DESC
            ) ultimo
            WHERE ult7.km IS NOT NULL
            ORDER BY a.MarcaModelo
        """, (sunday, sunday))
        vehiculos = cur.fetchall()
        for v in vehiculos:
            v["consumo_semana"] = int((v.get("km_esta_semana") or 0) - (v.get("km_semana_pasada") or 0))
            # Ventana de 7 días. Si no hay lectura anterior, NO se inventa: se
            # marca sin referencia y la pantalla lo muestra con cero.
            if v.get("km_7d") is not None and v.get("previo_7d") is not None:
                v["consumo_7d"] = int(v["km_7d"] - v["previo_7d"])
                v["sin_referencia"] = 0
            else:
                v["consumo_7d"] = 0
                v["sin_referencia"] = 1
            v.pop("km_7d", None)
            v.pop("previo_7d", None)

        # Total de la semana = suma del consumo REAL por vehículo. Sólo entran
        # los que tienen las dos lecturas (semana actual y anterior): restar
        # contra cero sería volver a contar el odómetro.
        total_semana = sum(
            int(v["consumo_semana"]) for v in vehiculos
            if v.get("km_esta_semana") is not None and v.get("km_semana_pasada") is not None
        )

        # Serie de 7 días para la sparkline.
        #
        # OJO: `Kilometros` es el ODOMETRO, no el consumo. Sumar las lecturas de
        # un día da un número sin sentido (en producción daba 594.362 km en un
        # solo día). Lo correcto es, por vehículo y día: última lectura del día
        # menos la lectura anterior. Eso es lo que se dibuja, y el cálculo de
        # la resta se hace acá en Python, que es más legible que el OUTER APPLY.
        cur.execute("""
            SELECT CAST(FechaHora AS DATE) AS dia, IdAutomovil,
                MAX(Kilometros) AS km_dia, COUNT(*) AS registros
            FROM HUB_RegistroKilometros
            WHERE FechaHora >= DATEADD(DAY, -6, CAST(GETDATE() AS DATE))
            GROUP BY CAST(FechaHora AS DATE), IdAutomovil
            ORDER BY dia ASC
        """)
        filas = cur.fetchall()

        # Lectura anterior de cada vehículo (para restar).
        previos = {}
        for f in filas:
            veh = f["IdAutomovil"]
            if veh in previos:
                continue
            cur.execute("""
                SELECT TOP 1 Kilometros AS km
                FROM HUB_RegistroKilometros
                WHERE IdAutomovil = %s AND CAST(FechaHora AS DATE) < %s
                ORDER BY FechaHora DESC
            """, (veh, f["dia"]))
            prev = cur.fetchone()
            previos[veh] = prev["km"] if prev else None

        por_dia = {}
        for f in filas:
            d = str(f["dia"])
            acc = por_dia.setdefault(d, {"km": 0, "registros": 0})
            acc["registros"] += f["registros"] or 0
            previo = previos.get(f["IdAutomovil"])
            if previo is not None and f["km_dia"] is not None:
                acc["km"] += max(0, int(f["km_dia"]) - int(previo))

        # Rellenar los días sin registro para que la línea no "salte" días.
        serie = []
        base = _dt.date.today() - _dt.timedelta(days=6)
        for i in range(7):
            d = base + _dt.timedelta(days=i)
            clave = str(d)
            acc = por_dia.get(clave) or {"km": 0, "registros": 0}
            serie.append({"fecha": clave, "km": acc["km"], "registros": acc["registros"]})

        # "Km hoy" = el último punto de la serie (hoy), ya con la resta correcta.
        km_hoy = serie[-1]["km"] if serie else 0

    return {
        "total_semana": total_semana,
        "hoy": km_hoy,
        "por_vehiculo": vehiculos,
        "serie_7dias": serie,
    }


# ── TICKETS OXXOGAS ─────────────────────────────────────────────────────────
def tickets(sunday: str) -> dict:
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("SELECT COUNT(*) AS total FROM HUB_OxxoGasTickets")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT TOP 10 t.Id AS id_ticket, t.FolioTicket AS folio,
                a.MarcaModelo AS vehiculo, a.Placas,
                u.Nombre AS usuario,
                CONVERT(VARCHAR(16), t.FechaRegistro, 120) AS fecha,
                ISNULL(c.Cliente, t.IdCliente) AS cliente,
                ISNULL(t.Descripcion, '') AS descripcion,
                t.IdSolicitudVale AS id_solicitud_vale,
                CONVERT(VARCHAR(16), sv.FechaSolicitud, 120) AS fecha_vale,
                sv.Estatus AS estatus_vale,
                sv.MontoUnit AS monto_vale
            FROM HUB_OxxoGasTickets t
            LEFT JOIN HUB_Automoviles a ON t.IdVehiculo = a.Id
            JOIN HUB_Users u ON t.IdUsuario = u.Id
            LEFT JOIN clientes c ON t.IdCliente = c.IdCliente
            LEFT JOIN HUB_SolicitudVales sv ON t.IdSolicitudVale = sv.Id
            ORDER BY t.Id DESC
        """)
        ultimos = cur.fetchall()

        cur.execute("""
            SELECT TOP 8 a.MarcaModelo AS vehiculo, COUNT(*) AS total_tickets
            FROM HUB_OxxoGasTickets t
            JOIN HUB_Automoviles a ON t.IdVehiculo = a.Id
            GROUP BY a.MarcaModelo
            ORDER BY total_tickets DESC
        """)
        por_vehiculo = cur.fetchall()

    return {"total_semana": total, "ultimos": ultimos, "por_vehiculo": por_vehiculo}


def cotizaciones_lista_facturar() -> dict:
    """Cotizaciones en estado 'Lista Para Facturar' (Color=1) con dias transcurridos."""
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT i.Folio, i.IdCliente, c.Cliente, i.Contacto, i.Descripcion,
                   i.Autor, i.Fecha,
                   h.FechaCambio AS FechaLista,
                   DATEDIFF(day, ISNULL(h.FechaCambio, i.Fecha), GETDATE()) AS DiasTranscurridos
            FROM IndiceMateriales i
            LEFT JOIN clientes c ON i.IdCliente = c.IdCliente
            OUTER APPLY (
                SELECT TOP 1 FechaCambio
                FROM HUB_CotizacionEstatusHistorial
                WHERE Folio = i.Folio AND EstatusNuevo = 1
                ORDER BY FechaCambio DESC
            ) h
            WHERE i.Color = 1
            ORDER BY ISNULL(h.FechaCambio, i.Fecha) ASC
        """)
        rows = cur.fetchall()

        total = len(rows)
        verdes = sum(1 for r in rows if (r.get("DiasTranscurridos") or 0) < 7)
        amarillos = sum(1 for r in rows if 7 <= (r.get("DiasTranscurridos") or 0) <= 14)
        rojos = sum(1 for r in rows if (r.get("DiasTranscurridos") or 0) > 14)

        por_autor = {}
        for r in rows:
            autor = r.get("Autor") or "Sin autor"
            por_autor[autor] = por_autor.get(autor, 0) + 1

        # Top 5 más antiguas
        mas_antiguas = rows[:5]

    return {
        "total": total,
        "verdes": verdes,
        "amarillos": amarillos,
        "rojos": rojos,
        "por_autor": por_autor,
        "mas_antiguas": mas_antiguas,
        "mas_antigua_dias": mas_antiguas[0].get("DiasTranscurridos", 0) if mas_antiguas else 0,
    }


# ── IMAGEN DE PORTADA ───────────────────────────────────────────────────────
def imagen_pantalla(clave: str = "PORTADA") -> dict:
    """
    La imagen a pantalla completa de una pantalla del kiosco (la de portada, con
    "ECCSA en <mes>" encima).

    Los bytes NO se mandan en el snapshot: se escriben una vez a
    /data/media/panel/ y el snapshot lleva sólo la ruta (ver
    `medios.guardar_imagen_panel`). Meter 300 KB de JPEG en cada respuesta que
    la pantalla pide cada 30 s sería regalarle 10 MB/s a la red interna.

    Viene de `HUB_PantallaImagenes`, que escribe el módulo Notas de Admon.
    """
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT TOP 1 Id, Clave, Titulo, ContentType, Ancho, Alto, FechaSubida
            FROM HUB_PantallaImagenes
            WHERE Clave = %s AND Activo = 1
            ORDER BY Id DESC
        """, (clave,))
        fila = cur.fetchone()
    if not fila:
        return {"hay": False}

    # Si no hay título guardado, el de cortesía lo arma el mes en curso: la
    # pantalla tiene que decir algo aunque nadie haya escrito nada.
    mes_actual = _MESES[_dt.date.today().month - 1]
    titulo = (fila.get("Titulo") or "").strip() or f"ECCSA en {mes_actual}"
    return {
        "hay": True,
        "id": fila["Id"],
        "clave": fila["Clave"],
        "titulo": titulo,
        "content_type": fila.get("ContentType") or "image/jpeg",
        "ancho": fila.get("Ancho"),
        "alto": fila.get("Alto"),
        "subida": _s(fila.get("FechaSubida"), hora=True),
        # Lo rellena medios.guardar_imagen_panel() en el mismo ciclo.
        "ruta": "",
    }


def bytes_imagen_pantalla(clave: str = "PORTADA") -> tuple[bytes, str] | None:
    """Los bytes crudos de la imagen activa. Separate porque el snapshot no
    puede cargarse 300 KB en memoria en cada vuelta sólo para no usarlos."""
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT TOP 1 Archivo, ContentType
            FROM HUB_PantallaImagenes
            WHERE Clave = %s AND Activo = 1
            ORDER BY Id DESC
        """, (clave,))
        fila = cur.fetchone()
    if not fila:
        return None
    return fila["Archivo"], (fila.get("ContentType") or "image/jpeg")


# ── TEMA DEL MES ─────────────────────────────────────────────────────────────
def temas_lista() -> list:
    """
    Los doce temas, para que el front pueda previsualizar cualquiera con
    `?tema=N` sin que el worker haya generado ese mes todavía. Son 12 objetos
    chicos: no vale la pena complicarlo con una llamada aparte.
    """
    return [
        {
            "mes": m,
            "nombre": temas.TEMAS[m]["nombre"],
            "icono": temas.TEMAS[m]["icono"],
            "tinte": temas.TEMAS[m]["tinte"],
            "capa": f"/media/temas/mes{m}.png",
        }
        for m in range(1, 13)
    ]


def tema_mes(mes: int = None) -> dict:
    """
    El tema del mes para el fondo (colores y nombre). La CAPA png la genera
    `temas.generar_overlay` desde el snapshotter, porque eso escribe un archivo
    y la API es sólo lectura (AGENTS.md §La API sólo lee).
    """
    t = temas.tema_de(mes)
    return {
        "mes": t["mes"],
        "nombre": t["nombre"],
        "icono": t["icono"],
        "tinte": t["tinte"],
        "motivo": t["motivo"],
        "capa": f"/media/temas/mes{t['mes']}.png",
        "todos": temas_lista(),
    }


# ── ASISTENCIA DEL DÍA ─────────────────────────────────────────────────────
def ubicaciones_hoy() -> dict:
    """
    Dónde está cada quien HOY, desde `HUB_Ubicaciones`.

    La tabla la escribe la app Field cuando alguien presiona el botón flotante
    «Aquí estoy» (migración 0047). Cada registro es una ubicación en el
    momento en que se presionar; un Ingeniero que se mueve la vuelve a
    presionar y queda otro renglón.

    De todos los renglones del día se toma el MÁS RECIENTE de cada usuario: la
    pantalla dice dónde está HOY, no dónde pasó a las 9 de la mañana. Por eso
    `ROW_NUMBER() OVER (PARTITION BY IdUsuario ORDER BY FechaRegistro DESC)` y
    no un `MAX` con `GROUP BY`: el desempate por hora queda definido en la misma
    consulta, así que dos registros del mismo segundo no pueden duplicar a la
    persona en el mapa.

    SOLO HOY, y a propósito: `FechaRegistro >= CAST(GETDATE() AS date)` en el
    servidor. Al día siguiente la pantalla arranca en blanco sola, sin que nadie
    tenga que borrar nada ni que la vista sepa qué día es.

    La hora NO se devuelve ni se muestra: el mapa es "quién está dónde", no un
    historial. Si algún día hace falta saber desde cuándo lleva ahí el dato,
    ya está en la tabla.
    """
    try:
        with get_connection() as conn:
            with conn.cursor(as_dict=True) as cur:
                cur.execute("""
                    SELECT TOP 200
                           u.Id AS id_usuario,
                           u.Nombre AS nombre,
                           t.Latitud AS lat,
                           t.Longitud AS lon,
                           t.PrecisionM AS precision
                    FROM (
                        SELECT ub.IdUsuario, ub.Latitud, ub.Longitud, ub.PrecisionM,
                               ROW_NUMBER() OVER (
                                   PARTITION BY ub.IdUsuario
                                   ORDER BY ub.FechaRegistro DESC, ub.Id DESC
                               ) AS rn
                        FROM HUB_Ubicaciones ub
                        WHERE ub.FechaRegistro >= CAST(GETDATE() AS date)
                    ) t
                    JOIN HUB_Users u ON u.Id = t.IdUsuario
                    WHERE t.rn = 1 AND u.Activo = 1
                    ORDER BY u.Nombre
                """)
                # `id_usuario` no se ve en pantalla: se usa para el avatar del
                # pin y para agrupar a quien reporta desde el mismo punto. Sin
                # él el mapa tendría que adivinar de quién es cada cara.
                personas = [
                    {"id_usuario": r["id_usuario"], "nombre": r["nombre"],
                     "lat": float(r["lat"]), "lon": float(r["lon"]),
                     "precision": float(r["precision"]) if r["precision"] is not None else None}
                    for r in cur.fetchall()
                ]
        return {"personas": personas}
    except Exception:
        return {"personas": []}


def asistencia_hoy() -> dict:
    """
    Quién entró y salió HOY, desde `HUB_NetworkPresence`.

    OJO con la fuente: existen otras dos tablas de asistencia en la base y
    NINGUNA sirve para esto hoy —
      · `ControlAsistencia` (la vieja, del checador): su último registro es de
        enero de 2023, está abandonada.
      · `HUB_AsistenciaDiaria`: la última vez que se calculó fue el 2026-09-11
        y la mayoría de sus filas traen las horas en NULL; sólo la rellenó a
        mano una vez.
    La que se escribe sola todos los días es `HUB_NetworkPresence`, y la
    escribe el `network_scanner_worker` del contenedor `workersadmon` cuando ve
    aparecer o desaparecer una MAC conocida en la red.

    Por persona se toma la PRIMERA entrada del día y la ÚLTIMA salida: un
    celular que entra y sale 6 veces no debe verse como 6 llegadas distintas.
    Quien sigue dentro (último evento = ENTRADA) va con `en_sitio` para no
    mostrar una salida que no ha pasado.

    EL AJUSTE DE LA ENTRADA va AQUÍ, en la capa de datos, y no en el snapshotter
    ni en la vista, por dos razones:
      · es un dato (la hora de llegada es menor que la de detección), no una
        decisión de cómo se ve; si mañana se corrige, se corrige un solo lugar
        y no tres.
      · `DATEADD` dentro del SQL deja el cálculo en la misma agregación que
        decide cuál es la primera entrada: si se ajustara en Python, el "primer
        evento del día" podría dejar de ser el mínimo al ajustar.

    Por qué restar minutos: la MAC aparece en la red cuando el ARP la ve, y eso
    pasa hasta varios minutos después de que la persona cruzó la puerta (el
    escáner corre cada 3 min y el detector tiene 5 min de tolerancia). La hora
    de LLEGADA que se muestra es la de ENTRADA de la tabla, con el ajuste
    aplicado, para que se parezca a la real.

    OJO: el ajuste es SÓLO de la ENTRADA. La salida no se toca: cuando un
    dispositivo desaparece de la red se nota de inmediato, y restarle minutos
    haría que alguien saliera "antes" de irse.
    """
    conn = get_connection()
    # EV: el instante del ESCANEO que prueba el evento, con respaldo en la hora
    # de proceso para los registros anteriores a esa columna.
    #
    # El scanner guarda DOS fechas y su docstring dice que la asistencia debe
    # usar `FechaDeteccion` (la otra es "cuándo lo procesó el worker"). Cuando el
    # worker se atascó 6 h y drenó 1 195 escaneos de golpe, leer `FechaHora`
    # mostraba la hora del drenaje: Rosa llegaba 09:22 cuando llegó 08:35, y el
    # ajuste de minutos caía sobre el número equivocado.
    EV = "COALESCE(p.FechaDeteccion, p.FechaHora)"
    with conn.cursor(as_dict=True) as cur:
        cur.execute(f"""
            SELECT
                d.IdUsuario AS id_usuario,
                ISNULL(u.Nombre, '(sin usuario)') AS nombre,
                -- Primer evento del día YA AJUSTADO (más el tope del día, para
                -- que a las 00:02 no salga "23:58 de ayer"). Se ordena por la
                -- hora ajustada, que es la que ve la gente.
                CASE WHEN MIN(CASE WHEN p.TipoEvento = 'ENTRADA' THEN {EV} END)
                         IS NULL THEN NULL
                     ELSE CASE WHEN DATEADD(MINUTE, -%d, MIN(CASE WHEN p.TipoEvento = 'ENTRADA' THEN {EV} END))
                                    < CAST(CAST(GETDATE() AS date) AS datetime)
                               THEN CAST(CAST(GETDATE() AS date) AS datetime)
                               ELSE DATEADD(MINUTE, -%d, MIN(CASE WHEN p.TipoEvento = 'ENTRADA' THEN {EV} END))
                          END
                END AS entrada,
                MIN(CASE WHEN p.TipoEvento = 'ENTRADA' THEN {EV} END) AS entrada_cruda,
                MAX(CASE WHEN p.TipoEvento = 'ENTRADA' THEN {EV} END) AS ultima_entrada,
                MAX(CASE WHEN p.TipoEvento = 'SALIDA'  THEN {EV} END) AS salida,
                COUNT(*) AS eventos
            FROM HUB_NetworkPresence p
            JOIN HUB_NetworkDevices d ON d.Id = p.IdDispositivo
            LEFT JOIN HUB_Users u ON u.Id = d.IdUsuario
            WHERE {EV} >= CAST(CAST(GETDATE() AS date) AS datetime)
              AND {EV} < DATEADD(day, 1, CAST(CAST(GETDATE() AS date) AS datetime))
              AND d.IdUsuario IS NOT NULL
            GROUP BY d.IdUsuario, u.Nombre
            ORDER BY entrada
        """, (AJUSTE_ENTRADA_MIN, AJUSTE_ENTRADA_MIN))
        personas = cur.fetchall()

        # Último evento de cada quien: define si sigue dentro de la oficina.
        for p in personas:
            cur.execute("""
                SELECT TOP 1 p.TipoEvento AS tipo
                FROM HUB_NetworkPresence p
                JOIN HUB_NetworkDevices d ON d.Id = p.IdDispositivo
                WHERE d.IdUsuario = %s
                  AND COALESCE(p.FechaDeteccion, p.FechaHora)
                      >= CAST(CAST(GETDATE() AS date) AS datetime)
                ORDER BY p.Id DESC
            """, (p["id_usuario"],))
            ultimo = cur.fetchone()
            p["en_sitio"] = bool(ultimo and ultimo["tipo"] == "ENTRADA")

            # OJO: las comparaciones van ANTES de pasar los datetime a texto.
            # Al revés (convertir y luego comparar) revienta con
            # "'>' not supported between datetime.datetime and str" y, como
            # esto vive dentro del bloque de la BD, el snapshot entero se
            # queda en la versión anterior: la pantalla deja de refrescar
            # asistencia sin decir nada, salvo el ERROR del log.
            # `entrada` viene ya ajustada; `entrada_cruda` es la hora real de
            # detección. La comparación de "salió y volvió" va con la CRUDA:
            # comparar un arrival ya corrido contra una salida real daría
            # falsos positivos ("salió 08:10" cuando en realidad ni había
            # salido).
            entrada = p.get("entrada_cruda")
            ultima_entrada = p.get("ultima_entrada")
            ultima_salida = p.get("salida")

            # Si sigue dentro, la hora de SALIDA es la de una visita anterior y
            # no la de hoy: mostrarla junto a "en la oficina" se contradice
            # ("se fue 17:36" y está aquí a las 18:10, porque salió y volvió).
            # La salida de HOY todavía no pasa, y lo que interesa es cuándo
            # entró en la visita en la que sigue.
            reingreso = ""
            if p["en_sitio"]:
                if ultima_entrada and ultima_salida and ultima_entrada > entrada:
                    reingreso = _s(ultima_entrada, hora=True)
                p["salida"] = ""
            else:
                p["salida"] = _s(ultima_salida, hora=True)

            # Caso límite: si al restar los 4 minutos la entrada queda
            # DESPUÉS de la salida, la tarjeta mostraría "llegó 08:05 / se fue
            # 08:02", que es imposible y hace dudar de toda la pantalla. En ese
            # caso se queda la hora cruda (sin ajustar): antes de restar, la
            # detección siempre先后 de la salida.
            entrada_mostrar = p.get("entrada")
            if (not p["en_sitio"] and ultima_salida and entrada_mostrar
                    and entrada_mostrar > ultima_salida):
                entrada_mostrar = entrada
            p["entrada"] = _s(entrada_mostrar, hora=True)
            p["reingreso"] = reingreso
            p.pop("entrada_cruda", None)
            p.pop("ultima_entrada", None)
            p["eventos"] = int(p["eventos"] or 0)

    dentro = sum(1 for p in personas if p["en_sitio"])
    return {
        "personas": personas,
        "total": len(personas),
        "dentro": dentro,
        "salieron": len(personas) - dentro,
    }


# ── LEGENDS ─────────────────────────────────────────────────────────────────
# Niveles de temporada. Deben ser los mismos de `field/api/legends_core.py`:
# el kiosco calcula el nivel con los puntos de temporada para no depender de que
# el auditor haya corrido en el último ciclo.
_NIVELES = [
    ("Bronce", 0, "🥉", "#CD7F32"),
    ("Plata", 250, "🥈", "#C0C0C0"),
    ("Oro", 750, "🥇", "#FFD700"),
    ("Diamante", 1500, "💎", "#22D3EE"),
    ("Leyenda", 3000, "🌟", "#A855F7"),
]


def _ahora_mx() -> _dt.datetime:
    """Ahora en hora de México, sin tzinfo (así se compara con SQL Server)."""
    return _dt.datetime.now(_TZ_MX).replace(tzinfo=None)


def _nivel_info(puntos: int) -> dict:
    pts = int(puntos or 0)
    actual = _NIVELES[0]
    for nivel in _NIVELES:
        if pts >= nivel[1]:
            actual = nivel
        else:
            break
    return {
        "nombre": actual[0], "min": actual[1],
        "icono": actual[2], "color": actual[3],
    }


def _tabla_existe(cur, tabla: str) -> bool:
    cur.execute(
        "SELECT TOP 1 1 AS existe FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = %s",
        (tabla,),
    )
    return cur.fetchone() is not None


def legends() -> dict:
    """Ranking semanal + temporada + logros/racha para la pantalla grande.

    Solo usuarios con nickname y passkey (la misma regla de Field/Admon: el
    Legends se juega entre quienes usan la app). Los puntos se leen de
    `HUB_ScoreLog`, no de la caché `HUB_UserScores`: si el auditor se retrasa,
    la TV sigue mostrando la tabla real. El nivel se calcula con los puntos de
    la temporada (trimestre calendario), no con el total histórico.
    `puesto_anterior` se calcula en el snapshotter contra el ranking previo.
    """
    ahora = _ahora_mx()
    inicio_sem = ahora - _dt.timedelta(days=(ahora.weekday() + 1) % 7)
    inicio_sem = inicio_sem.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_sem = inicio_sem + _dt.timedelta(days=7)

    q = (ahora.month - 1) // 3 + 1
    inicio_temp = _dt.datetime(ahora.year, 3 * (q - 1) + 1, 1)
    if q == 4:
        fin_temp = _dt.date(ahora.year, 12, 31)
    else:
        fin_temp = _dt.date(ahora.year, 3 * q + 1, 1) - _dt.timedelta(days=1)

    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        # Una sola pasada: semana, temporada y total por usuario. Igual que el
        # core, se excluye `sync_completado` (no es una acción que valga puntos).
        cur.execute(
            """
            WITH pts AS (
                SELECT IdUsuario,
                    SUM(CASE WHEN FechaRegistro >= %s THEN Puntos ELSE 0 END) AS semana,
                    SUM(CASE WHEN FechaRegistro >= %s THEN Puntos ELSE 0 END) AS temporada,
                    SUM(Puntos) AS total
                FROM HUB_ScoreLog
                WHERE Metrica <> 'sync_completado'
                GROUP BY IdUsuario
            )
            SELECT u.Id AS id_usuario,
                   u.Nombre AS nombre,
                   LTRIM(RTRIM(u.Nickname)) AS nickname,
                   ISNULL(p.semana, 0) AS puntos_semana,
                   ISNULL(p.temporada, 0) AS puntos_temporada,
                   ISNULL(p.total, 0) AS puntos_total,
                   ISNULL(s.RachaDias, 0) AS racha_dias
            FROM HUB_Users u
            LEFT JOIN pts p ON p.IdUsuario = u.Id
            LEFT JOIN HUB_UserScores s ON s.IdUsuario = u.Id
            WHERE u.Activo = 1
              AND u.Nickname IS NOT NULL AND LTRIM(RTRIM(u.Nickname)) <> ''
              AND EXISTS (SELECT 1 FROM HUB_Passkeys pk WHERE pk.IdUsuario = u.Id)
            """,
            (inicio_sem, inicio_temp),
        )
        filas = cur.fetchall()

        logros = {}
        try:
            if _tabla_existe(cur, "HUB_UserLogros"):
                cur.execute(
                    "SELECT IdUsuario, COUNT(*) AS n FROM HUB_UserLogros GROUP BY IdUsuario"
                )
                logros = {int(r["IdUsuario"]): int(r["n"] or 0) for r in cur.fetchall()}
        except Exception:
            # La migración puede no estar aplicada todavía; la pantalla debe
            # seguir funcionando sin la columna de logros.
            logros = {}

        # Desglose de puntos por métrica de la semana actual (para mostrar por qué va ganando)
        cur.execute(
            """
            SELECT IdUsuario, Metrica, SUM(Puntos) AS total
            FROM HUB_ScoreLog
            WHERE FechaRegistro >= %s
            GROUP BY IdUsuario, Metrica
            """,
            (inicio_sem,),
        )
        desglose_raw = cur.fetchall()
        desglose_por_usuario = {}
        for r in desglose_raw:
            uid = int(r["IdUsuario"])
            if uid not in desglose_por_usuario:
                desglose_por_usuario[uid] = {}
            desglose_por_usuario[uid][r["Metrica"]] = int(r["total"] or 0)

        cur.execute(
            """
            SELECT TOP 1
                w.IdUsuario AS id_usuario,
                u.Nombre AS nombre,
                ISNULL(NULLIF(LTRIM(RTRIM(u.Nickname)), ''), u.Nombre) AS nickname,
                w.PuntuacionSemana AS puntos,
                CONVERT(VARCHAR(10), w.FechaInicio, 120) AS desde,
                CONVERT(VARCHAR(10), w.FechaFin, 120) AS hasta,
                ISNULL(s.Nivel, 'Bronce') AS nivel
            FROM HUB_WeeklyWinners w
            JOIN HUB_Users u ON w.IdUsuario = u.Id
            LEFT JOIN HUB_UserScores s ON s.IdUsuario = u.Id
            ORDER BY w.FechaInicio DESC
            """
        )
        ganador = cur.fetchone()

    ranking = []
    for r in filas:
        nivel = _nivel_info(r["puntos_temporada"])
        ranking.append({
            "id_usuario": int(r["id_usuario"]),
            "nombre": r["nombre"],
            "nickname": r["nickname"] or r["nombre"],
            "puntos_semana": int(r["puntos_semana"] or 0),
            "puntos_temporada": int(r["puntos_temporada"] or 0),
            "puntos_total": int(r["puntos_total"] or 0),
            "racha_dias": int(r["racha_dias"] or 0),
            "nivel": nivel["nombre"],
            "icono_nivel": nivel["icono"],
            "color_nivel": nivel["color"],
            "logros_desbloqueados": logros.get(int(r["id_usuario"]), 0),
            "elegible": True,
            "desglose": desglose_por_usuario.get(int(r["id_usuario"]), {}),
        })

    # Desempate igual que `legends_core.ranking`: puntos de semana, temporada,
    # total y, al final, el Id más bajo.
    ranking.sort(
        key=lambda r: (
            r["puntos_semana"], r["puntos_temporada"], r["puntos_total"],
            -r["id_usuario"],
        ),
        reverse=True,
    )
    for i, r in enumerate(ranking, start=1):
        r["posicion"] = i

    # El avatar NO viaja en el JSON: el snapshotter lo convierte en un archivo
    # local y lo pega a cada fila. Aquí se conserva `id_usuario` para eso.
    reset_en = max(int((fin_sem - ahora).total_seconds()), 0)
    return {
        "ranking": ranking,
        "ganador_semana": ganador,
        "total_puntos": sum(r["puntos_semana"] for r in ranking),
        "participantes": len(ranking),
        "reset_en_segundos": reset_en,
        "semana": {
            "inicio": inicio_sem.date().isoformat(),
            "fin": (fin_sem - _dt.timedelta(days=1)).date().isoformat(),
            "reset_en_segundos": reset_en,
        },
        "temporada": {
            "clave": f"{ahora.year}-Q{q}",
            "nombre": f"Temporada Q{q} {ahora.year}",
            "corto": f"Q{q} {ahora.year}",
            "inicio": inicio_temp.date().isoformat(),
            "fin": fin_temp.isoformat(),
            "dias_restantes": max((fin_temp - ahora.date()).days + 1, 0),
        },
    }


# ── FOTOS (carrusel) ────────────────────────────────────────────────────────
def fotos(limite: int) -> dict:
    """Ids sueltos: los bytes se sirven como thumbs desde /media (ver medios.py)."""
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT TOP %d f.IdReporte, r.Folio, r.Cliente, r.Tecnico AS ingeniero, f.Orden
            FROM ReportesServicioFotos f
            JOIN ReportesServicio r ON f.IdReporte = r.IdReporte
            ORDER BY NEWID()
        """, (limite,))
        return {"ids": cur.fetchall()}


# ── NOTAS (solo lectura) ────────────────────────────────────────────────────
def notas() -> list:
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT Id, Titulo, Contenido, Color, Autor, Fija,
                CONVERT(VARCHAR(16), FechaCreacion, 120) AS fecha_creacion,
                CONVERT(VARCHAR(16), FechaModificado, 120) AS fecha_modificado
            FROM HUB_DashboardNotas
            ORDER BY Fija DESC, FechaModificado DESC
        """)
        return cur.fetchall()


# ── CUMPLEAÑOS Y ANIVERSARIOS ───────────────────────────────────────────────
def _personas(cur, mes: int) -> list:
    """
    Cumpleaños del mes. Si hay `FechaNacimiento` se usa; si no, se deduce del
    CURP (posiciones 7-8 = mes, 9-10 = día, 5-6 = año). Es la misma lógica que
    tenía el dashboard de Field.
    """
    cur.execute("""
        SELECT u.Id AS id_usuario, u.Nombre,
            CASE
                WHEN u.FechaNacimiento IS NOT NULL THEN DAY(u.FechaNacimiento)
                WHEN u.CurpRfc IS NOT NULL AND LEN(u.CurpRfc) >= 10
                    THEN CAST(SUBSTRING(u.CurpRfc, 9, 2) AS INT)
                ELSE NULL
            END AS dia,
            CASE
                WHEN u.FechaNacimiento IS NOT NULL THEN MONTH(u.FechaNacimiento)
                WHEN u.CurpRfc IS NOT NULL AND LEN(u.CurpRfc) >= 10
                    THEN CAST(SUBSTRING(u.CurpRfc, 7, 2) AS INT)
                ELSE NULL
            END AS mes,
            CASE
                WHEN u.FechaNacimiento IS NOT NULL
                    THEN YEAR(GETDATE()) - YEAR(u.FechaNacimiento)
                WHEN u.CurpRfc IS NOT NULL AND LEN(u.CurpRfc) >= 10 THEN
                    CASE WHEN CAST(SUBSTRING(u.CurpRfc, 5, 2) AS INT) > 30
                         THEN YEAR(GETDATE()) - (1900 + CAST(SUBSTRING(u.CurpRfc, 5, 2) AS INT))
                         ELSE YEAR(GETDATE()) - (2000 + CAST(SUBSTRING(u.CurpRfc, 5, 2) AS INT))
                    END
                ELSE NULL
            END AS edad
        FROM HUB_Users u
        WHERE u.Activo = 1
          AND (
            (u.FechaNacimiento IS NOT NULL AND MONTH(u.FechaNacimiento) = %s)
            OR (u.CurpRfc IS NOT NULL AND LEN(u.CurpRfc) >= 10
                AND CAST(SUBSTRING(u.CurpRfc, 7, 2) AS INT) = %s)
          )
        ORDER BY dia
    """, (mes, mes))
    return cur.fetchall()


def _aniversarios(cur, mes: int) -> list:
    cur.execute("""
        SELECT u.Id AS id_usuario, u.Nombre,
            DAY(u.FechaIngreso) AS dia,
            MONTH(u.FechaIngreso) AS mes,
            YEAR(GETDATE()) - YEAR(u.FechaIngreso) AS anos
        FROM HUB_Users u
        WHERE u.Activo = 1
          AND u.FechaIngreso IS NOT NULL
          AND MONTH(u.FechaIngreso) = %s
        ORDER BY dia
    """, (mes,))
    return cur.fetchall()


def celebraciones() -> dict:
    """
    Devuelve el mes Y el día de hoy, separados. Lo de "hoy" es lo que en Field
    quedaba mezclado con el mes: en una pantalla del pasillo lo que importa es
    quién cumple HOY, y eso además dispara la toma de pantalla con confeti.
    """
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        mes = _dt.date.today().month
        hoy = _dt.date.today().day
        cumpleanos = _personas(cur, mes)
        aniversarios = _aniversarios(cur, mes)

    return {
        "cumpleanos": {
            "hoy": [p for p in cumpleanos if p["dia"] == hoy],
            "del_mes": cumpleanos,
        },
        "aniversarios": {
            "hoy": [a for a in aniversarios if a["dia"] == hoy],
            "del_mes": aniversarios,
        },
    }


# ── MÉTRICAS ────────────────────────────────────────────────────────────────
def metricas(sunday: str) -> dict:
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT TOP 1 Cliente, COUNT(*) AS total
            FROM ReportesServicio
            WHERE Fecha >= %s
            GROUP BY Cliente
            ORDER BY total DESC
        """, (sunday,))
        top_cliente = cur.fetchone()

        cur.execute("""
            SELECT TOP 1 Tecnico AS nombre, COUNT(*) AS reportes,
                SUM(CASE WHEN FechaHoraInicio IS NOT NULL AND FechaHoraFin IS NOT NULL
                    THEN DATEDIFF(MINUTE, FechaHoraInicio, FechaHoraFin) ELSE 0 END) AS minutos
            FROM ReportesServicio
            WHERE FechaHoraInicio IS NOT NULL AND FechaHoraFin IS NOT NULL AND Fecha >= %s
            GROUP BY Tecnico
            ORDER BY minutos DESC
        """, (sunday,))
        top_ingeniero = cur.fetchone()
        if top_ingeniero and top_ingeniero.get("minutos"):
            top_ingeniero["horas_totales"] = round(top_ingeniero["minutos"] / 60, 1)
        else:
            top_ingeniero = None

        # Heatmap: eventos por (día de la semana, hora) en los últimos 14 días.
        # Un solo GROUP BY sobre una unión de las tres tablas: es la forma más
        # barata de tener "la oficina a qué hora trabaja".
        #
        # OJO con el CAST: en `ReportesServicio`, `Fecha` es de tipo `date`, y
        # DATEPART(hour, ...) no existe para `date` (error 9810). Por eso las
        # tres columnas se castean a DATETIME.
        cur.execute("""
            SELECT dia, hora, COUNT(*) AS valor FROM (
                SELECT DATEPART(weekday, CAST(Fecha AS DATETIME)) - 1 AS dia,
                       DATEPART(hour, CAST(Fecha AS DATETIME)) AS hora
                FROM ReportesServicio WHERE Fecha >= DATEADD(DAY, -14, CAST(GETDATE() AS DATE))
                UNION ALL
                SELECT DATEPART(weekday, FechaHora) - 1, DATEPART(hour, FechaHora)
                FROM HUB_RegistroKilometros WHERE FechaHora >= DATEADD(DAY, -14, GETDATE())
                UNION ALL
                SELECT DATEPART(weekday, FechaRegistro) - 1, DATEPART(hour, FechaRegistro)
                FROM HUB_OxxoGasTickets WHERE FechaRegistro >= DATEADD(DAY, -14, GETDATE())
            ) x GROUP BY dia, hora
        """)
        pulso = [p for p in cur.fetchall() if 0 <= p["dia"] <= 6 and 0 <= p["hora"] <= 23]

        # Actividad de la última hora y el último evento (para la pantalla ⚡).
        cur.execute("""
            SELECT TOP 1
                CONCAT(u.Nombre, ' · ', a.MarcaModelo, ' · lectura ',
                       FORMAT(k.Kilometros, 'N0'), ' km') AS texto,
                CONVERT(VARCHAR(16), k.FechaHora, 120) AS fecha
            FROM HUB_RegistroKilometros k
            JOIN HUB_Users u ON k.IdUsuario = u.Id
            JOIN HUB_Automoviles a ON k.IdAutomovil = a.Id
            ORDER BY k.Id DESC
        """)
        ultimo = cur.fetchone()

        cur.execute("""
            SELECT COUNT(*) AS total FROM (
                SELECT Fecha FROM ReportesServicio WHERE Fecha >= DATEADD(HOUR, -1, GETDATE())
                UNION ALL
                SELECT FechaHora FROM HUB_RegistroKilometros WHERE FechaHora >= DATEADD(HOUR, -1, GETDATE())
                UNION ALL
                SELECT FechaRegistro FROM HUB_OxxoGasTickets WHERE FechaRegistro >= DATEADD(HOUR, -1, GETDATE())
            ) x
        """)
        actividad = cur.fetchone()["total"]

        cur.execute("""
            SELECT TOP 1 u.Nombre AS nombre, COUNT(*) AS total
            FROM ReportesServicio r
            JOIN HUB_Users u ON r.Tecnico = u.Nombre
            WHERE r.Fecha >= %s
            GROUP BY u.Nombre
            ORDER BY total DESC
        """, (sunday,))
        top_dia = cur.fetchone()

        # Reportes por día de la semana (domingo..sábado) para el mini-gráfico.
        cur.execute("""
            SELECT DATEPART(weekday, CAST(Fecha AS DATETIME)) - 1 AS dia, COUNT(*) AS total
            FROM ReportesServicio
            WHERE Fecha >= %s
            GROUP BY DATEPART(weekday, CAST(Fecha AS DATETIME)) - 1
        """, (sunday,))
        _por_dia = {int(r["dia"]): int(r["total"]) for r in cur.fetchall()}
        reportes_por_dia = [_por_dia.get(d, 0) for d in range(7)]

        # Tasa de firma: qué % de los reportes de la semana ya están firmados.
        cur.execute("""
            SELECT COUNT(*) AS total FROM ReportesServicio
            WHERE Estatus = 'Firmado' AND Fecha >= %s
        """, (sunday,))
        firmados_sem = cur.fetchone()["total"] or 0
        total_sem = sum(reportes_por_dia) if reportes_por_dia else 0
        tasa_firma = round((firmados_sem / total_sem * 100), 1) if total_sem > 0 else 0.0

    return {
        "top_cliente": top_cliente,
        "top_ingeniero": top_ingeniero,
        "pulso": pulso,
        "actividad_hora": actividad,
        "ultimo_evento": (
            {"texto": ultimo["texto"], "meta": ultimo["fecha"]}
            if ultimo else None
        ),
        "top_del_dia": (
            {"nombre": top_dia["nombre"], "valor": top_dia["total"], "unidad": "reportes"}
            if top_dia else None
        ),
        "reportes_por_dia": reportes_por_dia,
        "tasa_firma": tasa_firma,
    }


# ── Cursores para detectar eventos nuevos ───────────────────────────────────
def cursores_para_eventos() -> dict:
    """
    último Id y la fecha del último registro de cada tabla "viva". El
    snapshotter los compara con lo que tenía en state.json y de ahí salen los
    avisos de la pantalla.
    """
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        out = {}
        # (clave, tabla, columna de identidad, columna de fecha). OJO: la
        # identidad NO siempre se llama `Id` — en ReportesServicio es
        # `IdReporte`, y ese fue el bug del primer arranque.
        for clave, tabla, col_id, col_fecha in (
            ("km", "HUB_RegistroKilometros", "Id", "FechaHora"),
            ("tickets", "HUB_OxxoGasTickets", "Id", "FechaRegistro"),
            ("reportes", "ReportesServicio", "IdReporte", "Fecha"),
            ("notas", "HUB_DashboardNotas", "Id", "FechaModificado"),
        ):
            try:
                # MAX(id) y MAX(fecha) por separado: mezclar la identidad con un
                # agregado en la misma lista da "columna sin nombre" en SQL
                # Server, que es lo que rompía el primer ciclo.
                cur.execute(
                    f"SELECT ISNULL(MAX({col_id}), 0) AS id, MAX({col_fecha}) AS ultimo FROM {tabla}")
                fila = cur.fetchone()
                out[clave] = {"id": fila["id"] or 0, "fecha": _s(fila["ultimo"], hora=True)}
            except Exception as exc:          # una tabla que falte no tumba el ciclo
                out[clave] = {"id": 0, "fecha": "", "error": str(exc)[:120]}

        # Reportes recién FIRMADOS: se comparan los que pasaron a Firmado contra
        # el Id que ya se había avisado (mismo truco que el worker de avisos).
        try:
            cur.execute("SELECT ISNULL(MAX(IdReporte),0) AS m FROM ReportesServicio WHERE Estatus = 'Firmado'")
            out["firmados"] = {"id": cur.fetchone()["m"], "fecha": ""}
        except Exception as exc:
            out["firmados"] = {"id": 0, "fecha": "", "error": str(exc)[:120]}

        try:
            cur.execute("SELECT ISNULL(MAX(Id),0) AS m FROM HUB_Notificaciones")
            out["avisos"] = {"id": cur.fetchone()["m"], "fecha": ""}
        except Exception as exc:
            out["avisos"] = {"id": 0, "fecha": "", "error": str(exc)[:120]}

        try:
            cur.execute("SELECT ISNULL(MAX(IdUsuario),0) AS m FROM HUB_WeeklyWinners")
            out["ganadores"] = {"id": cur.fetchone()["m"], "fecha": ""}
        except Exception as exc:
            out["ganadores"] = {"id": 0, "fecha": "", "error": str(exc)[:120]}

        try:
            cur.execute("SELECT ISNULL(MAX(Id),0) AS m FROM HUB_NetworkPresence")
            out["presencia"] = {"id": cur.fetchone()["m"], "fecha": ""}
        except Exception as exc:
            out["presencia"] = {"id": 0, "fecha": "", "error": str(exc)[:120]}

    return out


def detalles_de(desde: dict) -> dict:
    """
    Trae el detalle (folio, cliente, foto…) de los registros a partir de un Id.

    OJO con el nombre y el valor: `desde[t]` es el **último Id ya procesado**
    (el cursor previo), NO cuántos hay nuevos. Antes se pasaba la diferencia
    ("cuántos nuevos") y se usaba como umbral del `WHERE Id >`, así que con
    saltos grandes (primer arranque, worker caido un rato, o 40 km de golpe) el
    `WHERE` no encontraba nada y los eventos se perdían en silencio.

    El recorte fino (cuántos de los encontrados se anuncian) lo hace
    `eventos.detectar`, que sí sabe cuántos son nuevos.
    """
    salida = {"km": [], "tickets": [], "reportes": [], "firmados": [], "avisos": [],
              "presencia": []}
    if not desde:
        return salida
    nuevos = desde
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        if "km" in nuevos:
            cur.execute("""
                SELECT TOP 8 k.Id, a.MarcaModelo, u.Nombre, k.Kilometros,
                    CONVERT(VARCHAR(16), k.FechaHora, 120) AS fecha
                FROM HUB_RegistroKilometros k
                JOIN HUB_Automoviles a ON k.IdAutomovil = a.Id
                JOIN HUB_Users u ON k.IdUsuario = u.Id
                WHERE k.Id > %s ORDER BY k.Id DESC
            """, (nuevos["km"],))
            salida["km"] = cur.fetchall()

        if "tickets" in nuevos:
            cur.execute("""
                SELECT TOP 6 t.Id, t.FolioTicket, a.MarcaModelo, u.Nombre,
                    ISNULL(c.Cliente, t.IdCliente) AS cliente, t.Descripcion,
                    CONVERT(VARCHAR(16), t.FechaRegistro, 120) AS fecha
                FROM HUB_OxxoGasTickets t
                LEFT JOIN HUB_Automoviles a ON t.IdVehiculo = a.Id
                JOIN HUB_Users u ON t.IdUsuario = u.Id
                LEFT JOIN clientes c ON t.IdCliente = c.IdCliente
                WHERE t.Id > %s ORDER BY t.Id DESC
            """, (nuevos["tickets"],))
            salida["tickets"] = cur.fetchall()

        if "reportes" in nuevos:
            cur.execute("""
                SELECT TOP 6 IdReporte, Folio, Cliente, Tecnico,
                    CAST(Fecha AS VARCHAR(10)) AS fecha, Estatus
                FROM ReportesServicio WHERE IdReporte > %s ORDER BY IdReporte DESC
            """, (nuevos["reportes"],))
            salida["reportes"] = cur.fetchall()

        if "firmados" in nuevos:
            cur.execute("""
                SELECT TOP 6 IdReporte, Folio, Cliente, Tecnico
                FROM ReportesServicio
                WHERE Estatus = 'Firmado' AND IdReporte > %s
                ORDER BY IdReporte DESC
            """, (nuevos["firmados"],))
            salida["firmados"] = cur.fetchall()

        if "presencia" in nuevos:
            # Entradas y salidas de la oficina detectadas por MAC. Es lo que
            # escribe el network_scanner_worker; el kiosco sólo lo lee.
            cur.execute("""
                SELECT TOP 8 p.Id, p.TipoEvento, p.FechaHora, p.Confianza,
                       d.IdUsuario, d.NombreDispositivo, d.Tipo,
                       ISNULL(u.Nombre, '(sin usuario)') AS Nombre
                FROM HUB_NetworkPresence p
                JOIN HUB_NetworkDevices d ON d.Id = p.IdDispositivo
                LEFT JOIN HUB_Users u ON u.Id = d.IdUsuario
                WHERE p.Id > %s ORDER BY p.Id DESC
            """, (nuevos["presencia"],))
            salida["presencia"] = cur.fetchall()

        if "avisos" in nuevos:
            cur.execute("""
                SELECT TOP 4 Id, Titulo, Mensaje, Autor,
                    CONVERT(VARCHAR(16), FechaEnvio, 120) AS fecha
                FROM HUB_Notificaciones
                WHERE Id > %s AND ISNULL(Titulo,'') NOT LIKE '%test%'
                  AND ISNULL(Mensaje,'') NOT LIKE '%test%'
                ORDER BY Id DESC
            """, (nuevos["avisos"],))
            salida["avisos"] = cur.fetchall()

    return salida


def avatares() -> dict:
    """{IdUsuario: bytes} para los que tengan avatar. Se guardan como archivo."""
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("SELECT IdUsuario, AvatarBase64 FROM HUB_UserAvatars")
        return {r["IdUsuario"]: r["AvatarBase64"] for r in cur.fetchall()
                if r.get("AvatarBase64")}


def fotos_usuarios() -> dict:
    """
    {IdUsuario: bytes} con la FOTO real (retrato) del usuario, desde
    `HUB_UsuariosFotos.Archivo` (VARBINARY, la imagen tal cual). NO es el avatar
    IA de `HUB_UserAvatars` (ésos los sigue usando Legends). Se convierte en
    archivo en /media/usuarios/u<Id>.jpg y se usa en Celebraciones y Asistencia;
    si el usuario no tiene foto, el front cae al avatar de Legends.
    """
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT f.IdUsuario, f.Archivo
            FROM HUB_UsuariosFotos f
            JOIN HUB_Users u ON u.Id = f.IdUsuario
            WHERE u.Activo = 1 AND f.Archivo IS NOT NULL
        """)
        return {r["IdUsuario"]: r["Archivo"] for r in cur.fetchall() if r.get("Archivo")}


def _dump(x) -> str:
    """Para depurar desde la consola."""
    return json.dumps(x, ensure_ascii=False, default=str, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# Combustible: vales, costos, precios por estación, consumo, personas, tiempos
# ═══════════════════════════════════════════════════════════════════════════
def combustible(sunday: str, hoy: str) -> dict:
    """Todo el tablero de combustible en una sola pasada (solo lectura).

    Regla de dinero: el gasto usa `MontoEmitido` (lo que de verdad salió). Un
    vale sin monto emitido NO se suma como 500: suma a «sin comprobante».
    """
    hoy_d = _dt.date.fromisoformat(hoy)
    inicio_mes = hoy_d.replace(day=1)
    inicio_mes_ant = (inicio_mes - _dt.timedelta(days=1)).replace(day=1)
    fin_mes_ant = inicio_mes - _dt.timedelta(days=1)
    hace_28 = hoy_d - _dt.timedelta(days=27)
    umbral = 2000.0

    res = {
        "resumen": {}, "semanas": [], "por_auto": [], "por_usuario": [],
        "estaciones": [], "clientes": [], "horas": [0] * 24, "dias": [0] * 7,
        "tiempos": {}, "calidad": {}, "saldo": None, "umbral": umbral,
    }

    estado = {"fallos": 0}

    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)

        def q(sql, params=()):
            """Una consulta. Si la base da un tirón, se reabre UNA vez; si ya
            van tres fallos seguidos, se corta: seguir golpeando un SQL sin
            memoria solo alarga el ciclo y deja el snapshot viejo igual."""
            nonlocal conn, cur
            try:
                cur.execute(sql, params)
                estado["fallos"] = 0
                return cur.fetchall()
            except Exception as e:
                print(f"[datos.combustible] {str(e)[:120]}")
                estado["fallos"] += 1
                if estado["fallos"] >= 3:
                    raise RuntimeError("la base no responde; se corta el bloque") from e
                try:
                    conn.close()
                except Exception:
                    pass
                conn = get_connection()
                cur = conn.cursor(as_dict=True)
                try:
                    cur.execute(sql, params)
                    return cur.fetchall()
                except Exception as e2:
                    print(f"[datos.combustible] reintento: {str(e2)[:120]}")
                    return []

        # ── Resumen del mes y del anterior ──
        base = """
            SELECT COUNT(*) AS n,
                   SUM(CASE WHEN MontoEmitido IS NOT NULL THEN MontoEmitido ELSE 0 END) AS gasto,
                   SUM(CASE WHEN MontoEmitido IS NULL THEN 1 ELSE 0 END) AS sin_monto,
                   AVG(CASE WHEN MontoEmitido IS NOT NULL THEN MontoEmitido ELSE MontoUnit END) AS prom
            FROM HUB_SolicitudVales
            WHERE FechaSolicitud >= %s AND FechaSolicitud < %s
        """
        act = (q(base, (inicio_mes.isoformat(), (hoy_d + _dt.timedelta(days=1)).isoformat()))
               or [{}])[0]
        ant = (q(base, (inicio_mes_ant.isoformat(), (fin_mes_ant + _dt.timedelta(days=1)).isoformat()))
               or [{}])[0]
        gasto = float(act.get("gasto") or 0)
        gasto_ant = float(ant.get("gasto") or 0)

        # Dinero sin comprobante: vale emitido sin ticket. MISMA VENTANA que el
        # bloque `pendientes` del kiosco (temporada en curso): el corte sale de
        # `HUB_Config.comprobantes_desde` y se normaliza con `corte_temporada`,
        # igual que allí. Antes esta consulta no tenía cota de fecha y el
        # tablero de combustible y el bloque `pendientes` daban dos números
        # distintos del mismo concepto (todo el histórico vs. la temporada).
        # El ajuste se lee con el cursor que ya está abierto: no se abre otra
        # conexión.
        corte_cfg = q("SELECT Valor FROM HUB_Config WHERE Clave = %s",
                      ("comprobantes_desde",))
        desde_sin_comp = corte_temporada(
            (corte_cfg[0].get("Valor") if corte_cfg else None))
        sin_comp = q("""
            SELECT COUNT(*) AS n,
                   SUM(CASE WHEN MontoEmitido IS NOT NULL THEN MontoEmitido ELSE 0 END) AS monto
            FROM HUB_SolicitudVales
            WHERE Estatus IN ('GENERADO', 'CONSUMIDO') AND IdTicketCierre IS NULL
              AND FechaSolicitud >= %s
        """, (desde_sin_comp,)) or [{}]
        sin_comp = sin_comp[0]

        saldo_fila = q("SELECT Valor FROM HUB_Config WHERE Clave = 'govale_saldo'")
        saldo = None
        if saldo_fila:
            try:
                saldo = float(saldo_fila[0]["Valor"])
            except (TypeError, ValueError):
                saldo = None

        res["resumen"] = {
            "gasto_mes": gasto,
            "gasto_mes_anterior": gasto_ant,
            "variacion_pct": (round((gasto - gasto_ant) / gasto_ant * 100, 1)
                              if gasto_ant else None),
            "vales_mes": int(act.get("n") or 0),
            "promedio": float(act.get("prom") or 0),
            "vales_sin_monto": int(act.get("sin_monto") or 0),
            "sin_comprobante_n": int(sin_comp.get("n") or 0),
            "sin_comprobante_monto": float(sin_comp.get("monto") or 0),
            # Ventana del número de arriba: es la temporada, no el histórico.
            "sin_comprobante_desde": desde_sin_comp,
            "saldo": saldo,
            "alcanza_vales": (int(saldo // 500) if saldo is not None else None),
        }

        # ── Vales por semana (últimos 28 días) ──
        res["semanas"] = q("""
            SELECT DATEPART(year, FechaSolicitud) AS anio,
                   DATEPART(week, FechaSolicitud) AS semana,
                   COUNT(*) AS vales,
                   SUM(CASE WHEN MontoEmitido IS NOT NULL THEN MontoEmitido ELSE 0 END) AS monto
            FROM HUB_SolicitudVales
            WHERE FechaSolicitud >= %s
            GROUP BY DATEPART(year, FechaSolicitud), DATEPART(week, FechaSolicitud)
            ORDER BY anio, semana
        """, (hace_28.isoformat(),))

        # ── Por auto: vales, monto, litros y km del periodo ──
        autos = q("""
            SELECT S.IdAutomovil AS id, A.MarcaModelo AS marca, A.Placas AS placas,
                   COUNT(*) AS vales,
                   SUM(CASE WHEN S.MontoEmitido IS NOT NULL THEN S.MontoEmitido ELSE 0 END) AS monto
            FROM HUB_SolicitudVales S
            LEFT JOIN HUB_Automoviles A ON A.Id = S.IdAutomovil
            WHERE S.FechaSolicitud >= %s
            GROUP BY S.IdAutomovil, A.MarcaModelo, A.Placas
            ORDER BY monto DESC
        """, (hace_28.isoformat(),))

        litros_auto = {f["id"]: float(f["litros"] or 0) for f in q("""
            SELECT IdVehiculo AS id, SUM(XmlLitros) AS litros
            FROM HUB_OxxoGasVales
            WHERE Fecha >= %s AND IdVehiculo IS NOT NULL AND XmlLitros > 0
            GROUP BY IdVehiculo
        """, (hace_28.isoformat(),))}

        # Km: primera y última lectura del periodo por auto (el odómetro no se suma).
        km_auto = {}
        for f in q("""
            SELECT v.IdAutomovil AS id,
                   MAX(v.Kilometros) AS km_max, MIN(v.Kilometros) AS km_min,
                   COUNT(*) AS lecturas
            FROM HUB_RegistroKilometros v
            WHERE v.FechaHora >= %s
            GROUP BY v.IdAutomovil
        """, (hace_28.isoformat(),)):
            if f["lecturas"] and int(f["lecturas"]) >= 2:
                km_auto[f["id"]] = max(0, float(f["km_max"]) - float(f["km_min"]))

        for a in autos:
            # El litro por auto no existe: la factura no guarda el vehículo.
            # Se deja en None y la pantalla muestra «—» en vez de inventar.
            litros = litros_auto.get(a["id"], 0.0)
            km = km_auto.get(a["id"], 0.0)
            a["litros"] = round(litros, 1) if litros else None
            a["km"] = round(km, 1)
            a["km_l"] = None
            a["costo_km"] = round(float(a["monto"] or 0) / km, 2) if km > 0 else None
            a["monto"] = float(a["monto"] or 0)
        res["por_auto"] = autos

        # ── Por usuario ──
        res["por_usuario"] = q("""
            SELECT U.Nombre AS nombre, COUNT(*) AS vales,
                   SUM(CASE WHEN S.MontoEmitido IS NOT NULL THEN S.MontoEmitido ELSE 0 END) AS monto
            FROM HUB_SolicitudVales S LEFT JOIN HUB_Users U ON U.Id = S.IdSolicitante
            WHERE S.FechaSolicitud >= %s
            GROUP BY U.Nombre
            ORDER BY vales DESC
        """, (hace_28.isoformat(),))

        # ── Estaciones: visitas por ticket ──
        #
        # El CFDI NO trae la gasolinera (XmlEstacion es la razón social, repetida
        # en todas) ni el vehículo, así que el precio POR estación no se puede
        # calcular. Lo que sí es real: cuántas veces se carga en cada estación.
        res["estaciones"] = q("""
            SELECT TOP 8 ISNULL(NULLIF(LTRIM(RTRIM(Estacion)), ''), 'Sin estación') AS estacion,
                   COUNT(*) AS tickets
            FROM HUB_OxxoGasTickets
            WHERE FechaRegistro >= %s
            GROUP BY ISNULL(NULLIF(LTRIM(RTRIM(Estacion)), ''), 'Sin estación')
            ORDER BY tickets DESC
        """, (hace_28.isoformat(),))

        # Precio por litro del periodo: solo facturas con litros reales.
        # Muchas vienen con XmlLitros = 1 (dato malo del CFDI): incluirlas daba
        # $431 el litro. Con litros > 1 el número es creíble (~$21-26).
        pl = q("""
            SELECT SUM(Monto) AS monto, SUM(XmlLitros) AS litros, COUNT(*) AS facturas
            FROM HUB_OxxoGasVales
            WHERE Fecha >= %s AND XmlLitros > 1
        """, (hace_28.isoformat(),)) or [{}]
        monto_l = float(pl[0].get("monto") or 0)
        litros_l = float(pl[0].get("litros") or 0)
        res["precio_l"] = round(monto_l / litros_l, 2) if litros_l > 0 else None
        res["litros"] = round(litros_l, 1)

        # ── Clientes más visitados ──
        res["clientes"] = q("""
            SELECT TOP 6 ISNULL(C.Cliente, T.IdCliente) AS cliente, COUNT(*) AS tickets
            FROM HUB_OxxoGasTickets T
            LEFT JOIN (SELECT IdCliente, MIN(Cliente) AS Cliente FROM clientes
                       GROUP BY IdCliente) C ON C.IdCliente = T.IdCliente
            WHERE T.FechaRegistro >= %s
            GROUP BY C.Cliente, T.IdCliente
            ORDER BY tickets DESC
        """, (hace_28.isoformat(),))

        # ── Horas y días de consumo ──
        for f in q("""
            SELECT DATEPART(hour, CAST(FechaRegistro AS DATETIME)) AS h, COUNT(*) AS n
            FROM HUB_OxxoGasTickets WHERE FechaRegistro >= %s
            GROUP BY DATEPART(hour, CAST(FechaRegistro AS DATETIME))
        """, (hace_28.isoformat(),)):
            if f["h"] is not None and 0 <= int(f["h"]) < 24:
                res["horas"][int(f["h"])] = int(f["n"])

        for f in q("""
            SELECT DATEPART(weekday, CAST(FechaRegistro AS DATETIME)) AS d, COUNT(*) AS n
            FROM HUB_OxxoGasTickets WHERE FechaRegistro >= %s
            GROUP BY DATEPART(weekday, CAST(FechaRegistro AS DATETIME))
        """, (hace_28.isoformat(),)):
            if f["d"] is not None and 1 <= int(f["d"]) <= 7:
                res["dias"][int(f["d"]) - 1] = int(f["n"])

        # ── Tiempos ──
        t = q("""
            SELECT AVG(DATEDIFF(minute, FechaSolicitud, FechaAprobado)) AS prom,
                   MAX(DATEDIFF(minute, FechaSolicitud, FechaAprobado)) AS peor
            FROM HUB_SolicitudVales
            WHERE FechaAprobado IS NOT NULL AND FechaSolicitud >= %s
        """, (hace_28.isoformat(),)) or [{}]
        res["tiempos"] = {
            "pedir_generar_min": round(float(t[0].get("prom") or 0), 1),
            "pedir_generar_peor_min": int(t[0].get("peor") or 0),
        }

        # ── Calidad del registro ──
        cal = q("""
            SELECT
              SUM(CASE WHEN CodigoQR IS NULL OR LTRIM(RTRIM(CodigoQR)) = '' THEN 1 ELSE 0 END) AS sin_codigo,
              SUM(CASE WHEN MontoEmitido IS NULL THEN 1 ELSE 0 END) AS sin_monto,
              SUM(CASE WHEN MontoEmitido IS NOT NULL AND ABS(MontoEmitido - 500) > 0.01 THEN 1 ELSE 0 END) AS monto_raro,
              COUNT(*) AS total
            FROM HUB_SolicitudVales
            WHERE FechaSolicitud >= %s AND Estatus IN ('GENERADO','CERRADO','CONSUMIDO')
        """, (hace_28.isoformat(),)) or [{}]
        cob = q("""
            SELECT COUNT(*) AS tickets,
                   SUM(CASE WHEN IdSolicitudVale IS NOT NULL THEN 1 ELSE 0 END) AS con_vale,
                   SUM(CASE WHEN ImagenTicket IS NOT NULL THEN 1 ELSE 0 END) AS con_foto
            FROM HUB_OxxoGasTickets WHERE FechaRegistro >= %s
        """, (hace_28.isoformat(),)) or [{}]
        res["calidad"] = {
            "sin_codigo": int(cal[0].get("sin_codigo") or 0),
            "sin_monto": int(cal[0].get("sin_monto") or 0),
            "monto_raro": int(cal[0].get("monto_raro") or 0),
            "total_vales": int(cal[0].get("total") or 0),
            "tickets": int(cob[0].get("tickets") or 0),
            "tickets_con_vale": int(cob[0].get("con_vale") or 0),
            "tickets_con_foto": int(cob[0].get("con_foto") or 0),
        }

    return res



# ═══════════════════════════════════════════════════════════════════════════
# Avisos para Volt: lo mismo que el vigilante manda por Telegram, pero en la
# pantalla del pasillo. La tabla la escribe WorkersAdmon; aquí solo se lee.
# ═══════════════════════════════════════════════════════════════════════════
def volt_avisos(limite: int = 8) -> list:
    """Últimos avisos vivos (48 h). Nunca lanza: si la tabla no existe todavía
    o la BD no responde, devuelve [] y la pantalla sigue con su charla."""
    limite = max(1, min(int(limite), 20))
    try:
        with get_connection() as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(f"""
                SELECT TOP ({limite}) Id, Fecha, Tipo, Nivel, Texto
                FROM HUB_VoltAvisos
                WHERE Activo = 1 AND Fecha >= DATEADD(hour, -48, GETDATE())
                ORDER BY Id DESC
            """)
            filas = cur.fetchall()
    except Exception as e:
        print(f"[datos.volt_avisos] {str(e)[:160]}")
        return []

    salida = []
    for f in filas:
        texto = (f.get("Texto") or "").strip()
        if not texto:
            continue
        fecha = f.get("Fecha")
        salida.append({
            "id": int(f["Id"]),
            "texto": texto,
            "tipo": (f.get("Tipo") or "vigilante").strip(),
            "nivel": (f.get("Nivel") or "info").strip(),
            "fecha": fecha.strftime("%Y-%m-%d %H:%M") if fecha else None,
        })
    return salida


# ═══════════════════════════════════════════════════════════════════════════
# Pendientes de comprobante: vales de la temporada sin foto de ticket + los
# últimos vales. El cálculo (y su forma) vive en `pendientes.py`, que no toca
# la base; aquí sólo se leen las filas.
# ═══════════════════════════════════════════════════════════════════════════
def _config(clave: str, defecto=None):
    """Un valor de `HUB_Config`. Nunca lanza: si la tabla o la BD no están, se
    queda el valor por defecto (la pantalla no puede depender de un ajuste)."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT Valor FROM HUB_Config WHERE Clave = %s", (clave,))
            fila = cur.fetchone()
            return fila[0] if fila else defecto
    except Exception:
        return defecto


def pendientes_snapshot() -> dict:
    """Pendientes de la temporada + últimos vales (la lista que nunca se vacía).

    OJO: aquí NO hay `try/except`, a diferencia de `volt_avisos`. Un fallo de la
    base tiene que llegar a `_bloque` en el snapshotter, que reusa el bloque del
    snapshot anterior y marca el ciclo como degradado (healthz 503). Si se
    atrapara aquí y se devolviera la forma vacía, la pantalla enseñaría «0
    vales» —un cero falso— y además nadie se enteraría del fallo.
    """
    desde = corte_temporada(_config("comprobantes_desde"))
    with get_connection() as conn:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """SELECT COUNT(*) AS n,
                      SUM(CASE WHEN MontoEmitido IS NOT NULL THEN MontoEmitido ELSE 0 END) AS monto
               FROM HUB_SolicitudVales
               WHERE Estatus IN ('GENERADO','CONSUMIDO') AND IdTicketCierre IS NULL
                 AND FechaSolicitud >= %s""", (desde,))
        totales = cur.fetchone() or {}
        cur.execute(
            """SELECT TOP 6 S.IdSolicitante AS id_usuario,
                      ISNULL(U.Nombre, '—') AS persona, S.Placa,
                      S.MontoEmitido AS monto,
                      DATEDIFF(day, S.FechaSolicitud, GETDATE()) AS dias,
                      CASE WHEN S.IdTicketCierre IS NULL THEN 0 ELSE 1 END AS cerrado
               FROM HUB_SolicitudVales S
               LEFT JOIN HUB_Users U ON U.Id = S.IdSolicitante
               WHERE S.Estatus IN ('GENERADO','CONSUMIDO','CERRADO')
               ORDER BY S.FechaSolicitud DESC""")
        ultimos = cur.fetchall()
    return armar_pendientes(totales, ultimos, desde)
