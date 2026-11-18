"""Placeholder iteration records for the step-by-step view.

These tableaux belong to the Wyndor problem (Max 3x1 + 5x2) and exist only so
the interface can be laid out before the optimization engine returns real
``pasos``. Remove this module once ``resolver_gran_m`` provides them.
"""
from __future__ import annotations

PASOS_WYNDOR = [
    {
        "iteracion": 0,
        "columnas": ["Z", "x1", "x2", "s1", "s2", "s3", "LD"],
        "filas": ["Z", "s1", "s2", "s3"],
        "tablero": [
            ["1", "-3", "-5", "0", "0", "0", "0"],
            ["0", "1", "0", "1", "0", "0", "4"],
            ["0", "0", "2", "0", "1", "0", "12"],
            ["0", "3", "2", "0", "0", "1", "18"],
        ],
        "entra": "x2",
        "razones": ["s1: 4/0 no aplica", "s2: 12/2 = 6", "s3: 18/2 = 9"],
        "sale": "s2",
        "pivote": {"fila": "s2", "columna": "x2"},
        "explicacion": "Entra x2 porque -5 es el coeficiente mas negativo de la fila Z.",
    },
    {
        "iteracion": 1,
        "columnas": ["Z", "x1", "x2", "s1", "s2", "s3", "LD"],
        "filas": ["Z", "s1", "x2", "s3"],
        "tablero": [
            ["1", "-3", "0", "0", "5/2", "0", "30"],
            ["0", "1", "0", "1", "0", "0", "4"],
            ["0", "0", "1", "0", "1/2", "0", "6"],
            ["0", "3", "0", "0", "-1", "1", "6"],
        ],
        "entra": "x1",
        "razones": ["s1: 4/1 = 4", "x2: 6/0 no aplica", "s3: 6/3 = 2"],
        "sale": "s3",
        "pivote": {"fila": "s3", "columna": "x1"},
        "explicacion": "Entra x1 porque -3 es el unico coeficiente negativo que queda en la fila Z.",
    },
]
