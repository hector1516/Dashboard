"""
Pruebas del ranking del bot de WhatsApp (`api/datos.py::wa_ranking`).

No tocan la base: la conexión se sustituye por un doble. Fijan tres cosas del
contrato:

  · la ventana es de 30 días y solo cuenta lo que ENTRA (`Direccion='IN'`);
  · el Id 1 (la cuenta del bot) se excluye, y un teléfono sin usuario no entra;
  · el resultado se recorta a 10 y se numera por posición, en el orden que
    devuelve la consulta (mensajes descendentes).

Igual que `test_pendientes_bd.py`, un fallo de la base debe propagarse: el
snapshotter reusa la última lectura buena en vez de borrar la tarjeta.
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
except ModuleNotFoundError as _exc:   # solo se salta si falta pymssql
    if _exc.name != "pymssql":
        raise
    datos = None
    _MOTIVO = str(_exc)


class _CursorFalso:
    """Cursor doble: guarda el SQL y devuelve filas ya ordenadas.

    El ORDER BY real lo hace SQL Server; aquí se comprueba que la consulta lo
    pide y que la forma de salida respeta ese orden con `posicion` 1..N.
    """

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


def _filas(n: int) -> list:
    return [{"id_usuario": i, "nombre": f"Persona {i}", "mensajes": 100 - i}
            for i in range(1, n + 1)]


class WaRankingTest(unittest.TestCase):
    def setUp(self):
        if datos is None:
            self.skipTest(f"no se pudo importar api/datos.py: {_MOTIVO}")

    def test_consulta_la_ventana_y_excluye_al_bot(self):
        con = _ConexionFalsa(_filas(3))
        with mock.patch.object(datos, "get_connection", return_value=con):
            datos.wa_ranking()
        sql = con.registro[-1][0]
        self.assertIn("HUB_WhatsappEntrante", sql)
        self.assertIn("HUB_UsuariosWhatsapp", sql)
        self.assertIn("HUB_Users", sql)
        self.assertIn("Direccion = 'IN'", sql)
        self.assertIn("DATEADD(day, -30", sql)
        self.assertIn("w.IdUsuario <> 1", sql)
        # Un mensaje de un número sin usuario no puede entrar: el CROSS APPLY
        # solo produce fila cuando encuentra el teléfono en la plantilla.
        self.assertIn("CROSS APPLY", sql)
        self.assertIn("ORDER BY mensajes DESC", sql)
        self.assertIn("TOP 10", sql)

    def test_devuelve_top_10_numerado_en_orden(self):
        con = _ConexionFalsa(_filas(12))
        with mock.patch.object(datos, "get_connection", return_value=con):
            r = datos.wa_ranking()
        self.assertTrue(r["generado"])
        self.assertEqual(len(r["items"]), 10)
        self.assertEqual(r["items"][0], {
            "posicion": 1, "nombre": "Persona 1", "mensajes": 99})
        self.assertEqual(r["items"][9]["posicion"], 10)
        self.assertEqual([i["posicion"] for i in r["items"]], list(range(1, 11)))

    def test_un_fallo_de_la_base_se_propaga(self):
        """No se convierte en lista vacía: el snapshotter conserva lo anterior."""
        with mock.patch.object(datos, "get_connection",
                               side_effect=RuntimeError("sin base")):
            with self.assertRaises(RuntimeError):
                datos.wa_ranking()


if __name__ == "__main__":
    unittest.main()
