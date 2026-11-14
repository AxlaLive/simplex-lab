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
        nombres_cols.append(f"R{i+1}")

    total_cols = n + slack_count + surplus_count + art_count
    
    A_amp = [[Fraction(0) for _ in range(total_cols)] for _ in range(m)]
    
    for i in range(m):
        for j in range(n):
            A_amp[i][j] = A[i][j]
            
    col_idx = n
    base_indices = []
    
    for i, info in enumerate(restricciones_info):
        tipo = info[0]
        if tipo == "slack":
            A_amp[i][col_idx] = Fraction(1)
            base_indices.append(col_idx)
            col_idx += 1
        elif tipo == "surplus_art":
            A_amp[i][col_idx] = Fraction(-1)
            col_idx += 1
            A_amp[i][col_idx] = Fraction(1)
            base_indices.append(col_idx)
            col_idx += 1
        elif tipo == "art":
            A_amp[i][col_idx] = Fraction(1)
            base_indices.append(col_idx)
            col_idx += 1

    c_tab = []
    for j in range(total_cols):
        if j < n:
            val = c_orig[j] if sense == "Maximizar" else -c_orig[j]
            c_tab.append(CoeficienteM(val, 0))
        elif j >= n + slack_count + surplus_count:
            m_val = Fraction(1) if sense == "Maximizar" else Fraction(-1)
            c_tab.append(CoeficienteM(0, m_val))
        else:
            c_tab.append(CoeficienteM(0, 0))

    b_tab = [Fraction(val) for val in b]

    fila_z_reg = [Fraction(0) for _ in range(total_cols)]
    fila_z_m = [Fraction(0) for _ in range(total_cols)]

    for j in range(total_cols):
        reg_sum = Fraction(0)
        m_sum = Fraction(0)
        for i in range(m):
            var_base_idx = base_indices[i]
            c_b_reg = c_tab[var_base_idx].regular
            c_b_m = c_tab[var_base_idx].m_coeff
            
            reg_sum += c_b_reg * A_amp[i][j]
            m_sum += c_b_m * A_amp[i][j]
        
        reg_neto = reg_sum - c_tab[j].regular
        m_neto = m_sum - c_tab[j].m_coeff
        fila_z_reg[j] = reg_neto
        fila_z_m[j] = m_neto  # <-- Asignación corregida

    max_iter = 100
    pasos = []

    for iteracion in range(max_iter):
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

        candidato_fila = -1
        min_razon = None

        for i in range(m):
            val_a = A_amp[i][candidato_col]
            if val_a > 0:
                razon = b_tab[i] / val_a
                if min_razon is None or razon < min_razon:
                    min_razon = razon
                    candidato_fila = i

        if candidato_fila == -1:
            return {"estado": "no acotado", "x": [], "Z": Fraction(0), "holguras": [], "pasos": pasos}

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

        # Actualizar fila Z en el pivoteo
        factor_z_reg = fila_z_reg[candidato_col]
        factor_z_m = fila_z_m[candidato_col]
        
        for j in range(total_cols):
            fila_z_reg[j] -= factor_z_reg * A_amp[candidato_fila][j]
            fila_z_m[j] -= factor_z_m * A_amp[candidato_fila][j]

        base_indices[candidato_fila] = candidato_col

    x_result = [Fraction(0)] * n
    for i in range(m):
        var_idx = base_indices[i]
        if var_idx < n:
            x_result[var_idx] = b_tab[i]

    for i in range(m):
        var_idx = base_indices[i]
        if var_idx >= n + slack_count + surplus_count:
            if b_tab[i] > 1e-9:
                return {"estado": "infactible", "x": [], "Z": Fraction(0), "holguras": [], "pasos": []}

    z_val = Fraction(0)
    for j in range(n):
        z_val += c_orig[j] * x_result[j]

    return {
        "estado": "óptimo",
        "x": x_result,
        "Z": z_val if sense == "Maximizar" else -z_val,
        "holguras": [],
        "pasos": pasos
    }