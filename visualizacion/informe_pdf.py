from __future__ import annotations

from fractions import Fraction
from io import BytesIO
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

from motor.sensibilidad import analizar_sensibilidad
from visualizacion.grafico import dibujar, geometria

TINTA = "#0E1B3D"
ACENTO = "#4B4DED"
GRIS = "#5B6788"
CLARO = "#EEF2FB"
VERDE = "#18794E"
BORDES = "#DCE3EF"


def _numero(valor: object) -> str:
    if isinstance(valor, Fraction):
        return str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"
    return str(valor)


def _expresion_lineal(coeficientes: list) -> str:
    terminos = []
    for indice, coeficiente in enumerate(coeficientes):
        valor = Fraction(str(coeficiente))
        termino = f"{_numero(abs(valor))} x{indice + 1}"
        if not terminos:
            terminos.append(f"-{termino}" if valor < 0 else termino)
        else:
            signo = "-" if valor < 0 else "+"
            terminos.append(f"{signo} {termino}")
    return " ".join(terminos) or "0"


def _objetivo(problema: dict) -> str:
    return f"{problema['sense']} Z = {_expresion_lineal(problema['c'])}"


def _restriccion(coeficientes: list, signo: str, lado_derecho: object) -> str:
    return f"{_expresion_lineal(coeficientes)} {signo} {_numero(lado_derecho)}"


def _pagina(titulo: str, subtitulo: str = ""):
    figura = plt.figure(figsize=(11.69, 8.27), facecolor="white")
    figura.add_artist(Rectangle((0, 0.89), 1, 0.11, transform=figura.transFigure,
                                facecolor=TINTA, edgecolor="none", zorder=-1))
    figura.add_artist(Rectangle((0.065, 0.89), 0.012, 0.11, transform=figura.transFigure,
                                facecolor="#FFC93C", edgecolor="none", zorder=0))
    figura.text(0.095, 0.958, "SIMPLEX LAB", fontsize=8, fontweight="bold", color="#D9E5FF")
    figura.text(0.095, 0.914, titulo, fontsize=16, fontweight="bold", color="white")
    if subtitulo:
        figura.text(0.94, 0.92, subtitulo, fontsize=8, color="#D9E5FF", ha="right")
    figura.add_artist(Rectangle((0.065, 0.065), 0.87, 0.0015, transform=figura.transFigure,
                                facecolor=BORDES, edgecolor="none"))
    figura.text(0.07, 0.035, "Programación lineal · Informe de resultados", fontsize=8, color=GRIS)
    return figura


def _guardar_pagina(pdf: PdfPages, figura, vistas: list[bytes] | None) -> None:
    pdf.savefig(figura, bbox_inches="tight")
    if vistas is not None:
        imagen = BytesIO()
        figura.savefig(imagen, format="png", dpi=100, bbox_inches="tight")
        vistas.append(imagen.getvalue())
    plt.close(figura)


def _tabla(figura, encabezados: list[str], filas: list[list[str]], bbox: list[float], row_labels=None):
    eje = figura.add_axes(bbox)
    eje.axis("off")
    tabla = eje.table(
        cellText=filas,
        colLabels=encabezados,
        rowLabels=row_labels,
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(max(6, min(9, 90 // max(1, len(encabezados)))))
    for (fila, _), celda in tabla.get_celld().items():
        celda.set_edgecolor(BORDES)
        celda.set_linewidth(0.55)
        if fila == 0:
            celda.set_facecolor(TINTA)
            celda.set_text_props(color="white", weight="bold")
        else:
            celda.set_facecolor("#F3F6FB" if fila % 2 == 0 else "white")
            celda.set_text_props(color=TINTA)
    return tabla


def _pagina_texto(
    pdf: PdfPages,
    titulo: str,
    lineas: list[str],
    subtitulo: str = "",
    vistas: list[bytes] | None = None,
) -> None:
    figura = _pagina(titulo, subtitulo)
    y = 0.81
    for linea in lineas:
        envueltas = textwrap.wrap(linea, width=112) or [""]
        for texto in envueltas:
            figura.text(0.08, y, texto, fontsize=10, color=TINTA, va="top")
            y -= 0.042
            if y < 0.08:
                _guardar_pagina(pdf, figura, vistas)
                figura = _pagina(titulo + " (continuación)", subtitulo)
                y = 0.81
    _guardar_pagina(pdf, figura, vistas)


def _pagina_tableau(
    pdf: PdfPages,
    titulo: str,
    columnas: list[str],
    filas: list[str],
    valores: list[list[str]],
    detalle: list[str] | None = None,
    pivote: dict | None = None,
    vistas: list[bytes] | None = None,
) -> None:
    figura = _pagina(titulo)
    y = 0.84
    for linea in detalle or []:
        for texto in textwrap.wrap(linea, width=132):
            figura.text(0.08, y, texto, fontsize=8.5, color=GRIS, va="top")
            y -= 0.035
    alto_tabla = max(0.22, y - 0.16)
    tabla = _tabla(figura, columnas, valores, [0.08, 0.14, 0.84, alto_tabla], row_labels=filas or None)
    if pivote:
        fila_pivote = pivote.get("fila")
        columna_pivote = pivote.get("columna")
        if fila_pivote in filas and columna_pivote in columnas:
            celda = tabla[(filas.index(fila_pivote) + 1, columnas.index(columna_pivote))]
            celda.set_facecolor("#FFC93C")
            celda.set_text_props(color=TINTA, weight="bold")
    _guardar_pagina(pdf, figura, vistas)


def _pagina_sensibilidad(
    pdf: PdfPages,
    titulo: str,
    elementos: list[dict],
    columnas: list[str],
    claves: list[str],
    vistas: list[bytes] | None = None,
) -> None:
    for inicio in range(0, len(elementos), 4):
        grupo = elementos[inicio:inicio + 4]
        figura = _pagina(titulo, f"Filas {inicio + 1}–{inicio + len(grupo)}")
        filas = [[_numero(elemento[clave]) for clave in claves] for elemento in grupo]
        _tabla(figura, columnas, filas, [0.07, 0.55, 0.86, 0.25])
        lineas = [
            f"{elemento.get('variable', elemento.get('restriccion', ''))}: {elemento['interpretacion']}"
            for elemento in grupo
        ]
        y = 0.48
        for linea in lineas:
            for texto in textwrap.wrap(linea, width=118):
                figura.text(0.08, y, texto, fontsize=8, color=TINTA, va="top")
                y -= 0.035
        _guardar_pagina(pdf, figura, vistas)


def _generar_informe(resultado_interfaz: dict, incluir_vistas: bool) -> tuple[bytes, list[bytes]]:
    problema = resultado_interfaz["p"]
    resultado = resultado_interfaz.get("m")
    buffer = BytesIO()
    vistas: list[bytes] | None = [] if incluir_vistas else None

    with PdfPages(buffer) as pdf:
        figura = _pagina("Informe de programación lineal", "Simplex Lab")
        figura.text(0.08, 0.81, _objetivo(problema), fontsize=13, fontweight="bold", color=TINTA)
        estado = "Error del motor" if resultado is None else resultado.get("estado", "sin estado")
        estado = {
            "optimo": "Óptimo",
            "multiples": "Óptimos múltiples",
            "infactible": "Infactible",
            "no_acotado": "No acotado",
            "degenerado": "Degenerado",
        }.get(estado, estado)
        figura.text(0.08, 0.72, f"Estado: {estado}", fontsize=11, color=ACENTO)

        if resultado is None:
            figura.text(0.08, 0.64, f"Detalle: {resultado_interfaz.get('error') or 'No disponible'}", fontsize=10, color=TINTA)
        elif resultado.get("estado") == "optimo":
            variables = ", ".join(
                f"x{indice + 1} = {_numero(valor)}" for indice, valor in enumerate(resultado["x"])
            )
            figura.add_artist(Rectangle((0.07, 0.39), 0.86, 0.19, transform=figura.transFigure,
                                        facecolor="#EAF7F2", edgecolor="none"))
            figura.text(0.09, 0.535, "SOLUCIÓN ÓPTIMA", fontsize=8, fontweight="bold", color=VERDE)
            figura.text(0.09, 0.465, variables, fontsize=13, fontweight="bold", color=TINTA)
            figura.text(0.76, 0.465, f"Z = {_numero(resultado['Z'])}", fontsize=16,
                        fontweight="bold", color=VERDE, ha="right")
            holguras = resultado.get("holguras") or {}
            figura.text(
                0.08,
                0.30,
                "Holguras y excesos: " + (", ".join(f"{nombre} = {_numero(valor)}" for nombre, valor in holguras.items()) or "no disponibles"),
                fontsize=10,
                color=TINTA,
            )
        else:
            figura.text(0.08, 0.64, "No hay una solución óptima que reportar para este estado.", fontsize=10, color=TINTA)

        _guardar_pagina(pdf, figura, vistas)

        filas_restricciones = [
            [f"R{indice}", _restriccion(coeficientes, signo, lado_derecho)]
            for indice, (coeficientes, signo, lado_derecho) in enumerate(
                zip(problema["A"], problema["s"], problema["b"]), 1
            )
        ]
        _pagina_tableau(
            pdf,
            "Problema ingresado · Restricciones",
            ["Restricción", "Expresión"],
            [],
            filas_restricciones,
            vistas=vistas,
        )

        if resultado:
            for paso in resultado.get("pasos", []):
                detalle = [
                    paso.get("explicacion", ""),
                    "Entra: " + str(paso.get("entra", "—")),
                    "Sale: " + str(paso.get("sale", "—")),
                    "Razones: " + "; ".join(paso.get("razones", [])),
                ]
                _pagina_tableau(
                    pdf,
                    f"Iteración {paso.get('iteracion', '')}",
                    paso["columnas"],
                    paso["filas"],
                    paso["tablero"],
                    detalle,
                    paso.get("pivote"),
                    vistas,
                )

            tableau_final = resultado.get("tableau_final")
            if tableau_final:
                _pagina_tableau(
                    pdf,
                    "Tabla final con resultados",
                    tableau_final["columnas"],
                    tableau_final["filas"],
                    tableau_final["tablero_texto"],
                    [
                        "Variables básicas: " + ", ".join(tableau_final["variables_basicas"]),
                        "Solución: " + ", ".join(
                            f"x{indice + 1} = {_numero(valor)}"
                            for indice, valor in enumerate(resultado.get("x", []))
                        ),
                        "Z = " + _numero(resultado["Z"]),
                    ],
                    vistas=vistas,
                )

        grafico = resultado_interfaz.get("g")
        if problema.get("n") == 2:
            if grafico is None:
                grafico = geometria(problema)
            if grafico.get("estado") == "infactible":
                _pagina_texto(
                    pdf,
                    "Gráfico",
                    ["La región factible está vacía; no hay una región que graficar."],
                    vistas=vistas,
                )
            else:
                figura = dibujar(problema, grafico)
                figura.set_size_inches(11.69, 8.27)
                figura.subplots_adjust(top=0.84, bottom=0.14)
                figura.add_artist(Rectangle((0, 0.89), 1, 0.11, transform=figura.transFigure,
                                            facecolor=TINTA, edgecolor="none", zorder=-1))
                figura.add_artist(Rectangle((0.065, 0.89), 0.012, 0.11, transform=figura.transFigure,
                                            facecolor="#FFC93C", edgecolor="none", zorder=0))
                figura.text(0.095, 0.958, "SIMPLEX LAB", fontsize=8, fontweight="bold", color="#D9E5FF")
                figura.text(0.095, 0.914, "Región factible y recta objetivo",
                            color="white", fontsize=16, fontweight="bold")
                figura.add_artist(Rectangle((0.065, 0.065), 0.87, 0.0015, transform=figura.transFigure,
                                            facecolor=BORDES, edgecolor="none"))
                figura.text(0.07, 0.035, "Programación lineal · Informe de resultados", fontsize=8, color=GRIS)
                _guardar_pagina(pdf, figura, vistas)
        else:
            _pagina_texto(
                pdf,
                "Gráfico",
                ["El gráfico solo está disponible para problemas con dos variables."],
                vistas=vistas,
            )

        if resultado:
            sensibilidad = analizar_sensibilidad(problema, resultado)
            if not sensibilidad["disponible"]:
                lineas = [sensibilidad["mensaje"]]
                lineas.extend(sensibilidad.get("advertencias", []))
                _pagina_texto(pdf, "Análisis de sensibilidad", lineas, vistas=vistas)
            else:
                if sensibilidad.get("advertencias"):
                    _pagina_texto(
                        pdf,
                        "Advertencias de sensibilidad",
                        sensibilidad["advertencias"],
                        vistas=vistas,
                    )
                _pagina_sensibilidad(
                    pdf,
                    "Sensibilidad · Variables",
                    sensibilidad["variables"],
                    ["Variable", "Valor óptimo", "Costo reducido", "Coeficiente", "Mínimo", "Máximo"],
                    ["variable", "valor_optimo", "costo_reducido", "coeficiente_objetivo", "minimo", "maximo"],
                    vistas,
                )
                _pagina_sensibilidad(
                    pdf,
                    "Sensibilidad · Restricciones",
                    sensibilidad["restricciones"],
                    ["Restricción", "Precio sombra", "Lado derecho", "Mínimo", "Máximo"],
                    ["restriccion", "precio_sombra", "lado_derecho", "minimo", "maximo"],
                    vistas,
                )

    return buffer.getvalue(), vistas or []


def generar_informe_pdf(resultado_interfaz: dict) -> bytes:
    """Export the submitted problem and all available solution details to PDF."""
    return _generar_informe(resultado_interfaz, incluir_vistas=False)[0]


def generar_informe_con_vistas(resultado_interfaz: dict) -> tuple[bytes, list[bytes]]:
    """Return the PDF and matching page images for an in-app preview."""
    return _generar_informe(resultado_interfaz, incluir_vistas=True)