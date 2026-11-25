"""
Pruebas del cableado de `pendientes_snapshot()` (api/datos.py).

NO tocan la base: la conexión se sustituye por un doble. Lo que fijan es el
contrato con el snapshotter:

  · un fallo de la base PROPAGA (no se convierte en ceros falsos), para que
    `_bloque` reúse el bloque anterior y marque el ciclo como degradado;
  · la consulta de totales usa la ventana de temporada que sale de
    `HUB_Config.comprobantes_desde`.
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

# `datos` importa `db` → `config`, que exige credenciales al importarse. Estas
# pruebas no abren conexión, así que basta con que existan para poder importar.
os.environ.setdefault("HUB_DB_USER", "pruebas")
os.environ.setdefault("HUB_DB_PASSWORD", "pruebas")

try:
    import datos
except Exception as _exc:          # sin pymssql / sin entorno: se salta
    datos = None
    _MOTIVO = str(_exc)


class _CursorFalso:
    """Cursor doble: guarda lo que se ejecuta y responde a las tres consultas.

    `_config()` abre el cursor SIN `as_dict` (espera una tupla), así que el doble
    tiene que respetar esa diferencia: si no, la configuración "fallaría" y el
    corte caería al valor por defecto, que es justo lo que no se quiere probar.
    """

    def __init__(self, registro: list, as_dict: bool):
        self.registro = registro
        self.as_dict = as_dict

    def execute(self, sql, params=()):
        self.registro.append((sql, params))

    def fetchone(self):
        sql = self.registro[-1][0]
        if "HUB_Config" in sql:
            return {"Valor": "2026-01-15"} if self.as_dict else ("2026-01-15",)
        if "COUNT(*)" in sql:
            return {"n": 2, "monto": 1500.5}
        return None

    def fetchall(self):
        sql = self.registro[-1][0]
        if "TOP 6" in sql:
            return [
                {"persona": "Alfredo", "placa": "RWS675B", "monto": 500,
                 "dias": 0, "cerrado": 0, "id_usuario": 7},
                {"persona": "Héctor", "placa": "X", "monto": None,
                 "dias": 3, "cerrado": 1, "id_usuario": 2},
            ]
        return []


class _ConexionFalsa:
    def __init__(self):
        self.registro = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, as_dict=False):
        return _CursorFalso(self.registro, as_dict)


class PendientesSnapshotTest(unittest.TestCase):
    def setUp(self):
        if datos is None:
            self.skipTest(f"no se pudo importar api/datos.py: {_MOTIVO}")

    def test_propaga_el_fallo_de_la_base(self):
        """Un fallo NO puede volver como {vales: 0}: es un cero falso."""
        with mock.patch.object(datos, "get_connection",
                               side_effect=RuntimeError("sin base")):
            with self.assertRaises(RuntimeError):
                datos.pendientes_snapshot()

    def test_usa_la_ventana_de_temporada(self):
        con = _ConexionFalsa()
        with mock.patch.object(datos, "get_connection", return_value=con):
            r = datos.pendientes_snapshot()
        sql, params = next((s, p) for s, p in con.registro if "COUNT(*)" in s)
        self.assertIn("FechaSolicitud >= %s", sql)
        self.assertEqual(params, ("2026-01-15",))
        self.assertEqual(r["desde"], "2026-01-15")
        self.assertEqual(r["vales"], 2)
        self.assertEqual(r["monto"], 1500.5)
        self.assertIsNone(r["ultimos"][1]["monto"])
        self.assertTrue(r["ultimos"][1]["cerrado"])


if __name__ == "__main__":
    unittest.main()
