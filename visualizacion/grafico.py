"""Graphical method for two-variable linear programming problems.

This module is pure presentation logic: it computes the feasible region and
draws it, but it never imports Streamlit and never solves the problem with
Simplex. The canonical solution always comes from the optimization engine.
"""
from __future__ import annotations

import itertools
import math
from fractions import Fraction

import matplotlib.pyplot as plt
import numpy as np

ACENTO, TINTA, GRIS, AMARILLO = "#4B4DED", "#0E1B3D", "#5B6788", "#FFC93C"


def fmt(v) -> str:
    """Format a number as an exact fraction when one is close enough."""
    f = Fraction(float(v)).limit_denominator(1000)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def geometria(p: dict) -> dict:
    """Enumerate the vertices of the feasible region for a two-variable problem.

    Returns the feasible vertices ``V``, the clipped polygon used for drawing
    ``VB``, the optimum vertex ``mejor`` and the optimal value ``Z``.
    The state is one of ``infactible``, ``no acotado``, ``múltiples`` or ``óptimo``.
    """
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
    """Draw the feasible region, its vertices, and the objective line at the optimum."""
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
