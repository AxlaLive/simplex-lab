from __future__ import annotations
from fractions import Fraction
from motor.forma_estandar import preparar_forma_estandar

class CoeficienteM:
    """Representa un número de la forma a + b*M para aritmética exacta."""
    def __init__(self, regular: Fraction | int | float = 0, m_coeff: Fraction | int | float = 0):
        self.regular = Fraction(regular)
        self.m_coeff = Fraction(m_coeff)

    def __add__(self, otro: CoeficienteM | Fraction | int) -> CoeficienteM:
        if isinstance(otro, (Fraction, int)):
            return CoeficienteM(self.regular + Fraction(otro), self.m_coeff)
        return CoeficienteM(self.regular + otro.regular, self.m_coeff + otro.m_coeff)

    def __sub__(self, otro: CoeficienteM | Fraction | int) -> CoeficienteM:
        if isinstance(otro, (Fraction, int)):
            return CoeficienteM(self.regular - Fraction(otro), self.m_coeff)
        return CoeficienteM(self.regular - otro.regular, self.m_coeff - otro.m_coeff)

    def __mul__(self, escalar: Fraction | int) -> CoeficienteM:
        e = Fraction(escalar)
        return CoeficienteM(self.regular * e, self.m_coeff * e)

    def __neg__(self) -> CoeficienteM:
        return CoeficienteM(-self.regular, -self.m_coeff)

    def es_negativo(self, M_valor: float = 1000000.0) -> bool:
        val_total = float(self.regular) + float(self.m_coeff) * M_valor
        return val_total < -1e-9

    def es_positivo(self, M_valor: float = 1000000.0) -> bool:
        val_total = float(self.regular) + float(self.m_coeff) * M_valor
        return val_total > 1e-9

    def __repr__(self) -> str:
        r_str = str(self.regular)
        if self.m_coeff == 0:
            return r_str
        m_str = f"{self.m_coeff}M" if self.m_coeff != 1 else "M"
        if self.regular == 0:
            return m_str
        signo = "+" if self.m_coeff > 0 else ""
        return f"{r_str} {signo} {m_str}"


def fraction_to_str(f: Fraction) -> str:
    """Convierte una fracción a formato de texto legible (ej: '2/5' o '4')."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def resolver_gran_m(problema: dict) -> dict:
    """Resuelve un problema de Programación Lineal usando el método de la Gran M."""
    prob = preparar_forma_estandar(problema)
    sense = prob["sense"]
    c_orig = prob["c"]
    A = prob["A"]
    s_list = prob["s"]
    b = prob["b"]
    n = prob["n"]
    m = len(b)

    nombres_cols = [f"x{j+1}" for j in range(n)]

    slack_count = 0
    surplus_count = 0
    art_count = 0

    restricciones_info = []
    for i in range(m):
        signo = s_list[i]
        if signo == "≤":
            slack_count += 1
            restricciones_info.append(("slack", slack_count))
        elif signo == "≥":
            surplus_count += 1
            art_count += 1
            restricciones_info.append(("surplus_art", surplus_count, art_count))
        elif signo == "=":
            art_count += 1
            restricciones_info.append(("art", art_count))

    for i in range(slack_count):
        nombres_cols.append(f"s{i+1}")
    for i in range(surplus_count):
        nombres_cols.append(f"e{i+1}")
    for i in range(art_count):
        nombres_cols.append(f"a{i+1}")

    total_cols = n + slack_count + surplus_count + art_count

    A_amp = [[Fraction(0) for _ in range(total_cols)] for _ in range(m)]

    for i in range(m):
        for j in range(n):
            A_amp[i][j] = A[i][j]

    slack_idx = 0
    surplus_idx = 0
    art_idx = 0
    base_indices = []

    for i, info in enumerate(restricciones_info):
        tipo = info[0]
        if tipo == "slack":
            col = n + slack_idx
            A_amp[i][col] = Fraction(1)
            base_indices.append(col)
            slack_idx += 1
        elif tipo == "surplus_art":
            surplus_col = n + slack_count + surplus_idx
            art_col = n + slack_count + surplus_count + art_idx
            A_amp[i][surplus_col] = Fraction(-1)
            A_amp[i][art_col] = Fraction(1)
            base_indices.append(art_col)
            surplus_idx += 1
            art_idx += 1
        elif tipo == "art":
            art_col = n + slack_count + surplus_count + art_idx
            A_amp[i][art_col] = Fraction(1)
            base_indices.append(art_col)
            art_idx += 1

    c_tab = []
    for j in range(total_cols):
        if j < n:
            val = c_orig[j] if sense == "Maximizar" else -c_orig[j]
            c_tab.append(CoeficienteM(val, 0))
        elif j >= n + slack_count + surplus_count:
            c_tab.append(CoeficienteM(0, -1))
        else:
            c_tab.append(CoeficienteM(0, 0))

    b_tab = [Fraction(val) for val in b]

    fila_z_reg = [Fraction(0) for _ in range(total_cols)]
    fila_z_m = [Fraction(0) for _ in range(total_cols)]

    def recalcular_fila_z():
        for j in range(total_cols):
            reg_sum = Fraction(0)
            m_sum = Fraction(0)
            for i in range(m):
                var_base_idx = base_indices[i]
                c_b_reg = c_tab[var_base_idx].regular
                c_b_m = c_tab[var_base_idx].m_coeff
                
                reg_sum += c_b_reg * A_amp[i][j]
                m_sum += c_b_m * A_amp[i][j]
            
            fila_z_reg[j] = reg_sum - c_tab[j].regular
            fila_z_m[j] = m_sum - c_tab[j].m_coeff

    recalcular_fila_z()

    max_iter = 100
    pasos = []

    def construir_tablero_actual() -> list[list[str]]:
        z_row_strs = ["1"]
        for j in range(total_cols):
            reg = fila_z_reg[j]
            m_c = fila_z_m[j]
            if m_c != 0:
                m_str = f"{fraction_to_str(m_c)}M" if m_c != 1 else "M"
                signo = "+" if reg > 0 else ""
                r_str = f"{fraction_to_str(reg)}" if reg != 0 else ""
                z_row_strs.append(f"{r_str}{signo}{m_str}" if r_str else m_str)
            else:
                z_row_strs.append(fraction_to_str(reg))
        
        ld_z_reg = sum(b_tab[i] * c_tab[base_indices[i]].regular for i in range(m))
        ld_z_m = sum(b_tab[i] * c_tab[base_indices[i]].m_coeff for i in range(m))
        if ld_z_m != 0:
            m_str = f"{fraction_to_str(ld_z_m)}M" if ld_z_m != 1 else "M"
            signo = "+" if ld_z_reg > 0 else ""
            r_str = f"{fraction_to_str(ld_z_reg)}" if ld_z_reg != 0 else ""
            z_row_strs.append(f"{r_str}{signo}{m_str}" if r_str else m_str)
        else:
            z_row_strs.append(fraction_to_str(ld_z_reg))
        
        tab = [z_row_strs]
        for i in range(m):
            row_strs = ["0"]
            for j in range(total_cols):
                row_strs.append(fraction_to_str(A_amp[i][j]))
            row_strs.append(fraction_to_str(b_tab[i]))
            tab.append(row_strs)
        return tab

    for iteracion in range(max_iter):
        cols_snapshot = ["Z"] + nombres_cols + ["LD"]
        filas_snapshot = ["Z"] + [nombres_cols[base_indices[i]] for i in range(m)]
        tablero_snapshot = construir_tablero_actual()

        candidato_col = -1
        min_val_m = Fraction(0)
        min_val_reg = Fraction(0)

        for j in range(total_cols):
            if j in base_indices:
                continue
            
            m_c = fila_z_m[j]
            reg_c = fila_z_reg[j]
            
            if CoeficienteM(reg_c, m_c).es_negativo():
                if m_c < min_val_m or (m_c == min_val_m and reg_c < min_val_reg):
                    min_val_m = m_c
                    min_val_reg = reg_c
                    candidato_col = j

        if candidato_col == -1:
            break

        var_entrante = nombres_cols[candidato_col]
        candidato_fila = -1
        min_razon = None
        razones_strs = []

        for i in range(m):
            val_a = A_amp[i][candidato_col]
            nombre_fila_actual = nombres_cols[base_indices[i]]
            if val_a > 0:
                razon = b_tab[i] / val_a
                razones_strs.append(f"{nombre_fila_actual}: {fraction_to_str(b_tab[i])}/{fraction_to_str(val_a)} = {fraction_to_str(razon)}")
                if min_razon is None or razon < min_razon:
                    min_razon = razon
                    candidato_fila = i
            else:
                razones_strs.append(f"{nombre_fila_actual}: no aplica (a <= 0)")

        if candidato_fila == -1:
            tiene_art_en_base = any(base_indices[i] >= n + slack_count + surplus_count and b_tab[i] > 1e-9 for i in range(m))
            if tiene_art_en_base:
                return {"estado": "infactible", "x": [], "Z": Fraction(0), "holguras": {}, "pasos": pasos}
            return {"estado": "no_acotado", "x": [], "Z": Fraction(0), "holguras": {}, "pasos": pasos}

        var_saliente = nombres_cols[base_indices[candidato_fila]]
        
        pasos.append({
            "iteracion": iteracion,
            "columnas": cols_snapshot,
            "filas": filas_snapshot,
            "tablero": tablero_snapshot,
            "valores": tablero_snapshot,
            "entra": var_entrante,
            "razones": razones_strs,
            "sale": var_saliente,
            "pivote": {"fila": var_saliente, "columna": var_entrante},
            "explicacion": f"Entra {var_entrante} porque su coeficiente en la fila Z es el más negativo. Sale {var_saliente} por la prueba de la razón mínima."
        })

        pivote = A_amp[candidato_fila][candidato_col]
        for j in range(total_cols):
            A_amp[candidato_fila][j] /= pivote
        b_tab[candidato_fila] /= pivote

        for i in range(m):
            if i != candidato_fila:
                factor = A_amp[i][candidato_col]
                for j in range(total_cols):
                    A_amp[i][j] -= factor * A_amp[candidato_fila][j]
                b_tab[i] -= factor * b_tab[candidato_fila]

        base_indices[candidato_fila] = candidato_col
        recalcular_fila_z()

    for i in range(m):
        var_idx = base_indices[i]
        if var_idx >= n + slack_count + surplus_count:
            if b_tab[i] > 1e-9:
                return {"estado": "infactible", "x": [], "Z": Fraction(0), "holguras": {}, "pasos": pasos}

    x_result = [Fraction(0)] * n
    for i in range(m):
        var_idx = base_indices[i]
        if var_idx < n:
            x_result[var_idx] = b_tab[i]

    holguras_dict = {}
    for i in range(m):
        signo = s_list[i]
        val_lhs = sum(A[i][j] * x_result[j] for j in range(n))
        if signo == "≤":
            holguras_dict[f"s{i+1}"] = b[i] - val_lhs
        elif signo == "≥":
            holguras_dict[f"e{i+1}"] = val_lhs - b[i]

    z_val = sum(c_orig[j] * x_result[j] for j in range(n))
    return {
        "estado": "optimo",
        "x": x_result,
        "Z": z_val,
        "holguras": holguras_dict,
        "pasos": pasos
    }