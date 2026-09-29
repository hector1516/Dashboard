"""
main.py — la API mínima del kiosco.

Deliberadamente CHICA. El frontend es una pantalla que no escribe nada: todo lo
que necesita son cuatro GETs, y lo demás lo sirve nginx desde el volumen.

  GET /api/dashboard/snapshot   → el snapshot que calcula worker/snapshotter.py
  GET /api/dashboard/version    → build de la imagen (para recargar la pantalla)
  GET /api/shell/state          → contrato del ECCSA-Shell (SIN sesión)
  GET /healthz                  → salud: ok | degradado + qué falta

Y el panel remoto, que es lo ÚNICO que escribe (ver panel.py):
  GET  /api/panel/estado        → el comando pendiente (sin token: lo lee la TV)
  POST /api/panel/comando       → encola "muéstrame X" (exige HUB_PANEL_TOKEN)
  POST /api/panel/confirmado    → la TV dice "ya lo hice"
  POST /api/panel/latido        → la TV dice "sigo aquí"
  POST /api/panel/pantallas     → la TV publica su lista de pantallas

Sobre `/api/shell/state`: el contrato del shell dice que las apps lo exponen
porque el banner lo usa para el lugar y las versiones. El kiosco no monta ese
banner (no hay ni usuario ni cola de sincronización), pero la app cumple el
contrato igual y además le sirve a `check_daily.py` del shell. Es el único
endpoint sin `require_user` del ecosistema, y es correcto: solo devuelve
versiones, lugar y salud. Ver ECCSA-Shell/docs/CONTRATO.md §2b.
"""
import json
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import config as C
import panel as P
from lugar import lugar_de

app = FastAPI(title="Dashboard ECCSA", version="1.0.0")

_cache = {"datos": None, "ts": 0.0}
_CACHE_TTL = 5.0        # segundos: el snapshot cambia cada 2 min


def _leer_snapshot() -> dict:
    """Del disco, con 5 s de cache en memoria (varias requests a la vez)."""
    ahora = time.time()
    if _cache["datos"] is not None and ahora - _cache["ts"] < _CACHE_TTL:
        return _cache["datos"]
    try:
        with open(C.SNAPSHOT, encoding="utf-8") as fh:
            datos = json.load(fh)
        _cache.update(datos=datos, ts=ahora)
        return datos
    except Exception:
        return _cache["datos"] or {}


def _sin_datos() -> dict:
    """Lo que se ve si el snapshotter todavía no ha corrido nunca."""
    return {
        "schema_version": C.SCHEMA_VERSION,
        "generado_en": None,
        "degradado": ["sin-datos"],
        "origen": "cache",
        "build": C.leer_build(),
        "reportes": {"total": 0, "firmados": 0, "pendientes": 0, "hoy": 0,
                     "esta_semana": 0, "por_ingeniero": [], "ultimos": []},
        "kilometros": {"total_semana": 0, "hoy": 0, "por_vehiculo": [], "serie_7dias": []},
        "tickets": {"total_semana": 0, "ultimos": [], "por_vehiculo": []},
        "legends": {"ranking": [], "ganador_semana": None, "total_puntos": 0,
                    "reset_en_segundos": 0},
        "fotos": {"ids": [], "rutas": []},
        "notas": [],
        "cumpleanos": {"hoy": [], "del_mes": []},
        "aniversarios": {"hoy": [], "del_mes": []},
        "metricas": {"top_cliente": None, "top_ingeniero": None, "pulso": [],
                     "actividad_hora": 0, "ultimo_evento": None, "top_del_dia": None},
        "clima": {"actual": {"temperatura": None, "humedad": None, "viento": None,
                             "codigo_clima": 0, "descripcion": "Sin datos",
                             "icono": "❓", "es_dia": True},
                  "hoy": {"max": None, "min": None, "prob_lluvia": None},
                  "manana": {"max": None, "min": None, "prob_lluvia": None},
                  "leido_en": None},
        "asistencia": {"personas": [], "total": 0, "dentro": 0, "salieron": 0},
        "imagen": {"hay": False},
        "fondos": [],
        "eventos": [],
    }


def _salud() -> dict:
    try:
        with open(C.SALUD, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {"ok": False, "degradado": ["sin-datos"], "generado_en": None}


@app.get("/api/dashboard/snapshot")
def snapshot():
    """
    El snapshot completo. `no-store` a propósito: la pantalla lo pide cada 30 s
    y con caché de navegador mostraría datos viejos sin avisar.
    """
    datos = _leer_snapshot() or _sin_datos()
    return JSONResponse(datos, headers={
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "X-Kiosko-Degradado": ",".join(datos.get("degradado") or []),
    })


@app.get("/api/dashboard/version")
def version():
    """
    Build de la imagen. La pantalla lo consulta cada minuto y se recarga sola si
    cambió: sin esto, un hotsync no se vería hasta que alguien reiniciara Edge
    a mano (que en un kiosco puede tardar días).
    """
    return JSONResponse({"build": C.leer_build()}, headers={"Cache-Control": "no-store"})


@app.get("/api/shell/state")
def shell_state(request: Request):
    """
    Contrato del ECCSA-Shell, SIN sesión (esta es una pantalla, no una app con
    usuarios). Lo que sí refleja de verdad es la SALUD del refresco de datos: en
    una pantalla sin nadie mirando, ese es el dato que evita que se lean ceros
    viejos como si fueran de hoy.
    """
    salud = _salud()
    modo, ip = lugar_de(request.headers, request.client.host if request.client else "")
    estado = "idle" if salud.get("ok") else "error"
    return {
        "app": {"id": "dashboard", "nombre": "Centro de Operaciones", "version": _app_version()},
        "shell": {"version": _shell_version()},
        "user": None,        # sin sesión: el banner omite el bloque .who
        "sync": {
            "estado": estado,
            "pendientes": 0,
            "ultimo": salud.get("generado_en"),
        },
        "lugar": {"modo": modo, "ip": ip},
    }


@app.get("/healthz")
def healthz():
    salud = _salud()
    ok = bool(salud.get("ok"))
    return JSONResponse(
        {
            "status": "ok" if ok else "degradado",
            "generado_en": salud.get("generado_en"),
            "degradado": salud.get("degradado", []),
            "revisado": salud.get("revisado"),
            "build": C.leer_build(),
        },
        status_code=200 if ok else 503,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/")
def raiz():
    return {
        "app": "Dashboard ECCSA · Centro de Operaciones",
        "pantalla": "/ (esta misma)",
        "api": ["/api/dashboard/snapshot", "/api/dashboard/version",
                "/api/shell/state", "/healthz"],
        "build": C.leer_build(),
    }


def _app_version() -> str:
    """La versión la manda package.json → src/lib/shell.js (la estampa el shell)."""
    try:
        ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "package.json")
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh).get("version", "?")
    except Exception:
        return "?"


def _shell_version() -> str:
    try:
        ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ECCSA_SHELL_VERSION")
        with open(ruta, encoding="utf-8") as fh:
            return fh.read().strip() or "?"
    except Exception:
        return "?"


# ── Panel remoto de la pantalla ─────────────────────────────────────────────
# Lo escribe Admon (módulo Notas) y lo obedece la TV. Ver panel.py para el
# porqué de que leer no exija token y escribir sí.
@app.get("/api/panel/estado")
def panel_estado():
    """Sin token: lo consulta la propia TV cada 3 s."""
    return JSONResponse(P.estado())


@app.post("/api/panel/comando")
async def panel_comando(request: Request):
    """
    Encola un comando para la pantalla. Requiere el secreto compartido en la
    cabecera `X-Panel-Token` (env HUB_PANEL_TOKEN en el contenedor).
    """
    try:
        P.exigir_token(request.headers.get("X-Panel-Token"))
        cuerpo = await _cuerpo(request)
        comando = P.mandar(cuerpo.get("accion", ""), cuerpo.get("pantalla"))
        return JSONResponse({"ok": True, "comando": comando})
    except P.ErrorPanel as exc:
        return JSONResponse({"ok": False, "error": exc.mensaje}, status_code=exc.status)


@app.post("/api/panel/confirmado")
async def panel_confirmado(request: Request):
    try:
        cuerpo = await _cuerpo(request)
        return JSONResponse(P.confirmar(cuerpo.get("id", 0)))
    except P.ErrorPanel as exc:
        return JSONResponse({"ok": False, "error": exc.mensaje}, status_code=exc.status)


@app.post("/api/panel/latido")
def panel_latido():
    """La TV avisa que está viva. Sin token: no se puede mandar nada con esto."""
    return JSONResponse(P.latido())


@app.post("/api/panel/pantallas")
async def panel_pantallas(request: Request):
    """
    La TV publica su lista de pantallas al arrancar, para que Admon dibuje los
    botones sin tener la lista duplicada en dos repos.
    """
    try:
        cuerpo = await _cuerpo(request)
        return JSONResponse(P.publicar_pantallas(cuerpo.get("pantallas", [])))
    except P.ErrorPanel as exc:
        return JSONResponse({"ok": False, "error": exc.mensaje}, status_code=exc.status)


async def _cuerpo(request: Request) -> dict:
    """El JSON del POST, o {} si no viene o no es objeto. Nunca revienta."""
    try:
        datos = await request.json()
    except Exception:
        return {}
    return datos if isinstance(datos, dict) else {}
