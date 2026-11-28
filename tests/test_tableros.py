"""Tests for the tableau renderer.

Run with:  python -m unittest discover tests
"""
from __future__ import annotations

import subprocess
import sys
import unittest

import pandas as pd

from tests.fixtures import PASOS_WYNDOR
from visualizacion.grafico import AMARILLO
from visualizacion.tableros import (
    construir_tablero,
    construir_tablero_final,
    razones_texto,
    render,
    resaltar_pivote,
)


class TestConstruirTablero(unittest.TestCase):
    def test_dimensiones_y_valores(self):
        df = construir_tablero(PASOS_WYNDOR[0])
        self.assertEqual(df.shape, (4, 7))
        self.assertEqual(list(df.index), ["Z", "s1", "s2", "s3"])
        self.assertEqual(df.loc["s3", "x2"], "2")
        self.assertEqual(df.loc["Z", "x2"], "-5")

    def test_conserva_orden_de_columnas(self):
        df = construir_tablero(PASOS_WYNDOR[1])
        self.assertEqual(list(df.columns)[-1], "LD")
        self.assertEqual(list(df.index)[2], "x2")

    def test_construye_tabla_final_del_motor(self):
        tabla_final = {
            "filas": ["Z", "x2"],
            "columnas": ["Z", "x1", "x2", "LD"],
            "tablero_texto": [
                ["1", "0", "0", "10"],
                ["0", "1/2", "1", "5/2"],
            ],
        }

        df = construir_tablero_final(tabla_final)

        self.assertEqual(list(df.index), ["Z", "x2"])
        self.assertEqual(list(df.columns), ["Z", "x1", "x2", "LD"])
        self.assertEqual(df.loc["x2", "LD"], "5/2")


class TestResaltarPivote(unittest.TestCase):
    def test_marca_la_celda_del_pivote(self):
        df = construir_tablero(PASOS_WYNDOR[0])
        html = resaltar_pivote(df, "s2", "x2").to_html()
        self.assertIn(AMARILLO.lower(), html.lower())

    def test_pivote_inexistente_no_rompe(self):
        df = construir_tablero(PASOS_WYNDOR[0])
        html = resaltar_pivote(df, "no_existe", "x2").to_html()
        self.assertNotIn("font-weight:700", html)
        self.assertEqual(df.shape, (4, 7))

    def test_pivote_none_no_rompe(self):
        df = construir_tablero(PASOS_WYNDOR[0])
        html = resaltar_pivote(df, None, None).to_html()
        self.assertNotIn("font-weight:700", html)

    def test_no_modifica_el_dataframe_original(self):
        df = construir_tablero(PASOS_WYNDOR[0])
        antes = df.copy()
        resaltar_pivote(df, "s2", "x2").to_html()
        pd.testing.assert_frame_equal(df, antes)


class TestRender(unittest.TestCase):
    def test_render_de_cada_paso(self):
        for paso in PASOS_WYNDOR:
            self.assertTrue(render(paso).to_html())

    def test_render_sin_pivote(self):
        paso = dict(PASOS_WYNDOR[0])
        paso["pivote"] = None
        self.assertTrue(render(paso).to_html())

    def test_render_pivote_nombra_fila_y_columna(self):
        html = render(PASOS_WYNDOR[1]).to_html()
        self.assertIn(AMARILLO.lower(), html.lower())


class TestRazones(unittest.TestCase):
    def test_une_las_razones(self):
        texto = razones_texto(PASOS_WYNDOR[0])
        self.assertIn("s2: 12/2 = 6", texto)
        self.assertIn(" · ", texto)

    def test_sin_razones(self):
        self.assertEqual(razones_texto({}), "")


class TestSinDependenciaDeStreamlit(unittest.TestCase):
    def test_tableros_no_importa_streamlit(self):
        code = (
            "import sys; import visualizacion.tableros; "
            "sys.exit(1 if 'streamlit' in sys.modules else 0)"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         "visualizacion/tableros.py debe mantenerse libre de Streamlit")


if __name__ == "__main__":
    unittest.main()
