"""
Pruebas de los estados «no sé»: nunca un cero fingido.

`pendientes` es OPCIONAL en el snapshot. Si los respaldos lo publicaran con
ceros (`{vales: 0, monto: 0, ...}`), `Comprobantes` concluiría «Todo al día» sin
saber nada y el chip diría «0 sin foto». Estas pruebas fijan que:

  · `_sin_datos()` (api/main.py) NO incluye `pendientes`;
  · el fallback del snapshotter devuelve el bloque anterior tal cual (puede ser
    `None`) y no fabrica `{vales: 0, monto: 0, ...}`.

No abren base de datos ni escriben en `/data`.
"""
import os
import sys
import unittest
from unittest import mock

_AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_AQUI, "..", "api"))
sys.path.insert(0, os.path.join(_AQUI, "..", "worker"))

# `datos` importa `db` → `config`, que exige credenciales al importarse.
os.environ.setdefault("HUB_DB_USER", "pruebas")
os.environ.setdefault("HUB_DB_PASSWORD", "pruebas")

try:
    import main            # noqa: E402
    import snapshotter     # noqa: E402
except ModuleNotFoundError as _exc:   # solo se salta si falta pymssql
    if _exc.name != "pymssql":
        raise
    main = None
    snapshotter = None
    _MOTIVO = str(_exc)


class SinDatosTest(unittest.TestCase):
    def setUp(self):
        if main is None:
            self.skipTest(f"no se pudo importar la API: {_MOTIVO}")

    def test_sin_datos_no_trae_pendientes(self):
        """Un bloque con ceros haría decir «Todo al día» sin saber nada."""
        self.assertNotIn("pendientes", main._sin_datos())


class FallbackPendientesTest(unittest.TestCase):
    def setUp(self):
        if snapshotter is None:
            self.skipTest(f"no se pudo importar el snapshotter: {_MOTIVO}")

    def _bloque_que_falla(self, previo):
        def falla():
            raise RuntimeError("sin base")

        with mock.patch.object(snapshotter, "_log"):
            return snapshotter._bloque(falla, previo)

    def test_sin_previo_el_fallback_es_none(self):
        """Primer ciclo tras un deploy: no hay bloque y no se inventa."""
        self.assertIsNone(self._bloque_que_falla(None))

    def test_con_previo_se_conserva_el_bloque(self):
        previo = {"vales": 2, "monto": None, "desde": "2026-11-23", "ultimos": []}
        self.assertEqual(self._bloque_que_falla(previo), previo)


if __name__ == "__main__":
    unittest.main()
