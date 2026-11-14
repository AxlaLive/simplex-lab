from __future__ import annotations
import unittest
from fractions import Fraction
from motor.gran_m import resolver_gran_m

class TestGranM(unittest.TestCase):
    
    def test_maximizacion_simple(self):
        # Maximizar Z = 3x1 + 5x2
        # Sujeto a: x1 <= 4, 2x2 <= 12, 3x1 + 2x2 <= 18
        problema = {
            "sense": "Maximizar",
            "c": [Fraction(3), Fraction(5)],
            "A": [
                [Fraction(1), Fraction(0)],
                [Fraction(0), Fraction(2)],
                [Fraction(3), Fraction(2)]
            ],
            "s": ["≤", "≤", "≤"],
            "b": [Fraction(4), Fraction(12), Fraction(18)],
            "n": 2
        }
        
        resultado = resolver_gran_m(problema)
        self.assertEqual(resultado["estado"], "óptimo")
        self.assertEqual(resultado["Z"], Fraction(36))
        self.assertEqual(resultado["x"][0], Fraction(2))
        self.assertEqual(resultado["x"][1], Fraction(6))

    def test_minimizacion_con_restriccion_mayor_igual(self):
        # Minimizar Z = 4x1 + 1x2
        # Sujeto a:
        # 3x1 + 1x2 = 3
        # 4x1 + 3x2 >= 6
        # x1, x2 >= 0
        problema = {
            "sense": "Minimizar",
            "c": [Fraction(4), Fraction(1)],
            "A": [
                [Fraction(3), Fraction(1)],
                [Fraction(4), Fraction(3)]
            ],
            "s": ["=", "≥"],
            "b": [Fraction(3), Fraction(6)],
            "n": 2
        }
        
        resultado = resolver_gran_m(problema)
        self.assertEqual(resultado["estado"], "óptimo")
        self.assertIn("Z", resultado)
        self.assertGreaterEqual(len(resultado["x"]), 2)

if __name__ == "__main__":
    unittest.main()