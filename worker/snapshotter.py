#!/usr/bin/env python3
"""
snapshotter.py — el proceso que mantiene vivo al kiosco.

Un loop, cuatro pasos, y la regla que define todo el proceso:

    SI ALGO FALLA, NO SE BORRA NADA.

Es decir: si la base no responde, el snapshot viejo sigue en disco y la
pantalla lo muestra diciendo "datos de hace 40 min". Antes (en el dashboard de
Field) una caída de red se veía como una pantalla con ceros, que es peor que
una pantalla con información vieja: en un tablero de la oficina, un cero falso
se interpreta como "no trabaja nadie".

Ciclo (cada `INTERVALO_SNAPSHOT`, 2 min por omisión):
  1. clima        → Open-Meteo (con respaldo del último dato guardado)
  2. fondos       → 1 wallpaper nuevo de Bing, reescalado a Full HD y local
  3. medios       → thumbs de fotos/tickets + avatares
  4. datos        → SQL Server: los 9 bloques + cursores de eventos
  5. snapshot     → /data/snapshot.json (escritura atómica)

Los deltas de las tablas vivas se convierten en avisos en /data/eventos.json.

Se corre como proceso supervisor `snapshotter` dentro del contenedor; también
se puede lanzar a mano para probar:

    HUB_DB_PASSWORD=... python worker/snapshotter.py --una-vez
"""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))

import config as C          # noqa: E402
import datos as D           # noqa: E402
import eventos as E         # noqa: E402
import medios as M          # noqa: E402


def _log(msg: str) -> None:
    linea = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(linea, flush=True)
    try:
        C.asegurar_directorios()
        with open(C.LOG_SINCRONO, "a", encoding="utf-8") as fh:
            fh.write(linea + "\n")
    except Exception:
        pass


def _leer_json(ruta: str, defecto):
    try:
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return defecto


def _escribir_json(ruta: str, obj) -> None:
    """Atómico: nginx (o la API) nunca leen un snapshot a medio escribir."""
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, default=str)
    os.replace(tmp, ruta)


def _fusionar_eventos(eventos_nuevos: list) -> list:
    """Acumula en eventos.json, sin repetir ids y sin crecer sin límite."""
    previos = _leer_json(C.EVENTOS, [])
    ids_previos = {e.get("id") for e in previos}
    todos = [e for e in eventos_nuevos if e.get("id") not in ids_previos] + previos
    return todos[:C.MAX_EVENTOS]


def _firmar_avatares(avs: dict) -> dict:
    """{IdUsuario: '/media/avatars/u<Id>.jpg'} solo para los que se escribieron."""
    rutas = {}
    for id_usuario in (avs or {}):
        if os.path.isfile(os.path.join(C.AVATARS_DIR, f"u{id_usuario}.jpg")):
            rutas[id_usuario] = f"/media/avatars/u{id_usuario}.jpg"
    return rutas


def _con_avatares(personas: list, rutas: dict) -> list:
    """Pega la ruta del avatar a cada persona (por nombre → id del snapshot)."""
    for p in personas or []:
        r = rutas.get(p.get("id_usuario"))
        p["avatar"] = r
        p.pop("id_usuario", None)
    return personas


def ciclo() -> dict:
    """Un vuelta completa. Devuelve el snapshot (para el log y las pruebas)."""
    C.asegurar_directorios()
    degradado = []

    # 1) Clima -------------------------------------------------------------
    clima, clima_ok = M.leer_clima()
    if not clima_ok:
        degradado.append("clima")

    # 2) Fondos ------------------------------------------------------------
    fondos, fondos_ok = M.actualizar_fondos()
    if not fondos_ok:
        degradado.append("bing")

    # 3) Datos de la base --------------------------------------------------
    try:
        import datetime as _dt
        hoy = _dt.date.today()
        sunday = D.domingo_de_hoy(hoy).isoformat()
        hoy_s = hoy.isoformat()

        bloques = {
            "reportes": D.reportes(sunday, hoy_s),
            "kilometros": D.kilometros(sunday, hoy_s),
            "tickets": D.tickets(sunday),
            "legends": D.legends(),
            "notas": D.notas(),
            "celebraciones": D.celebraciones(),
            "metricas": D.metricas(sunday),
            "asistencia": D.asistencia_hoy(),
        }
    except Exception as exc:
        # La base no responde: se conserva el snapshot anterior.
        _log(f"ERROR bd: {exc} · se conserva el snapshot anterior")
        salud = _leer_json(C.SALUD, {})
        salud.update({
            "degradado": sorted(set(salud.get("degradado", []) + ["bd"])),
            "ultimo_error": str(exc)[:300],
            "revisado": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ok": False,
        })
        _escribir_json(C.SALUD, salud)
        return _leer_json(C.SNAPSHOT, {})

    # 4) Medios ------------------------------------------------------------
    fotos = D.fotos(C.FOTOS_CARRUSEL)
    thumbs_fotos, fotos_ok = M.thumbs_de_fotos(fotos["ids"])
    # Los tickets van SIN foto (2026-09-28): no se generan sus thumbs. Antes sí,
    # y además había que rescatarlos de los 15 bytes basura con los que vienen
    # algunos blobs de ImagenTicket: trabajo de CPU y disco para nada.
    try:
        M.guardar_avatares(D.avatares())
    except Exception as exc:
        _log(f"WARN avatares: {exc}")
    if not fotos_ok:
        degradado.append("media")

    rutas_avatar = _firmar_avatares(D.avatares())

    # Avatares: en el ranking de Legends y en TODOS los cumpleaños/aniversarios
    # (los de hoy y los del mes). Antes sólo se pegaban a los de hoy y las
    # tarjetas del mes salían con la inicial, que a 3 metros no dice nada.
    bloques["legends"]["ranking"] = _con_avatares(bloques["legends"]["ranking"], rutas_avatar)
    # En asistencia NO se usa `_con_avatares` porque ése borra `id_usuario` y
    # el front lo necesita como key de la lista.
    for _p in bloques["asistencia"]["personas"]:
        _p["avatar"] = rutas_avatar.get(_p.get("id_usuario"))
    for clave in ("cumpleanos", "aniversarios"):
        for grupo in ("hoy", "del_mes"):
            bloques["celebraciones"][clave][grupo] = _con_avatares(
                bloques["celebraciones"][clave][grupo], rutas_avatar)

    # 5) Eventos (deltas contra state.json) ---------------------------------
    state = _leer_json(C.STATE, {})
    cursores_previos = state.get("cursores", {})
    try:
        cursores = D.cursores_para_eventos()
    except Exception as exc:
        cursores = {}
        degradado.append("cursores")
        _log(f"WARN cursores: {exc}")

    # Cooldown de presencia: se lee del state y se actualiza en el mismo
    # `detectar` (muta el dict que se le pasa), para no reprocesar en RAM.
    presencia_previa = state.get("presencia_vistos") or {}

    # Un solo shape para las dos funciones: {tabla: id} con el cursor previo.
    _prev_ids = {t: cursores_previos.get(t, {}).get("id", 0)
                 for t in ("km", "tickets", "reportes", "firmados", "avisos", "presencia")}

    nuevos = E.detectar(
        cursores,
        # OJO: a las dos funciones se les pasa el MISMO shape, {tabla: id} con
        # el cursor PREVIO (el Id desde el que hay que leer), no la diferencia.
        # `eventos.detectar` es quien recorta a los nuevos.
        _prev_ids,
        D.detalles_de(_prev_ids) if cursores else {},
        bloques["celebraciones"]["cumpleanos"]["hoy"],
        presencia_previa,
    )

    # Sin movimiento por mucho tiempo → un aviso informativo, no un error.
    if not nuevos:
        sil = E.sin_actividad(state.get("ultimo_evento"))
        if sil:
            nuevos = [sil]
    if nuevos:
        _escribir_json(C.EVENTOS, _fusionar_eventos(nuevos))
        _log(f"eventos nuevos: {len(nuevos)} → {', '.join(e['id'] for e in nuevos[:4])}")

    # Estado (cursores) — se avanza aunque no haya red, para no repetir avisos.
    if cursores:
        # `presencia_vistos` guarda "IdUsuario:TIPO" → última hora anunciada, y
        # se poda para que el state.json no crezca sin límite.
        vistos = {k: v for k, v in presencia_previa.items()
                  if v >= time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 7200))}
        state = {
            "cursores": cursores,
            "ultimo_evento": nuevos[0]["ts"] if nuevos else state.get("ultimo_evento"),
            "ranking_legends": [r["nombre"] for r in bloques["legends"]["ranking"]],
            "presencia_vistos": vistos,
            "actualizado": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _escribir_json(C.STATE, state)

    # 6) Armar el snapshot --------------------------------------------------
    legends = dict(bloques["legends"])
    # `puesto_anterior` para las flechas: contra el ranking guardado.
    antes = state.get("ranking_legends") or []
    ranking = legends.get("ranking") or []
    if antes and len(antes) == len(ranking):
        for i, r in enumerate(ranking):
            prev = antes.index(r["nombre"]) + 1 if r["nombre"] in antes else None
            r["puesto_anterior"] = prev if prev != i + 1 else None
    else:
        for r in ranking:
            r["puesto_anterior"] = None
    legends["ranking"] = ranking

    snapshot = {
        "schema_version": C.SCHEMA_VERSION,
        "generado_en": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "degradado": sorted(set(degradado)),
        "origen": "bd",
        "build": C.leer_build(),
        "reportes": bloques["reportes"],
        "kilometros": bloques["kilometros"],
        "tickets": bloques["tickets"],
        "legends": legends,
        "fotos": {"ids": fotos["ids"], "rutas": thumbs_fotos},
        "notas": bloques["notas"],
        "cumpleanos": bloques["celebraciones"]["cumpleanos"],
        "aniversarios": bloques["celebraciones"]["aniversarios"],
        "metricas": bloques["metricas"],
        "asistencia": bloques["asistencia"],
        "clima": clima,
        "fondos": fondos,
        # Anchos de los thumbs ya generados. El front los lee de acá en vez de
        # tener el número magical duplicado: pedir 1280 cuando el backend
        # genera 960 es un 404 y se ve una foto negra a pantalla completa.
        "media": {"fotos_w": C.THUMB_FOTOS_ANCHO},
        "eventos": _leer_json(C.EVENTOS, []),
    }
    _escribir_json(C.SNAPSHOT, snapshot)
    _escribir_json(C.SALUD, {
        "ok": not degradado,
        "degradado": sorted(set(degradado)),
        "generado_en": snapshot["generado_en"],
        "revisado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ultimo_error": "",
    })
    return snapshot


def main() -> int:
    una_vez = "--una-vez" in sys.argv
    C.asegurar_directorios()
    _log(f"snapshotter arrancado · datos en {C.DATA_DIR} · build {C.leer_build()}")
    while True:
        try:
            snap = ciclo()
            if snap:
                _log(
                    f"snapshot ok · {snap['reportes']['esta_semana']} reportes/semana · "
                    f"{snap['kilometros']['total_semana']} km · "
                    f"{len(snap['fondos'])} fondos · degradado={snap['degradado'] or 'nada'}"
                )
        except Exception:
            _log("ERROR ciclo:\n" + traceback.format_exc())
        if una_vez:
            return 0
        # Espera por trozos, con el plazo recalculado en cada vuelta.
        #
        # OJO: el plazo usa `time.monotonic()`, NO `time.time()`. El host es
        # Windows y ajusta el reloj (NTP, cambio de hora); con el reloj de pared
        # un salto hacia atrás dejaba al proceso durmiendo el delta entero
        # (se quedó 20 min sin refrescar una vez) y la pantalla se congelaba con
        # datos viejos sin avisar. Monotónico no se mueve por ajustes de reloj.
        siguiente = time.monotonic() + C.INTERVALO_SNAPSHOT
        while True:
            faltan = siguiente - time.monotonic()
            if faltan <= 0:
                break
            time.sleep(min(C.SEGUNDOS_ESPERA, faltan))


if __name__ == "__main__":
    sys.exit(main())
