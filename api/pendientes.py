"""Cálculo puro del bloque `pendientes` (sin base de datos)."""

from datetime import date

DESDE_POR_DEFECTO = "2026-11-23"


def corte_temporada(valor: str | None) -> str:
    """Fecha ISO del corte. Un valor ausente o inválido cae al de por defecto."""
    try:
        return date.fromisoformat(str(valor).strip()[:10]).isoformat()
    except (TypeError, ValueError):
        return DESDE_POR_DEFECTO


def armar_pendientes(totales: dict, ultimos: list[dict], desde: str) -> dict:
    """Forma del bloque. `monto` NULL se queda None: no es cero.

    El `SUM` de la consulta usa `CASE WHEN MontoEmitido IS NOT NULL` (sin el
    `ELSE 0`): si ningún vale emitido tiene monto, SQL devuelve NULL y aquí se
    conserva como None para que el ancla diga «sin monto» en vez de «$0».
    """
    monto = (totales or {}).get("monto")
    return {
        "vales": int((totales or {}).get("n") or 0),
        "monto": (float(monto) if monto is not None else None),
        "desde": desde,
        "ultimos": [
            {
                "nombre": (f.get("persona") or "—").strip(),
                "placa": (f.get("placa") or "").strip(),
                "monto": (float(f["monto"]) if f.get("monto") is not None else None),
                "dias": int(f.get("dias") or 0),
                "cerrado": bool(f.get("cerrado")),
                "id_usuario": f.get("id_usuario"),
            }
            for f in (ultimos or [])
        ],
    }
