"""
api/panel.py — control remoto de la pantalla de la oficina.

Quién manda sobre la TV: el módulo Notas de Admon (u otra app interna). Cómo:
escribe un comando aquí, la TV lo ve en su siguiente poll y lo obedece. No hay
conexión directa entre las dos apps: nadie le empuja nada a nadie.

Por qué un archivo y no una base de datos o una cola: el comando es de UN
comando ("muéstrame la pantalla de legends"), dura medio minuto de interés y
después es basura. Un JSON de 200 bytes en el volumen es más simple que una
tabla que limpiar, y si la TV está apagada el comando se queda ahí esperándola
(que es justo lo que uno quiere: "deja la pantalla en Metricas" y cuando
prenden la TV, es Metricas).

El token: escribir es mandar sobre la pantalla de todos en la oficina, así que
`/api/panel/comando` exige el secreto compartido (env HUB_PANEL_TOKEN). Leer
el estado NO lo exige: la TV lo consulta cada 3 s sin secreto, y lo que se ve
(no, está la TV y sí, se va en 20 s) no sirve para mandar nada.

Si HUB_PANEL_TOKEN no está puesto, escribir devuelve 403. Se prefiere que
nadie pueda mover la pantalla sin querer a que quede abierto "por si acaso".
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import config as C

# Acciones que se aceptan. Fijar la lista aquí (y no validarla en el endpoint)
# hace imposible que un typo desde Admon llegue a hacer otra cosa.
ACCIONES = ("ver", "avanzar", "pausa", "seguir", "salida")

# Techo de tamaño para el JSON del panel: si algún día se escribiera algo raro,
# el archivo no puede crecer sin control en el volumen.
MAX_BYTES = 8 * 1024


class ErrorPanel(Exception):
    """Error con mensaje apto para devolverle tal cual al cliente."""

    def __init__(self, mensaje: str, status: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _ruta() -> Path:
    return Path(C.PANEL)


def token_configurado() -> str:
    """
    El secreto compartido. Sale de la variable de entorno que genera el
    entrypoint del contenedor (ver AGENTS.md §Credenciales); no se guarda en
    ningún archivo porque no hace falta volver a leerlo después.
    """
    return (os.environ.get("HUB_PANEL_TOKEN") or "").strip()


def exigir_token(cabecera: str | None) -> None:
    esperado = token_configurado()
    if not esperado:
        raise ErrorPanel(
            "El panel remoto está deshabilitado: falta HUB_PANEL_TOKEN en el "
            "contenedor del kiosco.", 403,
        )
    if (cabecera or "").strip() != esperado:
        raise ErrorPanel("Token del panel incorrecto.", 403)


def _leer() -> dict:
    try:
        with open(_ruta(), encoding="utf-8") as fh:
            datos = json.load(fh)
    except Exception:
        return {}
    return datos if isinstance(datos, dict) else {}


def _escribir(datos: dict) -> None:
    tmp = _ruta().with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False)
    # replace y no rename directo: en Windows/host con SMB el rename sobre un
    # archivo abierto por otro proceso falla, y el replace atómico no.
    os.replace(tmp, _ruta())


def estado() -> dict:
    """Lo que lee la TV. Sin token."""
    datos = _leer()
    return {
        "comando": datos.get("comando"),
        "pantallas": _leer_pantallas(),
        "tv_conectada": _tv_conectada(),
    }


def _leer_pantallas() -> list:
    try:
        with open(C.PANEL_PANTALLAS, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def _tv_conectada() -> bool:
    """
    Si la TV se announced hace poco. La TV escribe su latido al arrancar; si
    hace más de 2 min no está, y Admon avisa en vez de mandar comandos al
    vacío.
    """
    datos = _leer()
    ultimo = float(datos.get("latido") or 0)
    return (time.time() - ultimo) < 120


def latido() -> dict:
    """Lo llama la TV al arrancar y cada minuto."""
    datos = _leer()
    datos["latido"] = time.time()
    _escribir(datos)
    return {"ok": True, "hora": time.strftime("%Y-%m-%d %H:%M:%S")}


def publicar_pantallas(lista: list) -> dict:
    """
    La TV publica su lista de pantallas al arrancar, para que Admon pueda
    dibujar los botones sin duplicar la lista en dos repos. Sin token: sólo
    informa de lo que ya se ve en pantalla.
    """
    limpio = [
        {"id": str(p.get("id", ""))[:40], "label": str(p.get("label", ""))[:60],
         "icono": str(p.get("icono", ""))[:8]}
        for p in (lista or [])
        if p.get("id")
    ]
    with open(C.PANEL_PANTALLAS, "w", encoding="utf-8") as fh:
        json.dump(limpio[:40], fh, ensure_ascii=False)
    return {"ok": True, "pantallas": len(limpio)}


def mandar(accion: str, pantalla: str | None = None) -> dict:
    """Valida y encola un comando. Lanza ErrorPanel si algo no cuadra."""
    accion = (accion or "").strip()
    if accion not in ACCIONES:
        raise ErrorPanel(f"Acción no válida: {accion!r}. Opciones: {', '.join(ACCIONES)}.")
    if accion == "ver" and not (pantalla or "").strip():
        raise ErrorPanel("La acción 'ver' necesita la pantalla a mostrar.")

    datos = _leer()
    comando = {
        "id": int(datos.get("ultimo_id") or 0) + 1,
        "accion": accion,
        "pantalla": (pantalla or "").strip() or None,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    datos["comando"] = comando
    datos["ultimo_id"] = comando["id"]
    _escribir(datos)
    return comando


def confirmar(id_comando: int) -> dict:
    """La TV dice 'ya lo hice'. Sirve para que Admon vea que fue obeyedecido."""
    datos = _leer()
    c = datos.get("comando") or {}
    if int(c.get("id") or 0) != int(id_comando or -1):
        return {"ok": False, "motivo": "ese comando no es el pendiente"}
    datos["confirmado"] = {
        "id": c.get("id"), "ts": c.get("ts"),
        "hecho": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _escribir(datos)
    return {"ok": True, "confirmado": datos["confirmado"]}
