"""Tests for the graphical method (two-variable problems).

Run with:  python -m unittest discover tests
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")

from visualizacion.grafico import dibujar, fmt, geometria  # noqa: E402


def problema(sense, c, A, s, b):
    """Build a problem dict with exact Fraction coefficients."""
    return {
        "sense": sense,
        "c": [Fraction(str(v)) for v in c],
        "A": [[Fraction(str(v)) for v in row] for row in A],
        "s": s,
        "b": [Fraction(str(v)) for v in b],
        "n": len(c),
    }


class TestGeometria(unittest.TestCase):
    def test_caso_1_region_optima(self):
        p = problema("Maximizar", [50, 80],
                     [[2, 1], [1, 3], [0, 1]], ["≤", "≤", "≤"], [100, 90, 40])
        g = geometria(p)
        self.assertEqual(g["estado"], "óptimo")
        self.assertAlmostEqual(g["mejor"][0], 42.0)
        self.assertAlmostEqual(g["mejor"][1], 16.0)
        self.assertAlmostEqual(g["Z"], 3380.0)

    def test_caso_2_minimizacion_con_igualdad_y_exceso(self):
        p = problema("Minimizar", [4, 1],
                     [[3, 1], [4, 3], [-1, -2]], ["=", "≥", "≥"], [3, 6, -4])
        g = geometria(p)
        self.assertEqual(g["estado"], "óptimo")
        self.assertAlmostEqual(g["mejor"][0], 0.4)
        self.assertAlmostEqual(g["mejor"][1], 1.8)
        self.assertAlmostEqual(g["Z"], 3.4)
        self.assertEqual(fmt(g["mejor"][0]), "2/5")
        self.assertEqual(fmt(g["mejor"][1]), "9/5")

    def test_caso_4_infactible(self):
        p = problema("Maximizar", [1, 1], [[1, 1], [1, 1]], ["≤", "≥"], [2, 5])
        self.assertEqual(geometria(p)["estado"], "infactible")

    def test_caso_5_no_acotado(self):
        p = problema("Maximizar", [1, 1], [[1, -1], [-1, 1]], ["≤", "≤"], [1, 2])
        self.assertEqual(geometria(p)["estado"], "no acotado")

    def test_caso_6_optimos_multiples(self):
        p = problema("Maximizar", [2, 4], [[1, 2], [1, 1]], ["≤", "≤"], [5, 4])
        g = geometria(p)
        self.assertEqual(g["estado"], "múltiples")
        self.assertAlmostEqual(g["Z"], 10.0)

    def test_caso_7_optimo_degenerado(self):
        p = problema("Maximizar", [3, 9], [[1, 4], [1, 2]], ["≤", "≤"], [8, 4])
        g = geometria(p)
        self.assertEqual(g["estado"], "óptimo")
        self.assertAlmostEqual(g["mejor"][0], 0.0)
        self.assertAlmostEqual(g["mejor"][1], 2.0)
        self.assertAlmostEqual(g["Z"], 18.0)

    def test_vertices_de_la_region(self):
        p = problema("Maximizar", [50, 80],
                     [[2, 1], [1, 3], [0, 1]], ["≤", "≤", "≤"], [100, 90, 40])
        self.assertEqual(len(geometria(p)["V"]), 4)


class TestDibujar(unittest.TestCase):
    def test_devuelve_figura_con_ejes(self):
        p = problema("Maximizar", [50, 80],
                     [[2, 1], [1, 3], [0, 1]], ["≤", "≤", "≤"], [100, 90, 40])
        fig = dibujar(p, geometria(p))
        self.assertTrue(fig.axes)
        self.assertGreater(len(fig.axes[0].collections), 0)


class TestSinDependenciaDeStreamlit(unittest.TestCase):
    def test_grafico_no_importa_streamlit(self):
        code = (
            "import sys; import visualizacion.grafico; "
            "sys.exit(1 if 'streamlit' in sys.modules else 0)"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0,
                         "visualizacion/grafico.py debe mantenerse libre de Streamlit")


if __name__ == "__main__":
    unittest.main()
