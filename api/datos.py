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

from db import get_connection

DIAS_SEMANA = 7


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
    with conn.cursor(as_dict=True) as cur:
        cur.execute("SELECT ISNULL(SUM(Kilometros),0) AS total FROM HUB_RegistroKilometros WHERE FechaHora >= %s", (sunday,))
        total_semana = cur.fetchone()["total"] or 0
        cur.execute("""
            SELECT ISNULL(SUM(k.Kilometros),0) AS total
            FROM HUB_RegistroKilometros k
            WHERE CAST(k.FechaHora AS DATE) = %s
        """, (hoy,))
        km_hoy = cur.fetchone()["total"] or 0

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
        cur.execute("SELECT COUNT(*) AS total FROM HUB_OxxoGasTickets WHERE FechaRegistro >= %s", (sunday,))
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT TOP 12 t.Id AS id_ticket, t.FolioTicket AS folio,
                a.MarcaModelo AS vehiculo, a.Placas,
                u.Nombre AS usuario,
                CONVERT(VARCHAR(16), t.FechaRegistro, 120) AS fecha,
                ISNULL(c.Cliente, t.IdCliente) AS cliente,
                ISNULL(t.Descripcion, '') AS descripcion
            FROM HUB_OxxoGasTickets t
            LEFT JOIN HUB_Automoviles a ON t.IdVehiculo = a.Id
            JOIN HUB_Users u ON t.IdUsuario = u.Id
            LEFT JOIN clientes c ON t.IdCliente = c.IdCliente
            WHERE t.FechaRegistro >= %s
            ORDER BY t.Id DESC
        """, (sunday,))
        ultimos = cur.fetchall()

        cur.execute("""
            SELECT TOP 8 a.MarcaModelo AS vehiculo, COUNT(*) AS total_tickets
            FROM HUB_OxxoGasTickets t
            JOIN HUB_Automoviles a ON t.IdVehiculo = a.Id
            WHERE t.FechaRegistro >= %s
            GROUP BY a.MarcaModelo
            ORDER BY total_tickets DESC
        """, (sunday,))
        por_vehiculo = cur.fetchall()

    return {"total_semana": total, "ultimos": ultimos, "por_vehiculo": por_vehiculo}


# ── LEGENDS ─────────────────────────────────────────────────────────────────
def legends() -> dict:
    """
    Solo usuarios con passkey (misma regla que en Field: el Legends se juega
    entre quienes usan la app, no entre los de la planilla).
    `puesto_anterior` se calcula en el snapshotter comparando con el ranking
    previo guardado en state.json: es lo que dibuja las flechas ↑↓.
    """
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT TOP 10
                u.Id AS id_usuario,
                u.Nombre AS nombre,
                ISNULL(u.Nickname, u.Nombre) AS nickname,
                ISNULL(s.PuntuacionSemanal, 0) AS puntos,
                ISNULL(s.Nivel, 'Bronce') AS nivel
            FROM HUB_Users u
            LEFT JOIN HUB_UserScores s ON s.IdUsuario = u.Id
            WHERE u.Activo = 1
              AND EXISTS (SELECT 1 FROM HUB_Passkeys p WHERE p.IdUsuario = u.Id)
            ORDER BY ISNULL(s.PuntuacionSemanal, 0) DESC
        """)
        ranking = cur.fetchall()

        cur.execute("""
            SELECT TOP 1 u.Nombre AS nombre, w.PuntuacionSemana AS puntos,
                CONVERT(VARCHAR(10), w.FechaInicio, 120) AS desde
            FROM HUB_WeeklyWinners w
            JOIN HUB_Users u ON w.IdUsuario = u.Id
            ORDER BY w.FechaInicio DESC
        """)
        ganador = cur.fetchone()

        cur.execute("SELECT ISNULL(SUM(PuntuacionSemanal),0) AS total FROM HUB_UserScores")
        total_pts = cur.fetchone()["total"]

    # El avatar NO viaja en el JSON: es un base64 de decenas de KB por persona.
    # El snapshotter lo convierte en un archivo en /media/avatars/u<Id>.jpg y
    # reemplaza `id_usuario` por la ruta, así que aquí el id se conserva.
    # (Antes se quitaba acá y el ranking llegaba sin avatar a la pantalla.)

    # Segundos para el próximo reinicio (domingo 00:00 hora del servidor).
    ahora = _dt.datetime.now()
    dias = (6 - ahora.weekday()) % 7  # 0 = domingo
    proximo = (ahora + _dt.timedelta(days=dias)).replace(hour=0, minute=0, second=0, microsecond=0)
    if proximo <= ahora:
        proximo += _dt.timedelta(days=7)
    reset_en = int((proximo - ahora).total_seconds())

    return {
        "ranking": ranking,
        "ganador_semana": ganador,
        "total_puntos": total_pts,
        "reset_en_segundos": reset_en,
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

    return out


def detalles_de(nuevos: dict) -> dict:
    """
    Trae el detalle (folio, cliente, foto…) de los registros nuevos que se van
    a anunciar. `nuevos` son los Id ya detectados por cursores_para_eventos.
    """
    salida = {"km": [], "tickets": [], "reportes": [], "firmados": [], "avisos": []}
    if not any(nuevos.values()):
        return salida
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        if nuevos.get("km"):
            cur.execute("""
                SELECT TOP 8 k.Id, a.MarcaModelo, u.Nombre, k.Kilometros,
                    CONVERT(VARCHAR(16), k.FechaHora, 120) AS fecha
                FROM HUB_RegistroKilometros k
                JOIN HUB_Automoviles a ON k.IdAutomovil = a.Id
                JOIN HUB_Users u ON k.IdUsuario = u.Id
                WHERE k.Id > %s ORDER BY k.Id DESC
            """, (nuevos["km"],))
            salida["km"] = cur.fetchall()

        if nuevos.get("tickets"):
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

        if nuevos.get("reportes"):
            cur.execute("""
                SELECT TOP 6 IdReporte, Folio, Cliente, Tecnico,
                    CAST(Fecha AS VARCHAR(10)) AS fecha, Estatus
                FROM ReportesServicio WHERE IdReporte > %s ORDER BY IdReporte DESC
            """, (nuevos["reportes"],))
            salida["reportes"] = cur.fetchall()

        if nuevos.get("firmados"):
            cur.execute("""
                SELECT TOP 6 IdReporte, Folio, Cliente, Tecnico
                FROM ReportesServicio
                WHERE Estatus = 'Firmado' AND IdReporte > %s
                ORDER BY IdReporte DESC
            """, (nuevos["firmados"],))
            salida["firmados"] = cur.fetchall()

        if nuevos.get("avisos"):
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


def _dump(x) -> str:
    """Para depurar desde la consola."""
    return json.dumps(x, ensure_ascii=False, default=str, indent=2)
