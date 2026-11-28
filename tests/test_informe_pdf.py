from __future__ import annotations

import unittest
from fractions import Fraction

from motor.gran_m import resolver_gran_m
from visualizacion.grafico import geometria
from visualizacion.informe_pdf import generar_informe_con_vistas, generar_informe_pdf


class TestInformePDF(unittest.TestCase):
    def test_exporta_problema_optimo_con_pdf_valido(self):
        problema = {
            "sense": "Minimizar",
            "c": [Fraction(3), Fraction(2)],
            "A": [[Fraction(1), Fraction(1)], [Fraction(2), Fraction(1)], [Fraction(1), Fraction(2)]],
            "s": ["=", "≥", "≥"],
            "b": [Fraction(8), Fraction(10), Fraction(10)],
            "n": 2,
        }
        resultado = {
            "p": problema,
            "m": resolver_gran_m(problema),
            "g": geometria(problema),
            "error": None,
            "modo": "Paso a paso",
        }

        documento, vistas = generar_informe_con_vistas(resultado)

        self.assertTrue(documento.startswith(b"%PDF-"))
        self.assertGreater(len(documento), 2000)
        self.assertGreaterEqual(len(vistas), 4)
        self.assertTrue(all(vista.startswith(b"\x89PNG\r\n\x1a\n") for vista in vistas))

    def test_exporta_estado_infactible_sin_fallar(self):
        problema = {
            "sense": "Maximizar",
            "c": [Fraction(1), Fraction(1)],
            "A": [[Fraction(1), Fraction(1)], [Fraction(1), Fraction(1)]],
            "s": ["≤", "≥"],
            "b": [Fraction(2), Fraction(5)],
            "n": 2,
        }
        resultado = {
            "p": problema,
            "m": resolver_gran_m(problema),
            "g": geometria(problema),
            "error": None,
            "modo": "Solución directa",
        }

        documento = generar_informe_pdf(resultado)

        self.assertTrue(documento.startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()