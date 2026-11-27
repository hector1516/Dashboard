"""
Pruebas del resumen de uso servido desde el snapshot y de los mensajes de Volt.

Dos contratos que costaron una pantalla en blanco (2026-11-27):

  · `/api/uso/resumen` NO puede calcular en la petición. La consulta agrega 32
    mil filas y tardaba 30-80 s: nginx respondía 504 y «Uso de Apps» se quedaba
    sin datos. Ahora solo lee `snapshot.uso` (lo calcula el snapshotter) y, si
    todavía no hay lectura, devuelve la forma con `degradado: true` —nunca un
    cero fingido ni un 504—. Las claves del contrato no cambian.

  · `volt_mensajes` filtra `Direccion='OUT'` y devuelve SOLO el texto, tal como
    se envió: sin destinatario, teléfono, chat ni fecha. Máximo 5 y 30 días.

No abren base de datos ni escriben en `/data`: la conexión es un doble.
"""
import json
import os
import sys
import time
import unittest
from unittest import mock

_AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_AQUI, "..", "api"))

# `datos` importa `db` → `config`, que exige credenciales al importarse.
os.environ.setdefault("HUB_DB_USER", "pruebas")
os.environ.setdefault("HUB_DB_PASSWORD", "pruebas")

try:
    import datos
    import main
except ModuleNotFoundError as _exc:   # solo se salta si falta pymssql
    if _exc.name != "pymssql":
        raise
    datos = None
    main = None
    _MOTIVO = str(_exc)


CLAVES_USO = ("activos_7d", "total_7d", "por_app", "por_dia", "por_hora",
              "por_dia_semana", "top_endpoints", "top_usuarios", "inactivos")


def _uso_de_ejemplo() -> dict:
    return {
        "activos_7d": 7,
        "total_7d": 1234,
        "por_app": {"admon": 1000, "field": 234},
        "por_dia": [{"dia": "2026-11-26", "llamadas": 300, "usuarios": 5}],
        "por_hora": [{"hora": 9, "llamadas": 120}],
        "por_dia_semana": [{"dia": "jueves", "llamadas": 400}],
        "top_endpoints": [{"endpoint": "/api/x", "usos": 90}],
        "top_usuarios": [{"usuario": "Ana", "id": "3", "llamadas": 40}],
        "inactivos": ["Luis"],
    }


class UsoDesdeSnapshotTest(unittest.TestCase):
    def setUp(self):
        if main is None:
            self.skipTest(f"no se pudo importar la API: {_MOTIVO}")

    def test_sin_caché_responde_vacio_y_degradado(self):
        """Primer arranque: forma completa con null, nunca 500 ni 504."""
        with mock.patch.object(main, "_leer_snapshot", return_value={}):
            r = main.uso_resumen()
        cuerpo = json.loads(r.body)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(cuerpo["degradado"])
        for clave in CLAVES_USO:
            self.assertIn(clave, cuerpo)
            self.assertIsNone(cuerpo[clave])

    def test_con_caché_responde_rapido_y_no_toca_la_base(self):
        """Lee el snapshot (milisegundos); la consulta la hace el snapshotter."""
        uso = _uso_de_ejemplo()
        snap = {"uso": uso, "generado_en": "2026-11-27T08:00:00"}
        with mock.patch.object(main, "_leer_snapshot", return_value=snap), \
             mock.patch.object(datos, "get_connection",
                               side_effect=AssertionError("no debe tocar la BD")):
            t0 = time.perf_counter()
            r = main.uso_resumen()
            segundos = time.perf_counter() - t0
        self.assertLess(segundos, 2.0)
        cuerpo = json.loads(r.body)
        self.assertFalse(cuerpo["degradado"])
        self.assertEqual(cuerpo["generado_en"], "2026-11-27T08:00:00")
        # Mismo contrato: los datos del snapshot intactos.
        for clave in CLAVES_USO:
            self.assertEqual(cuerpo[clave], uso[clave])


class _CursorFalso:
    def __init__(self, registro: list, filas: list):
        self.registro = registro
        self.filas = filas

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=()):
        self.registro.append((sql, params))

    def fetchall(self):
        return list(self.filas)


class _ConexionFalsa:
    def __init__(self, filas: list):
        self.registro = []
        self.filas = filas

    def cursor(self, as_dict=False):
        return _CursorFalso(self.registro, self.filas)

    def close(self):
        pass


class VoltMensajesTest(unittest.TestCase):
    def setUp(self):
        if datos is None:
            self.skipTest(f"no se pudo importar api/datos.py: {_MOTIVO}")

    def test_consulta_solo_los_enviados_de_30_dias(self):
        con = _ConexionFalsa([{"Texto": "Acepto la queja, pero con estilo."}])
        with mock.patch.object(datos, "get_connection", return_value=con):
            datos.volt_mensajes()
        sql = con.registro[-1][0]
        self.assertIn("HUB_WhatsappEntrante", sql)
        self.assertIn("Direccion = 'OUT'", sql)
        self.assertIn("DATEADD(day, -30", sql)
        self.assertIn("TOP 5", sql)
        self.assertIn("ORDER BY Fecha DESC", sql)
        self.assertIn("LIKE '%Acepto la queja%'", sql)
        self.assertIn("LIKE '%Por qué:%'", sql)
        self.assertIn("LIKE '%El tráfico ya te conoce%'", sql)

    def test_solo_devuelve_texto_y_maximo_cinco(self):
        """Ni nombre, ni teléfono, ni chat, ni fecha: solo la frase."""
        filas = [{
            "Texto": f"Roast {i}",
            "Nombre": "Destinatario",
            "Telefono": "5550000000",
            "Chat": "chat-1",
            "Fecha": "2026-11-27",
        } for i in range(9)]
        con = _ConexionFalsa(filas)
        with mock.patch.object(datos, "get_connection", return_value=con):
            r = datos.volt_mensajes()
        self.assertEqual(r, ["Roast 0", "Roast 1", "Roast 2", "Roast 3", "Roast 4"])
        self.assertTrue(all(isinstance(m, str) for m in r))

    def test_sin_filas_devuelve_lista_vacia(self):
        con = _ConexionFalsa([])
        with mock.patch.object(datos, "get_connection", return_value=con):
            self.assertEqual(datos.volt_mensajes(), [])


if __name__ == "__main__":
    unittest.main()
