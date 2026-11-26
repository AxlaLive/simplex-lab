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

import math
from fractions import Fraction

import pandas as pd
import streamlit as st

from motor.gran_m import resolver_gran_m
from motor.sensibilidad import analizar_sensibilidad
from visualizacion.grafico import dibujar, fmt, geometria
from visualizacion.tableros import razones_texto, render as render_tablero

st.set_page_config(page_title="Simplex Lab", page_icon="📐", layout="wide")

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
    primero = next(iter(EJEMPLOS))
    _poner(EJEMPLOS[primero])
    st.session_state.ejemplo = primero

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


# ───────────────────────── Punto de conexión con TU motor ─────────────────────────


def resolver(p: dict, modo: str) -> dict:
    """Conecta la interfaz con el motor Gran M.

    Devuelve un diccionario con:
        p        : el problema tal como se ingresó
        g        : vista geométrica (solo n = 2) para la pestaña Gráfico
        m        : resultado del motor, o None si falló
        error    : mensaje de la excepción, o None
        modo     : "Solución directa" | "Paso a paso"
    """
    g = geometria(p) if p["n"] == 2 else None
    m, error = None, None
    try:
        m = resolver_gran_m(p)
    except Exception as exc:  # el motor todavía no cubre todas las entradas
        error = f"{type(exc).__name__}: {exc}"
    return dict(p=p, g=g, m=m, error=error, modo=modo)


# El plan fija los estados en ASCII sin espacios, el motor hoy devuelve
# variantes con tilde. El adaptador absorbe la diferencia para que la
# interfaz funcione antes y después de que el motor se alinee.
ESTADOS = {
    "optimo": "óptimo",
    "óptimo": "óptimo",
    "multiples": "múltiples",
    "múltiples": "múltiples",
    "no_acotado": "no acotado",
    "no acotado": "no acotado",
    "infactible": "infactible",
    "degenerado": "degenerado",
}


def estado_visible(bruto: str) -> str:
    """Traduce el estado del motor a la clave que entiende la interfaz."""
    return ESTADOS.get(bruto, bruto)



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
    "degenerado": ("Solución degenerada", False),
    "no acotado": ("Solución no acotada", True),
    "infactible": ("Sin solución factible", True),
}


def chip(titulo: str, malo: bool) -> str:
    return f'<span class="estado{" mal" if malo else ""}">{titulo}</span>'


def tabla_restricciones(p: dict, x: list) -> pd.DataFrame:
    """Evalúa cada restricción en la solución y calcula holgura o exceso."""
    filas = []
    for i, (a, bb, s) in enumerate(zip(p["A"], p["b"], p["s"]), 1):
        uso = sum(float(aj) * float(xj) for aj, xj in zip(a, x))
        if s == "≤":
            filas.append((f"R{i}", fmt(uso), "Holgura", fmt(float(bb) - uso)))
        elif s == "≥":
            filas.append((f"R{i}", fmt(uso), "Exceso", fmt(uso - float(bb))))
        else:
            filas.append((f"R{i}", fmt(uso), "Igualdad", "0"))
    return pd.DataFrame(filas, columns=["Restricción", "Uso", "Tipo", "Valor"])


def bloque_motor(p: dict, m: dict) -> None:
    """Pinta el resultado devuelto por el motor Gran M."""
    estado = estado_visible(m["estado"])
    titulo, malo = TITULOS.get(estado, (estado, False))
    st.markdown(chip(titulo, malo), unsafe_allow_html=True)

    if estado == "infactible":
        st.write("Las restricciones se contradicen: ningún punto las cumple todas a la vez.")
        return
    if estado == "no acotado":
        st.write("Z puede mejorar sin límite: la región factible está abierta en la dirección del objetivo.")
        return

    x = m.get("x") or []
    xs = "".join(f"<div><span>x{i + 1}</span><b>{fmt(v)}</b></div>" for i, v in enumerate(x))
    st.markdown(
        f'<div class="zrow"><div class="zcard"><span>Z óptimo</span>'
        f'<b>{fmt(m["Z"])}</b></div><div class="xs">{xs}</div></div>', unsafe_allow_html=True)
    if estado == "múltiples":
        st.write("Hay más de un punto óptimo: todo el segmento entre los vértices óptimos da el mismo Z.")
    if estado == "degenerado":
        st.write("Hay una variable básica en cero: el método puede dar pasos sin mejorar Z.")
    st.dataframe(tabla_restricciones(p, x), hide_index=True, width="stretch")


def bloque_preview(p: dict, g) -> None:
    """Vista previa con el método gráfico, para cuando el motor no responde."""
    if g is None:
        st.info("Con más de dos variables la vista previa no está disponible. "
                "Aquí aparecerá la solución de tu método.")
        return
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
        st.dataframe(tabla_restricciones(p, x), hide_index=True, width="stretch")
    st.caption("Vista previa calculada con el método gráfico.")


def iteraciones(pasos: list) -> None:
    """Dibuja una lista de pasos con su tablero y su pivote resaltado."""
    for i, paso in enumerate(pasos):
        with st.expander(f"Iteración {paso['iteracion']}", expanded=(i == 0)):
            cl, cr = st.columns([1, 2.2])
            cl.markdown(f"**Entra** {paso['entra']}  \n{paso['explicacion']}")
            cl.markdown(f"**Razón mínima**  \n{razones_texto(paso)}")
            pivote = paso.get("pivote") or {}
            cl.markdown(f"**Sale** {paso['sale']}  \n"
                        f"**Pivote** {pivote.get('fila', '—')} / {pivote.get('columna', '—')}")
            cr.dataframe(render_tablero(paso), width="stretch")


def mostrar(res: dict) -> None:
    p, g = res["p"], res["g"]
    t_sol, t_pasos, t_graf, t_sens = st.tabs(["Solución", "Paso a paso", "Gráfico", "Sensibilidad"])

    with t_sol:
        if res["m"] is not None:
            bloque_motor(p, res["m"])
            if not (res["m"].get("pasos") or []):
                st.caption("El motor todavía no devuelve el registro de iteraciones.")
        else:
            if res["error"]:
                st.error("El motor todavía no puede resolver este problema.")
                st.code(res["error"], language="text")
            bloque_preview(p, g)

    with t_pasos:
        pasos = (res["m"] or {}).get("pasos") or []
        if res["modo"] == "Solución directa":
            st.info("Elegiste solución directa. Cambia a Paso a paso y vuelve a resolver para ver cada iteración.")
        elif pasos:
            iteraciones(pasos)
        else:
            st.info("El motor no devolvió iteraciones para este problema.")

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
        if res["m"] is None:
            st.info("No se pudo realizar el análisis porque el motor no devolvió una solución.")
        else:
            try:
                sensibilidad = analizar_sensibilidad(p, res["m"])
                for advertencia in sensibilidad["advertencias"]:
                    st.warning(advertencia)
                if res["m"].get("estado") != "optimo" or not sensibilidad["disponible"]:
                    st.info(
                        "El análisis de sensibilidad no está disponible. "
                        + sensibilidad["mensaje"]
                    )
                else:
                    def formato_sensibilidad(valor, es_minimo: bool = False) -> str:
                        if valor is None:
                            return "−∞" if es_minimo else "+∞"
                        if isinstance(valor, Fraction):
                            if valor.denominator == 1:
                                return str(valor.numerator)
                            return f"{valor.numerator}/{valor.denominator}"
                        return str(valor)

                    if sensibilidad["optimos_multiples"]:
                        st.info("Se detectaron soluciones óptimas múltiples.")

                    st.caption(
                        "Los rangos se calculan variando un parámetro a la vez y manteniendo "
                        "los demás constantes; corresponden a la base actual."
                    )
                    st.subheader("Variables")
                    columnas_variables = [
                        "Variable",
                        "Valor óptimo",
                        "Costo reducido",
                        "Coeficiente objetivo",
                        "Mínimo",
                        "Máximo",
                    ]
                    tabla_variables = pd.DataFrame(
                        [
                            {
                                "Variable": variable["variable"],
                                "Valor óptimo": formato_sensibilidad(variable["valor_optimo"]),
                                "Costo reducido": formato_sensibilidad(variable["costo_reducido"]),
                                "Coeficiente objetivo": formato_sensibilidad(variable["coeficiente_objetivo"]),
                                "Mínimo": formato_sensibilidad(variable["minimo"], es_minimo=True),
                                "Máximo": formato_sensibilidad(variable["maximo"]),
                            }
                            for variable in sensibilidad["variables"]
                        ],
                        columns=columnas_variables,
                    )
                    st.dataframe(tabla_variables, hide_index=True, width="stretch")
                    for variable in sensibilidad["variables"]:
                        st.write(f"**{variable['variable']}:** {variable['interpretacion']}")

                    st.subheader("Restricciones")
                    columnas_restricciones = [
                        "Restricción",
                        "Precio sombra",
                        "Lado derecho",
                        "Mínimo",
                        "Máximo",
                    ]
                    tabla_restricciones_sensibilidad = pd.DataFrame(
                        [
                            {
                                "Restricción": restriccion["restriccion"],
                                "Precio sombra": formato_sensibilidad(restriccion["precio_sombra"]),
                                "Lado derecho": formato_sensibilidad(restriccion["lado_derecho"]),
                                "Mínimo": formato_sensibilidad(restriccion["minimo"], es_minimo=True),
                                "Máximo": formato_sensibilidad(restriccion["maximo"]),
                            }
                            for restriccion in sensibilidad["restricciones"]
                        ],
                        columns=columnas_restricciones,
                    )
                    st.dataframe(tabla_restricciones_sensibilidad, hide_index=True, width="stretch")
                    for restriccion in sensibilidad["restricciones"]:
                        st.write(
                            f"**{restriccion['restriccion']}:** {restriccion['interpretacion']}"
                        )
            except Exception:
                st.error("No se pudo mostrar el análisis de sensibilidad.")


izq, der = st.columns([1, 1.45], gap="large")

with izq:
    with st.container(key="panel_izq"):
        st.markdown('<div class="ptitulo">Tu problema</div>', unsafe_allow_html=True)
        k1, k2 = st.columns([1.7, 1])
        k1.radio("Objetivo", ["Maximizar", "Minimizar"], key="sense", horizontal=True,
                 label_visibility="collapsed")
        k2.number_input("Variables", min_value=1, max_value=10, step=1, key="n", on_change=al_cambiar_n)
        st.selectbox("Cargar un ejemplo", list(EJEMPLOS), key="ejemplo", on_change=al_elegir_ejemplo)

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
            st.markdown('<div class="vacio">Ajusta el problema o carga otro ejemplo y pulsa <b>Resolver</b>. '
                        'Aquí verás la solución, el paso a paso, el gráfico y la sensibilidad.</div>',
                        unsafe_allow_html=True)
