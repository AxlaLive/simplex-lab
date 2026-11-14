from __future__ import annotations
from fractions import Fraction

def preparar_forma_estandar(problema: dict) -> dict:
    """Convierte el problema de PL a su forma estándar para el método de la Gran M.
    
    problema = {
        "sense": "Maximizar" o "Minimizar",
        "c": [Fraction, ...],
        "A": [[Fraction, ...], ...],
        "s": ["≤", "≥", "=", ...],
        "b": [Fraction, ...],
        "n": int
    }
    """
    sense = problema["sense"]
    c_orig = [Fraction(v) for v in problema["c"]]
    A_orig = [[Fraction(v) for v in row] for row in problema["A"]]
    s_list = problema["s"]
    b_orig = [Fraction(v) for v in problema["b"]]
    n = problema["n"]
    
    m = len(b_orig)
    
    # Asegurar lado derecho (b) no negativo multiplicando por -1 si es necesario
    A_mod = []
    b_mod = []
    s_mod = []
    
    for i in range(m):
        a_row = list(A_orig[i])
        b_val = b_orig[i]
        signo = s_list[i]
        
        if b_val < 0:
            # Invertir la desigualdad/igualdad y multiplicar la fila por -1
            a_row = [-val for val in a_row]
            b_val = -b_val
            if signo == "≤":
                signo = "≥"
            elif signo == "≥":
                signo = "≤"
            # '=' se queda igual pero cambia de signo el b
            
        A_mod.append(a_row)
        b_mod.append(b_val)
        s_mod.append(signo)

    # Contar cuántas variables de exceso y artificiales necesitamos
    # Estructura de variables: [x_orig (n), holguras/excesos, artificiales]
    # Por simplicidad en la primera versión, construimos las matrices ampliadas.
    
    return {
        "sense": sense,
        "c": c_orig,
        "A": A_mod,
        "s": s_mod,
        "b": b_mod,
        "n": n
    }