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

Niveles: `info` (banda), `exito` (toast), `destaque` (toma de pantalla con
confeti) y `alerta` (banda ámbar con sonido grave).
"""
import datetime as _dt

MAX_PENDIENTES_POR_VUELTA = 4   # no se anuncian 30 km de golpe


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


def detectar(cursores_nuevos: dict, cursores_previos: dict, detalles: dict, hoy_cumple: list) -> list:
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
            return max(0, cursores_nuevos[clave]["id"] - cursores_previos.get(clave, {}).get("id", 0))
        except Exception:
            return 0

    # ── Kilómetros ──────────────────────────────────────────────────────────
    n = nuevo("km")
    for f in (detalles.get("km") or [])[:n][:MAX_PENDIENTES_POR_VUELTA]:
        eventos.append({
            "id": f"km:{f['Id']}",
            "nivel": "info",
            "icono": "🛣️",
            "titulo": f"Kilómetros · {f['MarcaModelo']}",
            "texto": f"{f['Nombre']} registró {f['Kilometros']} km",
            "meta": f.get("fecha") or "",
            "ts": _iso(f.get("fecha")),
        })

    # ── Tickets OxxoGas ─────────────────────────────────────────────────────
    n = nuevo("tickets")
    for t in (detalles.get("tickets") or [])[:n][:MAX_PENDIENTES_POR_VUELTA]:
        ev = {
            "id": f"tkt:{t['Id']}",
            "nivel": "info",
            "icono": "🎫",
            "titulo": f"Ticket {t['FolioTicket']}",
            "texto": f"{t['MarcaModelo'] or '—'} · {t['Nombre']}"
                     + (f" · {_corta(t['Descripcion'], 50)}" if t.get("Descripcion") else ""),
            "meta": t.get("fecha") or "",
            "ts": _iso(t.get("fecha")),
        }
        # Sin imagen: los tickets se muestran sin foto (2026-09-28).
        eventos.append(ev)

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
            "nivel": "destaque",
            "icono": "✍️",
            "titulo": f"Reporte firmado · {r['Folio']}",
            "texto": f"{r['Cliente']} · {r['Tecnico']}",
            "meta": "firmado por el cliente",
            "ts": _iso(),
            "segundos": 8,
        })

    # ── Cumpleaños de HOY: el destaque del día ──────────────────────────────
    for p in (hoy_cumple or []):
        eventos.append({
            "id": f"cumple:{_dt.date.today().isoformat()}:{p['Nombre']}",
            "nivel": "destaque",
            "icono": "🎂",
            "titulo": f"¡Feliz cumpleaños, {p['Nombre']}!",
            "texto": f"{p.get('edad') or '—'} años hoy",
            "meta": "en ECCSA",
            "ts": _iso(),
            "segundos": 9,
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
