"""
eventos.py — de los deltas de la base a los avisos de la pantalla.

Cómo funciona, y por qué NO usa la base para acordarse:

  el snapshotter guarda en `/data/state.json` el último Id que vio de cada tabla
  "viva" (km, tickets, reportes, notas, avisos). En cada ciclo compara: lo que
  aparece con Id mayor es nuevo. Eso produce los avisos que ve la pantalla.

  · por qué el estado está en un archivo y no en `HUB_Config`: el kiosco es de
    SOLO LECTURA. Escribir el cursor en la base sería una escritura más que
    auditar y que puede tumbar el refresh si dos contenedores se pisan.
  · el cursor se avanza aunque no haya red: si el Id ya se vio, no se vuelve a
    ver aunque el aviso se haya perdido (preferible a repetir 40 avisos).
  · los eventos se acumulan en `/data/eventos.json` (los últimos 100). La
    pantalla deduplica por `id` y en el primer arranque no reproduce el
    historial (si no, la TV saludaría a la oficina con 100 avisos de golpe).

Niveles: `info` (banda), `exito` (toast), `pantalla` (aviso a pantalla
completa, con `confeti: true` si además es celebración) y `alerta` (banda ámbar
con sonido grave).
"""
import datetime as _dt

MAX_PENDIENTES_POR_VUELTA = 4   # no se anuncian 30 km de golpe

# Cuánto dura un aviso a pantalla completa. 10 s es lo justo para leer "quién,
# qué, de dónde" a 3 metros de distancia: más curto pasa inadvertido y más
# largo hace perder el turno de rotación.
SEGUNDOS_PANTALLA = 10

# Una persona no genera más de un aviso de presencia cada N minutos. Sin esto,
# un celular que pierde el WiFi un momento produce SALIDA+ENTRADA cada 3
# minutos y la pantalla se llena del mismo nombre (el detector usa 5 min de
# tolerancia, pero con la red intermitente se pasan).
COOLDOWN_PRESENCIA_MIN = 20


def _log_debug(msg: str) -> None:
    """Salida por stdout; el snapshotter la tee-a a /data/sync.log."""
    import time
    print(f"[{time.strftime('%H:%M:%S')}] eventos: {msg}", flush=True)


def _iso(fecha: str | None = None) -> str:
    if fecha:
        return fecha.replace(" ", "T")
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _corta(texto, n=90):
    t = (texto or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def detectar(cursores_nuevos: dict, cursores_previos: dict, detalles: dict, hoy_cumple: list,
             presencia_previa: dict | None = None) -> list:
    """
    Devuelve la lista de eventos NUEVOS de este ciclo (ya con su `id` estable).
    `cursores_previos` viene de state.json; si está vacío (primer arranque) se
    adelantan los cursores sin anunciar nada: la pantalla no debe gritar al
    encenderse.
    """
    eventos = []
    primero = not cursores_previos
    if primero:
        _log_debug("primer ciclo: cursores adelantados sin anunciar")

    def nuevo(clave):
        """Cuántos registros nuevos hay de esa tabla (0 en el primer arranque).

        En el primer ciclo NO se anuncia nada: la pantalla no debe arrancar
        gritándole 40 avisos a la oficina. Los cursores se adelantan igual
        (eso lo hace el snapshotter), así que tampoco se repiten después.
        """
        if primero:
            return 0
        try:
            return max(0, int(cursores_nuevos[clave]["id"]) - int(cursores_previos.get(clave, 0)))
        except Exception:
            return 0

    # ── Kilómetros ──────────────────────────────────────────────────────────
    # A pantalla completa: es un registro que alguien hizo a mano, y en una TV
    # de pasillo lo que se ve de lejos es "quién y cuántos km", no el detalle.
    n = nuevo("km")
    for f in (detalles.get("km") or [])[:n][:MAX_PENDIENTES_POR_VUELTA]:
        eventos.append({
            "id": f"km:{f['Id']}",
            "nivel": "pantalla",
            "tono": "aviso",
            "icono": "🛣️",
            "modulo": "HUB · Kilómetros",
            "titulo": f"{f['Kilometros']} km",
            "persona": f.get("Nombre") or "",
            "texto": f.get("MarcaModelo") or "vehículo",
            "meta": f.get("fecha") or "",
            "ts": _iso(f.get("fecha")),
            "segundos": SEGUNDOS_PANTALLA,
        })

    # ── Tickets OxxoGas ─────────────────────────────────────────────────────
    n = novo = nuevo("tickets")
    for t in (detalles.get("tickets") or [])[:novo][:MAX_PENDIENTES_POR_VUELTA]:
        # Sin imagen: los tickets se muestran sin foto (2026-09-28) y el aviso a
        # pantalla completa tampoco lleva fotografía, por pedido del usuario: en
        # una pantalla de pasillo una foto de 200 px no dice nada y roba el
        # espacio del texto, que es lo que importa.
        eventos.append({
            "id": f"tkt:{t['Id']}",
            "nivel": "pantalla",
            "tono": "aviso",
            "icono": "🎫",
            "modulo": "HUB · OxxoGas",
            "titulo": f"Ticket {t['FolioTicket']}",
            "persona": t.get("Nombre") or "",
            "texto": t.get("MarcaModelo") or "—",
            "meta": (t.get("Descripcion") or "")[:70],
            "ts": _iso(t.get("fecha")),
            "segundos": SEGUNDOS_PANTALLA,
        })

    # ── Reportes nuevos ─────────────────────────────────────────────────────
    n = nuevo("reportes")
    for r in (detalles.get("reportes") or [])[:n][:2]:
        eventos.append({
            "id": f"rep:{r['IdReporte']}",
            "nivel": "info",
            "icono": "📊",
            "titulo": f"Reporte {r['Folio']}",
            "texto": f"{r['Cliente']} · {r['Tecnico']}",
            "meta": r.get("fecha") or "",
            "ts": _iso(),
        })

    # ── Reporte FIRMADO: sí se destaca (es el evento "bueno" del día) ───────
    n = nuevo("firmados")
    for r in (detalles.get("firmados") or [])[:n][:2]:
        eventos.append({
            "id": f"firmado:{r['IdReporte']}",
            "nivel": "pantalla",
            "tono": "aviso",
            "icono": "✍️",
            "modulo": "Field · Reportes",
            "titulo": f"Reporte firmado",
            "persona": r.get("Tecnico") or "",
            "texto": f"{r['Folio']} · {r['Cliente']}",
            "meta": "firmado por el cliente",
            "ts": _iso(),
            "segundos": SEGUNDOS_PANTALLA,
        })

    # ── Entradas y salidas de la oficina (por MAC) ─────────────────────────
    # A pantalla completa, como pidió el usuario. Lo que evita que sea
    # insoportable no es que sea una banda, es el COOLDOWN de 20 min por
    # persona y tipo: sin él, un celular que pierde el WiFi un momento produce
    # SALIDA+ENTRADA cada 3 minutos y la pantalla se queda en saludos.
    vistos = dict(presencia_previa or {})
    for p in (detalles.get("presencia") or [])[:nuevo("presencia")][:4]:
        id_usuario = p.get("IdUsuario") or 0
        clave = f"{id_usuario}:{p['TipoEvento']}"
        ultima = vistos.get(clave)
        if ultima:
            try:
                if (_dt.datetime.now() - _dt.datetime.fromisoformat(ultima)).total_seconds() < \
                        COOLDOWN_PRESENCIA_MIN * 60:
                    continue
            except Exception:
                pass
        vistos[clave] = _iso()
        entrada = p["TipoEvento"] == "ENTRADA"
        nombre = p.get("Nombre") or "(sin usuario)"
        eventos.append({
            "id": f"presencia:{p['Id']}",
            "nivel": "pantalla",
            "tono": "hola" if entrada else "adios",
            "icono": "👋" if entrada else "🚪",
            "modulo": "Red de la oficina",
            "titulo": f"{'Entró' if entrada else 'Salió'}",
            "persona": nombre,
            "texto": p.get("NombreDispositivo") or "dispositivo",
            "meta": f"{'entró a la oficina' if entrada else 'salió de la oficina'}",
            "ts": _iso(str(p.get("FechaHora"))[:19]),
            "segundos": SEGUNDOS_PANTALLA,
        })
    if presencia_previa is not None:
        presencia_previa.update(vistos)

    # ── Cumpleaños de HOY: el destaque del día ──────────────────────────────
    for p in (hoy_cumple or []):
        eventos.append({
            "id": f"cumple:{_dt.date.today().isoformat()}:{p['Nombre']}",
            "nivel": "pantalla",
            "tono": "exito",
            "icono": "🎂",
            "modulo": "HUB · Celebraciones",
            "titulo": "¡Feliz cumpleaños!",
            "persona": p.get("Nombre") or "",
            "texto": f"{p.get('edad') or '—'} años hoy",
            "meta": "en ECCSA",
            "ts": _iso(),
            "segundos": SEGUNDOS_PANTALLA,
            # El confeti lo lanza el front al abrir este aviso. Antes vivía en
            # el nivel 'destaque', que era una segunda capa de pantalla completa
            # con otro estilo; ahora todo aviso a pantalla completa se ve igual.
            "confeti": True,
        })

    # ── Avisos del admin (HUB_Notificaciones) ──────────────────────────────
    n = nuevo("avisos")
    for a in (detalles.get("avisos") or [])[:n][:2]:
        eventos.append({
            "id": f"aviso:{a['Id']}",
            "nivel": "alerta",
            "icono": "📢",
            "titulo": a.get("Titulo") or "Aviso",
            "texto": _corta(a.get("Mensaje"), 120),
            "meta": a.get("Autor") or "",
            "ts": _iso(a.get("fecha")),
        })

    return eventos


def sin_actividad(ultimo_evento_iso: str | None, horas: int = 6) -> dict | None:
    """
    Si la oficina lleva `horas` sin registrar NADA, se genera un aviso. No es un
    error: en seasons baja la pantalla está igual y saberlo es información.
    """
    if not ultimo_evento_iso:
        return None
    try:
        t = _dt.datetime.fromisoformat(ultimo_evento_iso)
    except Exception:
        return None
    if (_dt.datetime.now() - t).total_seconds() < horas * 3600:
        return None
    return {
        "id": f"silencio:{ultimo_evento_iso}",
        "nivel": "info",
        "icono": "🌙",
        "titulo": "Oficina sin movimiento",
        "texto": f"Sin registros desde hace {horas} h o más",
        "meta": "normal fuera de horario",
        "ts": _iso(),
    }
