"""Simplex Lab: prototipo de interfaz (Streamlit).

Ejecutar:  streamlit run app.py

Qué es real y qué es demo
- Entrada, validación, tablas editables, ejemplos y navegación: reales.
- Gráfico (n = 2): real, calculado aquí con enumeración de vértices.
- Solución (n = 2): vista previa sacada del método gráfico.
- Paso a paso y sensibilidad: maqueta de formato con el problema de Wyndor.
  Aquí se conecta el motor propio (Gran M / simplex revisado), ver `resolver()`.
"""
from __future__ import annotations

import itertools
import math
from fractions import Fraction

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simplex Lab", page_icon="📐", layout="wide")

ACENTO, TINTA, GRIS, AMARILLO = "#4B4DED", "#0E1B3D", "#5B6788", "#FFC93C"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700&family=DM+Sans:wght@400;500;700&display=swap');
html, body, .stApp, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1280px; padding: 4.5rem 3rem 3rem; }

/* encabezado */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 40px; margin-bottom: 1.4rem; }
.logo { display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
        font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 20px; color: #0E1B3D; }
.hero h1 { margin: 0; padding: 0; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
           font-size: 46px; line-height: 1.05; letter-spacing: -0.025em; max-width: 640px; color: #0E1B3D; }

/* paneles */
.st-key-panel_izq, .st-key-panel_der { background: #fff; border-radius: 22px; padding: 1.7rem;
    box-shadow: 0 1px 2px rgba(14,27,61,.06), 0 12px 32px rgba(14,27,61,.07); }
.ptitulo { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 600; font-size: 20px; color: #0E1B3D; }
.sec { font-size: .85rem; color: #5B6788; margin: .9rem 0 .15rem 0; }

/* selectores tipo píldora (radios horizontales) */
div[role="radiogroup"] { background: #EEF2FB; border-radius: 12px; padding: 4px; gap: 2px; width: 100%; }
div[role="radiogroup"] label { flex: 1; justify-content: center; padding: 6px 10px; border-radius: 9px; margin: 0; cursor: pointer; }
div[role="radiogroup"] label > div:first-child { display: none; }
div[role="radiogroup"] label p { font-size: 14px; color: #5B6788; text-align: center; }
div[role="radiogroup"] label:has(input:checked) { background: #fff; box-shadow: 0 1px 3px rgba(14,27,61,.14); }
div[role="radiogroup"] label:has(input:checked) p { color: #0E1B3D; font-weight: 700; }

/* botón principal */
.stButton > button[kind="primary"] { height: 48px; border: 0; border-radius: 14px; background: #4B4DED;
    font-size: 16px; font-weight: 700; box-shadow: 0 8px 20px rgba(75,77,237,.32); }
.stButton > button[kind="primary"]:hover { background: #3B3DD6; }

/* pestañas tipo píldora */
button[data-baseweb="tab"] { border-radius: 999px; padding: 8px 16px; height: auto; font-weight: 500; }
button[data-baseweb="tab"][aria-selected="true"] { background: #0E1B3D; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #fff; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

/* resultado */
.zrow { display: flex; align-items: center; gap: 18px; margin: .6rem 0 1rem 0; }
.zcard { background: #E8E9FF; border-radius: 18px; padding: 14px 22px; }
.zcard span { display: block; font-size: 13px; color: #3B3DD6; font-weight: 500; }
.zcard b { font-family: 'Bricolage Grotesque', sans-serif; font-size: 48px; color: #3B3DD6; line-height: 1.05; }
.xs { display: flex; gap: 28px; }
.xs span { display: block; font-size: 13px; color: #5B6788; }
.xs b { font-family: 'Bricolage Grotesque', sans-serif; font-size: 32px; color: #0E1B3D; }
.estado { display: inline-block; padding: 5px 14px; border-radius: 999px; background: #DDF5E8;
          color: #146B3A; font-weight: 500; font-size: 14px; }
.estado.mal { background: #FDECEC; color: #B42318; }
.vacio { color: #5B6788; padding: 3rem 1rem; text-align: center; font-size: 15px; }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────── Ejemplos del enunciado ─────────────────────────
EJEMPLOS = {
    "Región con restricción redundante": dict(
        sense="Maximizar", c=["50", "80"],
        A=[["2", "1"], ["1", "3"], ["0", "1"]], s=["≤", "≤", "≤"], b=["100", "90", "40"]),
    "Minimizar con =, ≥ y lado derecho negativo": dict(
        sense="Minimizar", c=["4", "1"],
        A=[["3", "1"], ["4", "3"], ["-1", "-2"]], s=["=", "≥", "≥"], b=["3", "6", "-4"]),
    "Tres variables": dict(
        sense="Maximizar", c=["3", "2", "5"],
        A=[["1", "2", "1"], ["3", "0", "2"], ["1", "4", "0"]], s=["≤", "≤", "≤"],
        b=["430", "460", "420"]),
    "Infactible": dict(
        sense="Maximizar", c=["1", "1"], A=[["1", "1"], ["1", "1"]], s=["≤", "≥"], b=["2", "5"]),
    "No acotado": dict(
        sense="Maximizar", c=["1", "1"], A=[["1", "-1"], ["-1", "1"]], s=["≤", "≤"], b=["1", "2"]),
    "Óptimos múltiples": dict(
        sense="Maximizar", c=["2", "4"], A=[["1", "2"], ["1", "1"]], s=["≤", "≤"], b=["5", "4"]),
    "Degenerado": dict(
        sense="Maximizar", c=["3", "9"], A=[["1", "4"], ["1", "2"]], s=["≤", "≤"], b=["8", "4"]),
}
NINGUNO = "Elegir un ejemplo"


def cols(n: int) -> list[str]:
    return [f"x{i + 1}" for i in range(n)]


def _poner(e: dict) -> None:
    n = len(e["c"])
    st.session_state.sense = e["sense"]
    st.session_state.n = n
    st.session_state.c_df = pd.DataFrame([e["c"]], columns=cols(n))
    a = pd.DataFrame(e["A"], columns=cols(n))
    a["Signo"] = e["s"]
    a["Lado derecho"] = e["b"]
    st.session_state.a_df = a
    st.session_state.ver = st.session_state.get("ver", 0) + 1
    st.session_state.pop("res", None)


def al_elegir_ejemplo() -> None:
    nombre = st.session_state.ejemplo
    if nombre in EJEMPLOS:
        _poner(EJEMPLOS[nombre])


def al_cambiar_n() -> None:
    """Redimensiona las tablas conservando lo ya escrito."""
    n = st.session_state.n
    c = st.session_state.get("_c_now", st.session_state.c_df)
    a = st.session_state.get("_a_now", st.session_state.a_df)

    def ajustar(df: pd.DataFrame, extras: list[str]) -> pd.DataFrame:
        datos = {k: (df[k].fillna("") if k in df else [""] * len(df)) for k in cols(n)}
        for k in extras:
            datos[k] = df[k] if k in df else [""] * len(df)
        return pd.DataFrame(datos, index=df.index).reset_index(drop=True)

    st.session_state.c_df = ajustar(c, [])
    st.session_state.a_df = ajustar(a, ["Signo", "Lado derecho"])
    st.session_state.ver += 1
    st.session_state.pop("res", None)


if "ver" not in st.session_state:
    _poner(EJEMPLOS[next(iter(EJEMPLOS))])

# ───────────────────────── Validación ─────────────────────────


def num(v, donde: str, errs: list[str]):
    vacio = v is None or (isinstance(v, float) and math.isnan(v))
    s = "" if vacio else str(v).strip().replace(",", ".")
    if not s:
        errs.append(f"Falta un valor en {donde}.")
        return None
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        errs.append(f"«{s}» no es un número en {donde}. Usa enteros, decimales o fracciones como 2/5.")
        return None


def leer(c_df: pd.DataFrame, a_df: pd.DataFrame, n: int):
    errs: list[str] = []
    c = [num(c_df.iloc[0][f"x{j + 1}"], f"el coeficiente de x{j + 1}", errs) for j in range(n)]
    if len(a_df) == 0:
        errs.append("Agrega al menos una restricción.")
    A, s, b = [], [], []
    for i, (_, r) in enumerate(a_df.iterrows(), 1):
        A.append([num(r[f"x{j + 1}"], f"la restricción {i} (x{j + 1})", errs) for j in range(n)])
        signo = r["Signo"]
        if signo not in ("≤", "≥", "="):
            errs.append(f"Elige el signo de la restricción {i}.")
        s.append(signo)
        b.append(num(r["Lado derecho"], f"el lado derecho de la restricción {i}", errs))
    if errs:
        return None, errs
    return dict(sense=st.session_state.sense, c=c, A=A, s=s, b=b, n=n), []


def fmt(v) -> str:
    f = Fraction(float(v)).limit_denominator(1000)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


# ───────────────────────── Geometría (método gráfico, n = 2) ─────────────────────────


def geometria(p: dict) -> dict:
    c = [float(v) for v in p["c"]]
    sg = 1 if p["sense"] == "Maximizar" else -1
    R = [(float(a[0]), float(a[1]), float(bb), s) for a, bb, s in zip(p["A"], p["b"], p["s"])]
    R += [(1.0, 0.0, 0.0, "≥"), (0.0, 1.0, 0.0, "≥")]

    def cumple(pt, lst):
        for a1, a2, r, s in lst:
            v = a1 * pt[0] + a2 * pt[1]
            if (s == "≤" and v > r + 1e-9) or (s == "≥" and v < r - 1e-9) or (s == "=" and abs(v - r) > 1e-9):
                return False
        return True

    def vertices(lst):
        out: list[tuple[float, float]] = []
        for (a1, a2, r1, _), (b1, b2, r2, _) in itertools.combinations(lst, 2):
            det = a1 * b2 - a2 * b1
            if abs(det) < 1e-12:
                continue
            pt = ((r1 * b2 - a2 * r2) / det, (a1 * r2 - b1 * r1) / det)
            if cumple(pt, lst) and not any(math.dist(pt, q) < 1e-9 for q in out):
                out.append(pt)
        return out

    V = vertices(R)
    if not V:
        return {"estado": "infactible"}
    L = max(5.0, 1.35 * max(max(abs(x), abs(y)) for x, y in V))
    VB = vertices(R + [(1.0, 0.0, L, "≤"), (0.0, 1.0, L, "≤")])
    cx, cy = sum(q[0] for q in VB) / len(VB), sum(q[1] for q in VB) / len(VB)
    VB.sort(key=lambda q: math.atan2(q[1] - cy, q[0] - cx))

    def Z(q):
        return c[0] * q[0] + c[1] * q[1]

    mejor = max(V, key=lambda q: sg * Z(q))
    if sg * Z(max(VB, key=lambda q: sg * Z(q))) > sg * Z(mejor) + 1e-9:
        estado = "no acotado"
    elif sum(abs(Z(q) - Z(mejor)) < 1e-9 for q in V) > 1:
        estado = "múltiples"
    else:
        estado = "óptimo"
    return dict(estado=estado, V=V, VB=VB, L=L, mejor=mejor, Z=Z(mejor), Zf=Z, c=c)


def dibujar(p: dict, g: dict):
    L = g["L"]
    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    ax.set_xlim(0, L)
    ax.set_ylim(0, L)
    if len(g["VB"]) >= 3:
        xs, ys = zip(*g["VB"])
        ax.fill(xs, ys, color=ACENTO, alpha=0.14, lw=0)
    t = np.linspace(0, 1, 200)
    for i, (a, bb) in enumerate(zip(p["A"], p["b"]), 1):
        a1, a2, r = float(a[0]), float(a[1]), float(bb)
        if abs(a2) > 1e-12:
            xs, ys = np.array([0.0, L]), (r - a1 * np.array([0.0, L])) / a2
        elif abs(a1) > 1e-12:
            xs, ys = np.array([r / a1] * 2), np.array([0.0, L])
        else:
            continue
        ax.plot(xs, ys, color=GRIS, lw=1.1, alpha=0.8)
        X, Y = xs[0] + (xs[1] - xs[0]) * t, ys[0] + (ys[1] - ys[0]) * t
        dentro = np.where((X >= 0) & (X <= L) & (Y >= 0) & (Y <= L))[0]
        if len(dentro):
            j = dentro[int(len(dentro) * 0.8)]
            ax.annotate(f"R{i}", (X[j], Y[j]), xytext=(4, 4), textcoords="offset points",
                        fontsize=9, color=GRIS)
    c0, c1 = g["c"]
    if abs(c0) > 1e-12 or abs(c1) > 1e-12:
        xs = np.array([0.0, L])
        if abs(c1) > 1e-12:
            ax.plot(xs, (g["Z"] - c0 * xs) / c1, ls="--", color=ACENTO, lw=1.6, label="Recta de Z en el óptimo")
        else:
            ax.plot([g["Z"] / c0] * 2, [0, L], ls="--", color=ACENTO, lw=1.6, label="Recta de Z en el óptimo")
    for q in g["V"]:
        es_opt = math.dist(q, g["mejor"]) < 1e-9
        ax.scatter(*q, s=110 if es_opt else 30, color=AMARILLO if es_opt else TINTA,
                   edgecolor=TINTA, linewidth=1.4 if es_opt else 0, zorder=5)
        ax.annotate(f"({fmt(q[0])}, {fmt(q[1])})\nZ = {fmt(g['Zf'](q))}", q, xytext=(7, 7),
                    textcoords="offset points", fontsize=8.5, color=TINTA)
    ax.set_xlabel("x₁")
    ax.set_ylabel("x₂")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#AEB7D6")
    ax.tick_params(colors=GRIS, labelsize=9)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    return fig


# ───────────────────────── Punto de conexión con TU motor ─────────────────────────


def resolver(p: dict, modo: str) -> dict:
    """Aquí se conecta el Gran M / simplex revisado propio.

    Contrato sugerido (lo que la interfaz sabe pintar):
        estado   : "óptimo" | "múltiples" | "no acotado" | "infactible" | "degenerado"
        x        : lista de Fraction (variables originales)
        Z        : Fraction
        holguras : lista de Fraction (holgura o exceso por restricción)
        pasos    : [dict(titulo, entra, razon, sale, pivote, tablero: DataFrame, piv: (fila, col))]
        sens     : dict(precios_sombra=..., costos_reducidos=..., rangos_c=..., rangos_b=...)
    Por ahora devuelve una vista previa (n = 2) con el método gráfico.
    """
    g = geometria(p) if p["n"] == 2 else None
    return dict(p=p, g=g, modo=modo)


# ───────────────────────── Interfaz ─────────────────────────
HERO = """
<div class="hero">
  <div>
    <div class="logo"><svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><polygon points="4,24 26,24 20,9 4,14" fill="#4B4DED"/><circle cx="20" cy="9" r="3.5" fill="#FFC93C"/></svg>Simplex Lab</div>
    <h1>Cada decisión del método, a la vista.</h1>
  </div>
  <svg viewBox="0 0 330 120" width="330" height="120" role="img" aria-label="El método recorre los vértices de la región factible hasta el óptimo">
    <polygon points="14,106 250,106 296,52 236,14 70,26 14,60" fill="#4B4DED" fill-opacity="0.16" stroke="#4B4DED" stroke-width="1.5"/>
    <polyline points="14,106 250,106 296,52" fill="none" stroke="#0E1B3D" stroke-width="1.6" stroke-dasharray="5 4"/>
    <g fill="#0E1B3D"><circle cx="14" cy="106" r="4.5"/><circle cx="250" cy="106" r="4.5"/></g>
    <circle cx="296" cy="52" r="9" fill="#FFC93C" stroke="#0E1B3D" stroke-width="1.6"/>
  </svg>
</div>
"""
st.markdown(HERO, unsafe_allow_html=True)

TITULOS = {
    "óptimo": ("Solución óptima", False),
    "múltiples": ("Óptimos múltiples", False),
    "no acotado": ("Solución no acotada", True),
    "infactible": ("Sin solución factible", True),
}


def chip(titulo: str, malo: bool) -> str:
    return f'<span class="estado{" mal" if malo else ""}">{titulo}</span>'


def mostrar(res: dict) -> None:
    p, g = res["p"], res["g"]
    t_sol, t_pasos, t_graf, t_sens = st.tabs(["Solución", "Paso a paso", "Gráfico", "Sensibilidad"])

    with t_sol:
        if g is None:
            st.info("Con más de dos variables la vista previa no está disponible. "
                    "Aquí aparecerá la solución de tu método.")
        else:
            titulo, malo = TITULOS[g["estado"]]
            if g["estado"] == "infactible":
                st.markdown(chip(titulo, malo), unsafe_allow_html=True)
                st.write("Las restricciones se contradicen: ningún punto las cumple todas a la vez.")
            elif g["estado"] == "no acotado":
                st.markdown(chip(titulo, malo), unsafe_allow_html=True)
                st.write("Z puede mejorar sin límite: la región factible está abierta en la dirección del objetivo.")
            else:
                x = g["mejor"]
                xs = "".join(f"<div><span>x{i + 1}</span><b>{fmt(v)}</b></div>" for i, v in enumerate(x))
                st.markdown(
                    f'{chip(titulo, malo)}<div class="zrow"><div class="zcard"><span>Z óptimo</span>'
                    f'<b>{fmt(g["Z"])}</b></div><div class="xs">{xs}</div></div>', unsafe_allow_html=True)
                if g["estado"] == "múltiples":
                    st.write("Hay más de un punto óptimo: todo el segmento entre los vértices óptimos da el mismo Z.")
                filas = []
                for i, (a, bb, s) in enumerate(zip(p["A"], p["b"], p["s"]), 1):
                    uso = float(a[0]) * x[0] + float(a[1]) * x[1]
                    if s == "≤":
                        filas.append((f"R{i}", fmt(uso), "Holgura", fmt(float(bb) - uso)))
                    elif s == "≥":
                        filas.append((f"R{i}", fmt(uso), "Exceso", fmt(uso - float(bb))))
                    else:
                        filas.append((f"R{i}", fmt(uso), "Igualdad", "0"))
                st.dataframe(pd.DataFrame(filas, columns=["Restricción", "Uso", "Tipo", "Valor"]),
                             hide_index=True, width="stretch")
            st.caption("Vista previa calculada con el método gráfico. Se reemplaza por tu Gran M.")

    with t_pasos:
        if res["modo"] == "Solución directa":
            st.info("Elegiste solución directa. Cambia a Paso a paso y vuelve a resolver para ver cada iteración.")
        else:
            st.caption("Maqueta de formato con el problema de Wyndor (Max 3x₁ + 5x₂). "
                       "Aquí van las iteraciones de tu método.")
            cab = ["Z", "x1", "x2", "s1", "s2", "s3", "LD"]
            T0 = pd.DataFrame([["1", "-3", "-5", "0", "0", "0", "0"], ["0", "1", "0", "1", "0", "0", "4"],
                               ["0", "0", "2", "0", "1", "0", "12"], ["0", "3", "2", "0", "0", "1", "18"]],
                              index=["Z", "s1", "s2", "s3"], columns=cab)
            T1 = pd.DataFrame([["1", "-3", "0", "0", "5/2", "0", "30"], ["0", "1", "0", "1", "0", "0", "4"],
                               ["0", "0", "1", "0", "1/2", "0", "6"], ["0", "3", "0", "0", "-1", "1", "6"]],
                              index=["Z", "s1", "x2", "s3"], columns=cab)
            pasos = [
                ("Iteración 0", "x2", "−5, el más negativo de la fila Z", "4/0 no aplica · 12/2 = 6 · 18/2 = 9",
                 "s2", "2", T0, ("s2", "x2")),
                ("Iteración 1", "x1", "−3, el único negativo de la fila Z", "4/1 = 4 · 6/0 no aplica · 6/3 = 2",
                 "s3", "3", T1, ("s3", "x1")),
            ]
            for i, (tit, ent, why, raz, sal, piv, tab, pos) in enumerate(pasos):
                with st.expander(tit, expanded=(i == 0)):
                    cl, cr = st.columns([1, 2.2])
                    cl.markdown(f"**Entra** {ent}  \n{why}")
                    cl.markdown(f"**Razón mínima**  \n{raz}")
                    cl.markdown(f"**Sale** {sal}  \n**Pivote** {piv}")
                    cr.dataframe(
                        tab.style.apply(
                            lambda d, f=pos[0], c=pos[1]: pd.DataFrame(
                                [[f"background-color:{AMARILLO};color:{TINTA};font-weight:700" if (r == f and k == c) else ""
                                  for k in d.columns] for r in d.index], index=d.index, columns=d.columns),
                            axis=None),
                        width="stretch")

    with t_graf:
        if g is None:
            st.info("El método gráfico solo aplica con dos variables. Este problema tiene "
                    f"{p['n']}: usa la pestaña Paso a paso.")
        elif g["estado"] == "infactible":
            st.warning("La región factible está vacía, no hay nada que graficar.")
        else:
            if g["estado"] == "no acotado":
                st.warning("La región se extiende sin límite en la dirección del objetivo; "
                           "se muestra recortada a la ventana.")
            st.pyplot(dibujar(p, g), width="stretch")

    with t_sens:
        st.caption("Maqueta de las tablas. Se llenan con la tabla final de tu método.")
        st.dataframe(pd.DataFrame({"Restricción": [f"R{i + 1}" for i in range(len(p["A"]))],
                                   "Precio sombra": "—", "Rango del lado derecho": "—"}),
                     hide_index=True, width="stretch")
        st.dataframe(pd.DataFrame({"Variable": cols(p["n"]), "Valor": "—", "Costo reducido": "—",
                                   "Rango del coeficiente": "—"}),
                     hide_index=True, width="stretch")


izq, der = st.columns([1, 1.45], gap="large")

with izq:
    with st.container(key="panel_izq"):
        st.markdown('<div class="ptitulo">Tu problema</div>', unsafe_allow_html=True)
        k1, k2 = st.columns([1.7, 1])
        k1.radio("Objetivo", ["Maximizar", "Minimizar"], key="sense", horizontal=True,
                 label_visibility="collapsed")
        k2.number_input("Variables", min_value=1, max_value=10, step=1, key="n", on_change=al_cambiar_n)
        st.selectbox("Cargar un ejemplo", [NINGUNO, *EJEMPLOS], key="ejemplo", on_change=al_elegir_ejemplo)

        n, ver = st.session_state.n, st.session_state.ver
        st.markdown('<div class="sec">Función objetivo</div>', unsafe_allow_html=True)
        c_edit = st.data_editor(
            st.session_state.c_df, key=f"c{ver}", hide_index=True, width="stretch",
            column_config={k: st.column_config.TextColumn(k, width="small") for k in cols(n)},
        )
        st.markdown('<div class="sec">Restricciones</div>', unsafe_allow_html=True)
        a_edit = st.data_editor(
            st.session_state.a_df, key=f"a{ver}", num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                **{k: st.column_config.TextColumn(k, width="small") for k in cols(n)},
                "Signo": st.column_config.SelectboxColumn("Signo", options=["≤", "≥", "="], width="small"),
                "Lado derecho": st.column_config.TextColumn("Lado derecho", width="small"),
            },
        )
        st.session_state._c_now, st.session_state._a_now = c_edit, a_edit
        st.caption("Acepta enteros, decimales y fracciones como 2/5. Agrega o quita restricciones desde la tabla.")

        modo = st.radio("Modo", ["Solución directa", "Paso a paso"], key="modo", horizontal=True,
                        label_visibility="collapsed")
        if st.button("Resolver", type="primary", width="stretch"):
            prob, errores = leer(c_edit, a_edit, n)
            if errores:
                st.session_state.pop("res", None)
                st.error("Revisa el problema antes de resolver:\n\n" + "\n".join(f"- {e}" for e in errores[:6]))
            else:
                st.session_state.res = resolver(prob, modo)

with der:
    with st.container(key="panel_der"):
        if "res" in st.session_state:
            mostrar(st.session_state.res)
        else:
            st.markdown('<div class="vacio">Elige un ejemplo o escribe tu problema y pulsa <b>Resolver</b>. '
                        'Aquí verás la solución, el paso a paso, el gráfico y la sensibilidad.</div>',
                        unsafe_allow_html=True)
