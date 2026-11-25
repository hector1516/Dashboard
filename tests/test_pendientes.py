import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from pendientes import DESDE_POR_DEFECTO, armar_pendientes, corte_temporada


class CorteTest(unittest.TestCase):
    def test_corte_valido(self):
        self.assertEqual(corte_temporada("2026-12-01"), "2026-12-01")

    def test_corte_vacio(self):
        self.assertEqual(corte_temporada(None), DESDE_POR_DEFECTO)

    def test_corte_invalido(self):
        self.assertEqual(corte_temporada("basura"), DESDE_POR_DEFECTO)


class ArmarTest(unittest.TestCase):
    def test_suma_y_lista(self):
        totales = {"n": 2, "monto": 1000}
        ultimos = [
            {"persona": "Alfredo", "placa": "RWS675B", "monto": 500, "dias": 0,
             "cerrado": 0, "id_usuario": 7},
            {"persona": "José", "placa": "RYL615A", "monto": 500, "dias": 1,
             "cerrado": 1, "id_usuario": 1},
        ]
        r = armar_pendientes(totales, ultimos, "2026-11-23")
        self.assertEqual(r["vales"], 2)
        self.assertEqual(r["monto"], 1000)
        self.assertEqual(r["desde"], "2026-11-23")
        self.assertEqual(r["ultimos"][0]["nombre"], "Alfredo")
        self.assertFalse(r["ultimos"][0]["cerrado"])
        self.assertTrue(r["ultimos"][1]["cerrado"])

    def test_monto_nulo_no_es_cero(self):
        r = armar_pendientes({"n": 1, "monto": 0},
                             [{"persona": "Héctor", "placa": "X", "monto": None,
                               "dias": 3, "cerrado": 0, "id_usuario": 2}], "2026-11-23")
        self.assertIsNone(r["ultimos"][0]["monto"])
        self.assertEqual(r["monto"], 0)

    def test_sin_pendientes(self):
        r = armar_pendientes({}, [], "2026-11-23")
        self.assertEqual(r["vales"], 0)
        self.assertEqual(r["ultimos"], [])
