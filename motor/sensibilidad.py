from __future__ import annotations

from fractions import Fraction


def _no_disponible(mensaje: str) -> dict:
    return {
        "disponible": False,
        "mensaje": mensaje,
        "advertencias": [],
        "degenerado": False,
        "optimos_multiples": False,
        "variables": [],
        "restricciones": [],
    }


def _a_fraccion(valor: object) -> Fraction | None:
    if isinstance(valor, bool):
        return None
    try:
        return Fraction(str(valor))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None


def _lista_fracciones(valores: object) -> list[Fraction] | None:
    if not isinstance(valores, (list, tuple)):
        return None
    convertidos = [_a_fraccion(valor) for valor in valores]
    if any(valor is None for valor in convertidos):
        return None
    return [valor for valor in convertidos if valor is not None]


def _intersectar_desigualdad(
    minimo: Fraction | None,
    maximo: Fraction | None,
    constante: Fraction,
    pendiente: Fraction,
) -> tuple[Fraction | None, Fraction | None] | None:
    if pendiente == 0:
        if constante < 0:
            return None
    elif pendiente > 0:
        limite = -constante / pendiente
        minimo = limite if minimo is None else max(minimo, limite)
    else:
        limite = -constante / pendiente
        maximo = limite if maximo is None else min(maximo, limite)

    if minimo is not None and maximo is not None and minimo > maximo:
        return None
    return minimo, maximo


def _fraccion_texto(valor: Fraction) -> str:
    if valor.denominator == 1:
        return str(valor.numerator)
    return f"{valor.numerator}/{valor.denominator}"


def _limite_texto(valor: Fraction | None, es_minimo: bool) -> str:
    if valor is None:
        return "−∞" if es_minimo else "+∞"
    return _fraccion_texto(valor)


def analizar_sensibilidad(problema_original: dict, resultado_motor: dict) -> dict:
    """Analiza rangos de sensibilidad directamente desde el tableau final."""
    if not isinstance(problema_original, dict) or not isinstance(resultado_motor, dict):
        return _no_disponible("Se requieren diccionarios válidos del problema y del resultado del motor.")
    if resultado_motor.get("estado") != "optimo":
        return _no_disponible("El análisis solo está disponible cuando el estado del motor es optimo.")
    if "tableau_final" not in resultado_motor:
        return _no_disponible("El resultado del motor no contiene tableau_final.")

    campos_problema = ("sense", "c", "A", "s", "b", "n")
    campos_resultado = ("x", "Z")
    campos_tableau = (
        "filas",
        "columnas",
        "tablero_texto",
        "fila_z_regular",
        "fila_z_m",
        "filas_restricciones",
        "variables_basicas",
        "indices_basicos",
        "restricciones_info",
        "ld_z_regular",
        "ld_z_m",
    )
    faltantes = [campo for campo in campos_problema if campo not in problema_original]
    faltantes.extend(campo for campo in campos_resultado if campo not in resultado_motor)
    tableau = resultado_motor["tableau_final"]
    if not isinstance(tableau, dict):
        return _no_disponible("tableau_final debe ser un diccionario.")
    faltantes.extend(campo for campo in campos_tableau if campo not in tableau)
    if faltantes:
        return _no_disponible(f"Faltan campos necesarios: {', '.join(faltantes)}.")

    sense = problema_original["sense"]
    if sense not in ("Maximizar", "Minimizar"):
        return _no_disponible("El sentido de optimización debe ser Maximizar o Minimizar.")
    sigma = Fraction(1) if sense == "Maximizar" else Fraction(-1)

    n = problema_original["n"]
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        return _no_disponible("El número de variables originales no es válido.")

    costos = _lista_fracciones(problema_original["c"])
    lados_derechos = _lista_fracciones(problema_original["b"])
    matriz_original = problema_original["A"]
    signos = problema_original["s"]
    if costos is None or len(costos) != n:
        return _no_disponible("La cantidad de coeficientes de la función objetivo no coincide con n.")
    if not isinstance(matriz_original, (list, tuple)) or not isinstance(signos, (list, tuple)):
        return _no_disponible("A y s deben ser secuencias.")
    if lados_derechos is None or len(matriz_original) != len(lados_derechos) or len(signos) != len(lados_derechos):
        return _no_disponible("Las dimensiones de A, s y b no coinciden.")

    for fila in matriz_original:
        coeficientes = _lista_fracciones(fila)
        if coeficientes is None or len(coeficientes) != n:
            return _no_disponible("Una fila de A no tiene la cantidad esperada de coeficientes.")
    if any(signo not in ("≤", "≥", "=") for signo in signos):
        return _no_disponible("Una restricción tiene un signo no reconocido.")
    m = len(lados_derechos)

    filas = tableau["filas"]
    columnas = tableau["columnas"]
    tablero_texto = tableau["tablero_texto"]
    filas_restricciones = tableau["filas_restricciones"]
    variables_basicas = tableau["variables_basicas"]
    indices_basicos = tableau["indices_basicos"]
    restricciones_info = tableau["restricciones_info"]
    if not all(isinstance(valor, (list, tuple)) for valor in (
        filas, columnas, tablero_texto, filas_restricciones,
        variables_basicas, indices_basicos, restricciones_info
    )):
        return _no_disponible("Las filas, columnas o metadatos del tableau tienen un formato inválido.")
    if len(filas_restricciones) != m or len(restricciones_info) != m:
        return _no_disponible("El número de filas del tableau no coincide con las restricciones originales.")
    if len(filas) != m + 1 or len(variables_basicas) != m or len(indices_basicos) != m:
        return _no_disponible("Las filas o la base del tableau tienen dimensiones incoherentes.")
    if len(columnas) < n + 2 or any(not isinstance(nombre, str) for nombre in columnas):
        return _no_disponible("Las columnas del tableau tienen un formato inválido.")
    if columnas[0] != "Z" or columnas[-1] != "LD":
        return _no_disponible("Las columnas del tableau no tienen el formato esperado.")

    nombres_variables = list(columnas[1:-1])
    total_columnas = len(nombres_variables)
    if len(set(columnas)) != len(columnas):
        return _no_disponible("Los nombres de las columnas del tableau están repetidos.")
    if nombres_variables[:n] != [f"x{j + 1}" for j in range(n)]:
        return _no_disponible("Las columnas de las variables originales no coinciden con el problema.")
    if len(set(nombres_variables)) != total_columnas:
        return _no_disponible("Hay nombres de variables repetidos en las columnas del tableau.")

    fila_z_regular = _lista_fracciones(tableau["fila_z_regular"])
    fila_z_m = _lista_fracciones(tableau["fila_z_m"])
    ld_z_regular = _a_fraccion(tableau["ld_z_regular"])
    ld_z_m = _a_fraccion(tableau["ld_z_m"])
    if fila_z_regular is None or fila_z_m is None or ld_z_regular is None or ld_z_m is None:
        return _no_disponible("La fila Z o sus lados derechos contienen valores no numéricos.")
    if len(fila_z_regular) != total_columnas or len(fila_z_m) != total_columnas:
        return _no_disponible("Las filas Z no coinciden con las columnas de variables.")

    rhs_basicos = []
    coeficientes_filas = []
    for fila in filas_restricciones:
        if not isinstance(fila, dict) or "coeficientes" not in fila or "lado_derecho" not in fila:
            return _no_disponible("Una fila de restricciones no contiene coeficientes y lado_derecho.")
        coeficientes = _lista_fracciones(fila["coeficientes"])
        rhs = _a_fraccion(fila["lado_derecho"])
        if coeficientes is None or len(coeficientes) != total_columnas or rhs is None:
            return _no_disponible("Los coeficientes o el lado derecho de una fila tienen dimensiones inválidas.")
        coeficientes_filas.append(coeficientes)
        rhs_basicos.append(rhs)

    if len(tablero_texto) != m + 1 or any(
        not isinstance(fila, (list, tuple))
        or len(fila) != len(columnas)
        or any(not isinstance(valor, str) for valor in fila)
        for fila in tablero_texto
    ):
        return _no_disponible("tablero_texto no coincide con las dimensiones del tableau.")
    if any(not isinstance(nombre, str) for nombre in filas):
        return _no_disponible("Los nombres de las filas del tableau deben ser texto.")

    indices = []
    for indice in indices_basicos:
        if not isinstance(indice, int) or isinstance(indice, bool) or not 0 <= indice < total_columnas:
            return _no_disponible("Un índice básico está fuera de las columnas de variables.")
        indices.append(indice)
    if len(set(indices)) != len(indices):
        return _no_disponible("La base contiene índices repetidos.")
    if any(not isinstance(nombre, str) for nombre in variables_basicas):
        return _no_disponible("Los nombres de las variables básicas son inválidos.")
    nombres_base_esperados = [nombres_variables[indice] for indice in indices]
    if list(variables_basicas) != nombres_base_esperados or list(filas) != ["Z"] + nombres_base_esperados:
        return _no_disponible("Los nombres de las filas no coinciden con los índices de la base.")

    signos_estandarizados = []
    for signo, rhs in zip(signos, lados_derechos):
        if rhs < 0 and signo == "≤":
            signo = "≥"
        elif rhs < 0 and signo == "≥":
            signo = "≤"
        signos_estandarizados.append(signo)

    info_esperada = []
    contador_holguras = 0
    contador_excesos = 0
    contador_artificiales = 0
    for signo in signos_estandarizados:
        if signo == "≤":
            contador_holguras += 1
            info_esperada.append(("slack", contador_holguras))
        elif signo == "≥":
            contador_excesos += 1
            contador_artificiales += 1
            info_esperada.append(("surplus_art", contador_excesos, contador_artificiales))
        else:
            contador_artificiales += 1
            info_esperada.append(("art", contador_artificiales))
    try:
        info_normalizada = [tuple(info) for info in restricciones_info]
    except TypeError:
        return _no_disponible("restricciones_info contiene una entrada inválida.")
    if info_normalizada != info_esperada:
        return _no_disponible("restricciones_info no corresponde a los signos de las restricciones.")

    nombres_esperados = (
        [f"x{j + 1}" for j in range(n)]
        + [f"s{j + 1}" for j in range(contador_holguras)]
        + [f"e{j + 1}" for j in range(contador_excesos)]
        + [f"a{j + 1}" for j in range(contador_artificiales)]
    )
    if nombres_variables != nombres_esperados:
        return _no_disponible("Las columnas de holgura, exceso o artificiales no coinciden con restricciones_info.")

    indice_por_nombre = {nombre: indice for indice, nombre in enumerate(nombres_variables)}
    columnas_positivas = []
    for info in info_normalizada:
        if info[0] == "slack":
            nombre = f"s{info[1]}"
        elif info[0] == "surplus_art":
            nombre = f"a{info[2]}"
        else:
            nombre = f"a{info[1]}"
        columnas_positivas.append(indice_por_nombre[nombre])

    artificiales = {
        indice for indice, nombre in enumerate(nombres_variables)
        if nombre.startswith("a") and nombre[1:].isdigit()
    }
    if any(indice in artificiales for indice in indices):
        return _no_disponible(
            "La base conserva variables artificiales; no se puede garantizar un análisis de sensibilidad fiable con esa base."
        )

    if any(rhs < 0 for rhs in rhs_basicos):
        return _no_disponible("El tableau no es factible: una variable básica tiene lado derecho negativo.")
    for fila_indice, fila in enumerate(coeficientes_filas):
        for base_fila, indice in enumerate(indices):
            esperado = Fraction(1) if fila_indice == base_fila else Fraction(0)
            if fila[indice] != esperado:
                return _no_disponible("Las columnas básicas no forman una identidad en las filas de restricciones.")
    if any(fila_z_regular[indice] != 0 or fila_z_m[indice] != 0 for indice in indices):
        return _no_disponible("La fila Z no es coherente con la base indicada.")
    if any(fila_z_m[indice] != 0 for indice in range(total_columnas) if indice not in artificiales):
        return _no_disponible("La fila Z contiene coeficientes de M en columnas no artificiales.")
    if any(
        fila_z_regular[indice] < 0
        for indice in range(total_columnas)
        if indice not in indices and indice not in artificiales
    ):
        return _no_disponible("La fila Z indica que la solución todavía puede mejorarse.")

    valores_variables = [Fraction(0) for _ in range(n)]
    for fila_indice, indice in enumerate(indices):
        if indice < n:
            valores_variables[indice] = rhs_basicos[fila_indice]
    valores_motor = _lista_fracciones(resultado_motor["x"])
    valor_motor = _a_fraccion(resultado_motor["Z"])
    if valores_motor is None or len(valores_motor) != n or valor_motor is None:
        return _no_disponible("La solución del motor no tiene dimensiones o valores numéricos válidos.")
    if valores_motor != valores_variables:
        return _no_disponible("La solución del motor no coincide con los valores básicos del tableau.")
    if sum(costos[j] * valores_variables[j] for j in range(n)) != valor_motor:
        return _no_disponible("El valor objetivo del motor no coincide con la solución y los coeficientes originales.")

    ld_regular_esperado = sum(
        sigma * costos[indice] * rhs_basicos[fila_indice]
        for fila_indice, indice in enumerate(indices)
        if indice < n
    )
    if ld_z_regular != ld_regular_esperado or ld_z_m != 0:
        return _no_disponible("Los lados derechos de la fila Z no son coherentes con la base actual.")

    indices_base = set(indices)
    fila_por_indice = {indice: fila for fila, indice in enumerate(indices)}
    variables = []
    optimos_multiples = False
    for indice_variable in range(n):
        if indice_variable in indices_base:
            fila_basica = fila_por_indice[indice_variable]
            costo_reducido = Fraction(0)
            minimo_delta = None
            maximo_delta = None
            for columna in range(total_columnas):
                if columna in indices_base or columna in artificiales:
                    continue
                intervalo = _intersectar_desigualdad(
                    minimo_delta,
                    maximo_delta,
                    fila_z_regular[columna],
                    sigma * coeficientes_filas[fila_basica][columna],
                )
                if intervalo is None:
                    return _no_disponible("No se pudo obtener un intervalo coherente para un coeficiente objetivo.")
                minimo_delta, maximo_delta = intervalo
        else:
            costo_reducido = -sigma * fila_z_regular[indice_variable]
            intervalo = _intersectar_desigualdad(
                None,
                None,
                fila_z_regular[indice_variable],
                -sigma,
            )
            if intervalo is None:
                return _no_disponible("No se pudo obtener un intervalo coherente para un coeficiente objetivo.")
            minimo_delta, maximo_delta = intervalo
            if fila_z_regular[indice_variable] == 0:
                puede_aumentar = all(
                    rhs_basicos[fila] > 0 or coeficientes_filas[fila][indice_variable] <= 0
                    for fila in range(m)
                )
                if puede_aumentar:
                    optimos_multiples = True

        minimo_coeficiente = None if minimo_delta is None else costos[indice_variable] + minimo_delta
        maximo_coeficiente = None if maximo_delta is None else costos[indice_variable] + maximo_delta
        variables.append({
            "variable": f"x{indice_variable + 1}",
            "valor_optimo": valores_variables[indice_variable],
            "costo_reducido": costo_reducido,
            "coeficiente_objetivo": costos[indice_variable],
            "minimo": minimo_coeficiente,
            "maximo": maximo_coeficiente,
            "interpretacion": (
                "La base actual permanece óptima mientras el coeficiente esté entre "
                f"{_limite_texto(minimo_coeficiente, True)} y {_limite_texto(maximo_coeficiente, False)}."
            ),
        })

    restricciones = []
    for indice_restriccion, columna in enumerate(columnas_positivas):
        alpha = Fraction(1) if lados_derechos[indice_restriccion] >= 0 else Fraction(-1)
        precio_sombra = sigma * alpha * fila_z_regular[columna]
        minimo_delta = None
        maximo_delta = None
        for fila, rhs in enumerate(rhs_basicos):
            intervalo = _intersectar_desigualdad(
                minimo_delta,
                maximo_delta,
                rhs,
                alpha * coeficientes_filas[fila][columna],
            )
            if intervalo is None:
                return _no_disponible("No se pudo obtener un intervalo coherente para un lado derecho.")
            minimo_delta, maximo_delta = intervalo
        minimo_rhs = None if minimo_delta is None else lados_derechos[indice_restriccion] + minimo_delta
        maximo_rhs = None if maximo_delta is None else lados_derechos[indice_restriccion] + maximo_delta
        restricciones.append({
            "restriccion": f"R{indice_restriccion + 1}",
            "precio_sombra": precio_sombra,
            "lado_derecho": lados_derechos[indice_restriccion],
            "minimo": minimo_rhs,
            "maximo": maximo_rhs,
            "interpretacion": (
                f"El precio sombra es {_fraccion_texto(precio_sombra)} por unidad; el lado derecho "
                "puede variar entre "
                f"{_limite_texto(minimo_rhs, True)} y {_limite_texto(maximo_rhs, False)} "
                "manteniendo la base actual."
            ),
        })

    degenerado = any(rhs == 0 for rhs in rhs_basicos)
    advertencias = []
    if degenerado:
        advertencias.append(
            "La solución es degenerada; los precios sombra pueden no ser únicos y los rangos corresponden a la base actual."
        )

    return {
        "disponible": True,
        "mensaje": "",
        "advertencias": advertencias,
        "degenerado": degenerado,
        "optimos_multiples": optimos_multiples,
        "variables": variables,
        "restricciones": restricciones,
    }
