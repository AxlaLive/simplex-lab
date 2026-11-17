"""Tableau rendering for the step-by-step view.

This module turns the iteration records produced by the optimization engine
into pandas tables and styles, highlighting the pivot cell. It never imports
Streamlit: the interface decides where to place the result.

Iteration record ("paso") contract:

    paso = {
        "iteracion": 0,
        "columnas": ["Z", "x1", "x2", "s1", "LD"],
        "filas": ["Z", "s1"],
        "tablero": [["1", "-3", "-5", "0", "0"],
                    ["0", "1", "0", "1", "4"]],
        "entra": "x2",
        "razones": ["s1: 4/2 = 2"],
        "sale": "s1",
        "pivote": {"fila": "s1", "columna": "x2"},   # or None
        "explicacion": "Entra x2 porque -5 es el coeficiente mas negativo de la fila Z.",
    }
"""
from __future__ import annotations

import pandas as pd

from .grafico import AMARILLO, TINTA


def construir_tablero(paso: dict) -> pd.DataFrame:
    """Build the tableau DataFrame from an iteration record."""
    return pd.DataFrame(paso["tablero"], index=paso["filas"], columns=paso["columnas"])


def resaltar_pivote(df: pd.DataFrame, fila: str | None, columna: str | None):
    """Return a styled DataFrame with the pivot cell highlighted.

    Unknown row or column names are ignored instead of raising, so a missing
    pivot never breaks the whole step-by-step view.
    """
    destacar = (
        fila is not None
        and columna is not None
        and fila in df.index
        and columna in df.columns
    )

    def estilo(d: pd.DataFrame) -> pd.DataFrame:
        salida = pd.DataFrame("", index=d.index, columns=d.columns)
        if destacar:
            salida.loc[fila, columna] = (
                f"background-color:{AMARILLO};color:{TINTA};font-weight:700"
            )
        return salida

    return df.style.apply(estilo, axis=None)


def render(paso: dict):
    """Return the styled tableau for one iteration."""
    pivote = paso.get("pivote") or {}
    return resaltar_pivote(
        construir_tablero(paso),
        pivote.get("fila"),
        pivote.get("columna"),
    )


def razones_texto(paso: dict) -> str:
    """Join the minimum-ratio reasonings into a single readable line."""
    return " · ".join(paso.get("razones") or [])
