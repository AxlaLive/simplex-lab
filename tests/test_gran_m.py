from __future__ import annotations
import unittest
from fractions import Fraction
from motor.gran_m import resolver_gran_m

class TestGranM(unittest.TestCase):
    
    def test_minimizacion_caso_2(self):
        # Caso 2 del documento: Min Z = 2x1 + 3x2
        # Sujeto a: 2x1 + x2 = 10, x1 + 2x2 >= 8
        problema = {
            "sense": "Minimizar",
            "c": [Fraction(2), Fraction(3)],
            "A": [
                [Fraction(2), Fraction(1)],
                [Fraction(1), Fraction(2)]
            ],
            "s": ["=", "≥"],
            "b": [Fraction(10), Fraction(8)],
            "n": 2
        }
        
        resultado = resolver_gran_m(problema)
        # La solución óptima del sistema dado es x1 = 4, x2 = 2, con Z = 14.
        # El valor anterior no satisface la restricción 2x1 + x2 = 10.
        self.assertEqual(resultado["estado"], "optimo")
        self.assertEqual(resultado["Z"], Fraction(14, 1))
        self.assertEqual(resultado["x"][0], Fraction(4, 1))
        self.assertEqual(resultado["x"][1], Fraction(2, 1))

    def test_formato_pasos_para_front(self):
        problema = {
            "sense": "Maximizar",
            "c": [Fraction(3), Fraction(5)],
            "A": [
                [Fraction(1), Fraction(2)],
                [Fraction(2), Fraction(1)]
            ],
            "s": ["≤", "≤"],
            "b": [Fraction(10), Fraction(8)],
            "n": 2
        }

        resultado = resolver_gran_m(problema)
        self.assertEqual(resultado["estado"], "optimo")
        self.assertTrue(resultado["pasos"])
        primer_paso = resultado["pasos"][0]
        self.assertIn("columnas", primer_paso)
        self.assertIn("filas", primer_paso)
        self.assertIn("valores", primer_paso)
        self.assertIn("entra", primer_paso)
        self.assertIn("sale", primer_paso)
        self.assertIn("pivote", primer_paso)
        self.assertIn("explicacion", primer_paso)
        self.assertEqual(primer_paso["columnas"][0], "Z")

    def test_caso_infactible(self):
        # Caso 4: Max Z = x1 + x2 s.a. x1 + x2 <= 2, x1 + x2 >= 5
        problema = {
            "sense": "Maximizar",
            "c": [Fraction(1), Fraction(1)],
            "A": [
                [Fraction(1), Fraction(1)],
                [Fraction(1), Fraction(1)]
            ],
            "s": ["≤", "≥"],
            "b": [Fraction(2), Fraction(5)],
            "n": 2
        }
        
        resultado = resolver_gran_m(problema)
        self.assertEqual(resultado["estado"], "infactible")
        self.assertIn("pasos", resultado)
        self.assertIsInstance(resultado["holguras"], dict)

if __name__ == "__main__":
    unittest.main()