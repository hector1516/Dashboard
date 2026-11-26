"""
Pruebas de las listas RODANTES de celebraciones (pantalla Equipo).

Lo que se fija, porque es fácil de romper sin darse cuenta:

  · `proximos_cumpleanos` cuenta desde HOY (un cumpleaños de hoy lleva
    `dias: 0`) y, si la fecha ya pasó, salta al año siguiente: la lista no se
    vacía el 2 de enero ni en noviembre —que es cuando no cumple nadie.
  · `proximos_aniversarios` sólo incluye `anos >= 1` (el primer año de quien
    entró este año no es un aniversario).
  · El 29 de febrero no revienta en un año no bisiesto.
  · Vienen como máximo tres, ordenados por cercanía.

No abre base de datos: `_rodantes` recibe un cursor de mentira.
"""
import datetime as _dt
import os
import sys
import unittest

_AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_AQUI, "..", "api"))

# `datos` importa `db` → `config`, que exige credenciales al importarse.
os.environ.setdefault("HUB_DB_USER", "pruebas")
os.environ.setdefault("HUB_DB_PASSWORD", "pruebas")

try:
    import datos  # noqa: E402
except ModuleNotFoundError as _exc:   # solo se salta si falta pymssql
    if _exc.name != "pymssql":
        raise
    datos = None
    _MOTIVO = str(_exc)


class CursorFalso:
    """Devuelve las filas que se le dan, como un cursor `as_dict`."""

    def __init__(self, filas):
        self._filas = filas

    def execute(self, *args, **kwargs):
        pass

    def fetchall(self):
        return list(self._filas)


def persona(nombre, mes=None, dia=None, ingreso=None, uid=1):
    return {
        "id_usuario": uid,
        "Nombre": nombre,
        "mes": mes,
        "dia": dia,
        "ingreso": ingreso,
    }


class RodantesTest(unittest.TestCase):
    def setUp(self):
        if datos is None:
            self.skipTest(f"no se pudo importar datos.py: {_MOTIVO}")

    def rodantes(self, filas, hoy):
        return datos._rodantes(CursorFalso(filas), hoy)

    def test_cumpleanos_cruzan_el_anio(self):
        """En noviembre se anuncia el de enero, no se queda vacío."""
        hoy = _dt.date(2026, 11, 25)
        cumples, _, _ = self.rodantes(
            [persona("Ana", 1, 8), persona("Beto", 10, 8), persona("Caro", 12, 1)],
            hoy,
        )
        self.assertEqual([p["nombre"] for p in cumples], ["Caro", "Ana", "Beto"])
        self.assertEqual([p["dias"] for p in cumples], [6, 44, 317])
        self.assertEqual(cumples[0]["fecha"], "2026-12-01")
        self.assertEqual(cumples[1]["fecha"], "2027-01-08")

    def test_el_de_hoy_es_dias_cero(self):
        hoy = _dt.date(2026, 11, 25)
        cumples, _, _ = self.rodantes([persona("Ana", 11, 25)], hoy)
        self.assertEqual(cumples[0]["dias"], 0)
        self.assertEqual(cumples[0]["fecha"], "2026-11-25")

    def test_el_de_ayer_cuenta_para_el_anio_siguiente(self):
        hoy = _dt.date(2026, 11, 25)
        cumples, _, _ = self.rodantes([persona("Ana", 11, 24)], hoy)
        self.assertEqual(cumples[0]["dias"], 364)
        self.assertEqual(cumples[0]["fecha"], "2027-11-24")

    def test_solo_tres_y_ordenados(self):
        hoy = _dt.date(2026, 11, 25)
        filas = [persona(f"P{i}", 12, d) for i, d in enumerate((3, 1, 2, 9))]
        cumples, _, _ = self.rodantes(filas, hoy)
        self.assertEqual([p["nombre"] for p in cumples], ["P1", "P2", "P0"])

    def test_29_de_febrero_no_revienta(self):
        self.assertEqual(datos._proxima_fecha(2, 29, _dt.date(2027, 1, 1)),
                         _dt.date(2027, 2, 28))
        self.assertEqual(datos._proxima_fecha(2, 29, _dt.date(2028, 1, 1)),
                         _dt.date(2028, 2, 29))

    def test_aniversarios_solo_con_un_anio_cumplido(self):
        hoy = _dt.date(2026, 11, 25)
        _, anivs, _ = self.rodantes(
            [
                persona("Nuevo", ingreso="2026-11-20"),          # 2027: su 1.º
                persona("Veterana", ingreso="2011-10-04"),       # 2027: 16 años
                persona("Sin fecha", ingreso=None),
            ],
            hoy,
        )
        self.assertEqual([a["nombre"] for a in anivs], ["Veterana", "Nuevo"])
        self.assertEqual([a["anos"] for a in anivs], [16, 1])
        self.assertEqual(anivs[0]["dias"], 313)
        self.assertNotIn("Sin fecha", [a["nombre"] for a in anivs])

    def test_cuenta_las_personas_activas(self):
        """El ancla no se puede deducir de las listas: trae su propia cuenta."""
        hoy = _dt.date(2026, 11, 25)
        _, _, personas = self.rodantes(
            [persona("Ana", 1, 8), persona("Beto", ingreso="2022-01-01"),
             persona("Caro")],
            hoy,
        )
        self.assertEqual(personas, 3)

    def test_sin_fecha_de_nacimiento_no_inventa(self):
        hoy = _dt.date(2026, 11, 25)
        cumples, _, _ = self.rodantes([persona("Ana"), persona("Beto", 0, 0)], hoy)
        self.assertEqual(cumples, [])


if __name__ == "__main__":
    unittest.main()
