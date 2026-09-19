# ==============================================================================
# ARCHIVO: parser.py
# TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
# ASIGNATURA: Lenguajes y Autómatas / Compiladores
# DESCRIPCIÓN: Analizador sintáctico implementado con PLY (yacc).
#              Define la gramática libre de contexto para el DSL, construye
#              la tabla de símbolos, el grafo de la topología y la lista
#              de eventos para la simulación.
# ==============================================================================

import ply.yacc as yacc
from lexer import tokens, construir_lexer
from topology import TablaSimbolos, Topologia, EventoEmision

# -----------------------------------------------------------------------------
# VARIABLES GLOBALES PARA CONSTRUIR EL ESTADO DE LA TOPOLOGÍA
# Acá guardamos todo lo que vamos leyendo a medida que reducimos reglas gramaticales.
# -----------------------------------------------------------------------------
tabla_actual = None
topologia_actual = None
emisiones_actuales = []
errores_sintacticos = []

# -----------------------------------------------------------------------------
# REGLAS DE LA GRAMÁTICA (BNF)
# -----------------------------------------------------------------------------

# Regla inicial: Un programa es una lista de sentencias (declaraciones, conexiones, emits)
def p_program(p):
    '''program : statement_list'''
    # Al terminar de procesar todo el archivo, retornamos la tupla con todo listo
    p[0] = {
        'tabla': tabla_actual,
        'topologia': topologia_actual,
        'emisiones': emisiones_actuales,
        'errores': list(errores_sintacticos)
    }

# Lista de sentencias recursiva por la izquierda
def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement
                      | empty'''
    pass

# Tipos de sentencias aceptadas en nuestro DSL
def p_statement(p):
    '''statement : declaration_stmt
                 | connection_stmt
                 | emit_stmt
                 | simulation_block'''
    pass

# -----------------------------------------------------------------------------
# DECLARACIONES DE NODOS
# Permite declarar fuentes, operadores (con o sin paralelismo) y sumideros.
# -----------------------------------------------------------------------------

# Declaración de una fuente: SOURCE nombre;
def p_declaration_source(p):
    '''declaration_stmt : SOURCE IDENT SEMICOLON'''
    nombre_nodo = p[2]
    num_linea = p.lineno(2)
    # Guardamos en la tabla de símbolos como nodo de tipo SOURCE
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='SOURCE', paralelismo=1, linea=num_linea)

# -----------------------------------------------------------------------------
# EXIGENCIA DEL CONTROL: OPERADOR siempre debe declarar TIEMPO_SERVICIO.
# 'OPERATOR' y 'OPERADOR' comparten el mismo token (ver lexer.py), pero PLY
# conserva en p[1] el texto literal exacto que escribió el usuario (t.value no
# se sobreescribe al cambiar t.type), así que podemos distinguir cuál palabra
# se usó realmente sin duplicar la gramática ni crear un token nuevo.
# -----------------------------------------------------------------------------
def _es_palabra_oficial_operador(texto_literal):
    """True si el usuario escribió la palabra OFICIAL del Control ('operador',
    en cualquier combinación de mayúsculas/minúsculas), no la legacy 'operator'."""
    return texto_literal.lower() == 'operador'

def _rechazar_operador_oficial_sin_tiempo(p, nombre_nodo, linea):
    """
    Si la declaración usó la palabra OFICIAL 'OPERADOR' pero no incluye
    TIEMPO_SERVICIO, no se debe registrar el nodo como válido: el Control
    exige TIEMPO_SERVICIO siempre para OPERADOR. Retorna True si se rechazó.
    """
    if _es_palabra_oficial_operador(p[1]):
        tabla_actual.errores.append(
            f"[ERROR SEMÁNTICO] Línea {linea}: OPERADOR '{nombre_nodo}' debe declarar TIEMPO_SERVICIO "
            f"(exigido por el Control I). Use 'OPERADOR {nombre_nodo} TIEMPO_SERVICIO <valor> "
            f"[REPLICAS <n>];', o la forma legacy 'OPERATOR {nombre_nodo};' si solo necesita "
            f"compatibilidad técnica temporal (ver Readme.txt, sección 5)."
        )
        return True
    return False

# Declaración de un operador con paralelismo explícito: OPERATOR nombre PARALLEL numero;
def p_declaration_operator_parallel(p):
    '''declaration_stmt : OPERATOR IDENT PARALLEL NUMBER SEMICOLON'''
    nombre_nodo = p[2]
    num_replicas = p[4]
    num_linea = p.lineno(2)
    if _rechazar_operador_oficial_sin_tiempo(p, nombre_nodo, num_linea):
        return
    # Registramos el operador indicando cuántas réplicas en paralelo tendrá
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='OPERATOR', paralelismo=num_replicas, linea=num_linea)

# Declaración de operador con tiempo de servicio (exigido por el Control):
# OPERATOR nombre TIEMPO_SERVICIO numero;
def p_declaration_operator_tiempo_servicio(p):
    '''declaration_stmt : OPERATOR IDENT TIEMPO_SERVICIO NUMBER SEMICOLON'''
    nombre_nodo = p[2]
    tiempo_servicio = p[4]
    num_linea = p.lineno(2)
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='OPERATOR', paralelismo=1,
                                linea=num_linea, tiempo_servicio=tiempo_servicio)

# Declaración de operador con tiempo de servicio y réplicas (PARALLEL token,
# que ya acepta tanto 'PARALLEL' como el sinónimo 'REPLICAS' desde el lexer):
# OPERATOR nombre TIEMPO_SERVICIO numero PARALLEL numero;
# OPERATOR nombre TIEMPO_SERVICIO numero REPLICAS numero;
def p_declaration_operator_tiempo_servicio_parallel(p):
    '''declaration_stmt : OPERATOR IDENT TIEMPO_SERVICIO NUMBER PARALLEL NUMBER SEMICOLON'''
    nombre_nodo = p[2]
    tiempo_servicio = p[4]
    num_replicas = p[6]
    num_linea = p.lineno(2)
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='OPERATOR', paralelismo=num_replicas,
                                linea=num_linea, tiempo_servicio=tiempo_servicio)

# Declaración de operador con sintaxis de corchetes: OPERATOR nombre [PARALLEL = numero];
def p_declaration_operator_brackets(p):
    '''declaration_stmt : OPERATOR IDENT LBRACKET PARALLEL EQUALS NUMBER RBRACKET SEMICOLON'''
    nombre_nodo = p[2]
    num_replicas = p[6]
    num_linea = p.lineno(2)
    if _rechazar_operador_oficial_sin_tiempo(p, nombre_nodo, num_linea):
        return
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='OPERATOR', paralelismo=num_replicas, linea=num_linea)

# Declaración de operador simple (asume paralelismo = 1 si no se especifica): OPERATOR nombre;
def p_declaration_operator_default(p):
    '''declaration_stmt : OPERATOR IDENT SEMICOLON'''
    nombre_nodo = p[2]
    num_linea = p.lineno(2)
    if _rechazar_operador_oficial_sin_tiempo(p, nombre_nodo, num_linea):
        return
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='OPERATOR', paralelismo=1, linea=num_linea)

# Declaración de un sumidero: SINK nombre;
def p_declaration_sink(p):
    '''declaration_stmt : SINK IDENT SEMICOLON'''
    nombre_nodo = p[2]
    num_linea = p.lineno(2)
    tabla_actual.declarar_nodo(nombre=nombre_nodo, tipo='SINK', paralelismo=1, linea=num_linea)

# -----------------------------------------------------------------------------
# CONEXIONES ENTRE NODOS DE LA TOPOLOGÍA
# Soporta tanto cadenas simples (A -> B;) como encadenadas (A -> B -> C;)
# y también con la palabra opcional CONNECT (CONNECT A -> B;).
# -----------------------------------------------------------------------------

def p_connection_stmt(p):
    '''connection_stmt : chain_connection SEMICOLON
                       | CONNECT chain_connection SEMICOLON'''
    # Las aristas ya fueron agregadas en la regla chain_connection
    pass

# Forma OFICIAL del Control: CONECTAR <id_origen> A <id_destino>;
# 'CONECTAR' y 'A' son sinónimos léxicos de 'CONNECT' y 'TO' (ver lexer.py),
# así que esta regla es la única producción nueva necesaria -- reutiliza
# exactamente Topologia.conectar(), sin una segunda implementación de aristas.
# No admite encadenamiento (el Control solo especifica la forma binaria);
# el encadenamiento sigue siendo una extensión exclusiva de la sintaxis '->'.
def p_connection_conectar_a(p):
    '''connection_stmt : CONNECT IDENT TO IDENT SEMICOLON'''
    origen = p[2]
    destino = p[4]
    linea = p.lineno(2)
    topologia_actual.conectar(origen, destino, linea)

def p_chain_connection_pair(p):
    '''chain_connection : IDENT ARROW IDENT'''
    origen = p[1]
    destino = p[3]
    linea = p.lineno(1)
    # Agregamos la conexión en el grafo
    topologia_actual.conectar(origen, destino, linea)
    # Pasamos una lista con los dos nodos para permitir encadenar más con '->'
    p[0] = [origen, destino]

def p_chain_connection_multiple(p):
    '''chain_connection : chain_connection ARROW IDENT'''
    lista_nodos = p[1]
    nuevo_destino = p[3]
    linea = p.lineno(3)
    # Conectamos el último nodo de la cadena con el nuevo destino
    ultimo_origen = lista_nodos[-1]
    topologia_actual.conectar(ultimo_origen, nuevo_destino, linea)
    p[0] = lista_nodos + [nuevo_destino]

# -----------------------------------------------------------------------------
# EMISIÓN DE EVENTOS PARA LA SIMULACIÓN
# Soporta sintaxis: EMIT "mensaje" TO fuente; o EMIT "mensaje" -> fuente;
# -----------------------------------------------------------------------------

def p_emit_stmt(p):
    '''emit_stmt : EMIT STRING TO IDENT SEMICOLON
                 | EMIT STRING ARROW IDENT SEMICOLON'''
    payload = p[2]
    fuente_nombre = p[4]
    linea = p.lineno(1)
    # Creamos el objeto evento y lo agregamos a la cola de simulación
    nuevo_evento = EventoEmision(payload=payload, fuente_nombre=fuente_nombre, linea=linea)
    emisiones_actuales.append(nuevo_evento)

# Bloque opcional SIMULATE { ... } por si el usuario prefiere agrupar las emisiones
def p_simulation_block(p):
    '''simulation_block : SIMULATE LBRACE statement_list RBRACE'''
    pass

# -----------------------------------------------------------------------------
# SIMULAR <cantidad_eventos> (Control I)
# 'SIMULATE' y 'SIMULAR' son el mismo token léxico (ver lexer.py, igual que
# PARALLEL/REPLICAS), por lo que esta regla acepta tanto "SIMULATE 3;" como
# "SIMULAR 3;" sin duplicar la gramática.
# Genera automáticamente <cantidad_eventos> EventoEmision con contenido
# sintético y los agrega a la misma cola (emisiones_actuales) que ya consume
# el Simulador existente -- no se crea un mecanismo de simulación paralelo.
# -----------------------------------------------------------------------------
def p_simulation_run(p):
    '''simulation_block : SIMULATE NUMBER SEMICOLON'''
    cantidad_eventos = p[2]
    linea = p.lineno(1)

    if cantidad_eventos <= 0:
        tabla_actual.errores.append(
            f"[ERROR SEMÁNTICO] Línea {linea}: SIMULAR requiere una cantidad de eventos "
            f"mayor a 0 (se especificó: {cantidad_eventos})."
        )
        return

    generar_eventos_automaticos(cantidad_eventos, linea)

def generar_eventos_automaticos(cantidad_eventos, linea):
    """
    Genera 'cantidad_eventos' EventoEmision con contenido sintético (el
    Control pide simular tuplas "con contenido sintético"), repartidos
    mediante Round-Robin entre las FUENTEs declaradas HASTA ESTE PUNTO del
    archivo (igual que CONECTAR, SIMULAR exige que las FUENTEs ya estén
    declaradas antes de usarse).

    Decisión de equipo (el enunciado no especifica qué ocurre con múltiples
    FUENTEs): si hay más de una, los N eventos se distribuyen circularmente
    entre ellas -- misma idea de reparto equitativo que ya se usa para las
    réplicas de un OPERATOR, aplicada aquí a nivel de selección de fuente.
    """
    fuentes = [nodo for nodo in tabla_actual.simbolos.values() if nodo.tipo == 'SOURCE']
    if not fuentes:
        # Sin fuentes declaradas todavía no hay nada que generar; la
        # ausencia de SOURCE ya será reportada por Topologia.validar_topologia().
        return

    for indice in range(cantidad_eventos):
        fuente_elegida = fuentes[indice % len(fuentes)]
        payload_sintetico = f"tupla_sintetica_{indice + 1}"
        nuevo_evento = EventoEmision(payload=payload_sintetico, fuente_nombre=fuente_elegida.nombre, linea=linea)
        emisiones_actuales.append(nuevo_evento)

# Regla para permitir producciones vacías
def p_empty(p):
    '''empty :'''
    pass

# -----------------------------------------------------------------------------
# MANEJO DE ERRORES SINTÁCTICOS
# Cuando el parser encuentra un token que no calza con la gramática, entra acá.
# -----------------------------------------------------------------------------
def p_error(p):
    if p:
        mensaje = f"[ERROR SINTÁCTICO] Token inesperado '{p.value}' (tipo: {p.type}) en la línea {p.lineno}."
    else:
        mensaje = "[ERROR SINTÁCTICO] Fin de archivo inesperado (EOF). ¿Faltó algún punto y coma o cerrar llave?"
    print(mensaje)
    errores_sintacticos.append(mensaje)

# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL PARA PARSEAR UN TEXTO
# Inicializa las estructuras limpias, construye el parser y retorna el resultado.
# -----------------------------------------------------------------------------
def parsear_codigo(texto_fuente):
    """
    Recibe el string con el código DSL, ejecuta el análisis sintáctico
    y retorna un diccionario con la tabla de símbolos, topología y emisiones.
    """
    global tabla_actual, topologia_actual, emisiones_actuales, errores_sintacticos
    
    # Reiniciamos las estructuras para cada llamada
    tabla_actual = TablaSimbolos()
    topologia_actual = Topologia(tabla_actual)
    emisiones_actuales = []
    errores_sintacticos = []

    # Construimos el lexer e invocamos el parseo
    analizador_lexico = construir_lexer()
    # Construimos el parser de PLY
    parser = yacc.yacc(debug=False, write_tables=False)
    
    # Ejecutamos el análisis entregando el lexer
    resultado = parser.parse(texto_fuente, lexer=analizador_lexico)
    return resultado

# Prueba rápida individual de parser.py
if __name__ == '__main__':
    codigo_ejemplo = '''
    SOURCE s1;
    OPERATOR f1 PARALLEL 2;
    SINK k1;
    s1 -> f1 -> k1;
    EMIT "hola mundo" TO s1;
    '''
    print("--- Probando parser.py ---")
    res = parsear_codigo(codigo_ejemplo)
    if res and len(res['errores']) == 0:
        print("Sintaxis correcta. Nodos declarados:", list(res['tabla'].simbolos.keys()))
        print("Aristas conectadas:", res['topologia'].aristas)
        print("Emisiones:", len(res['emisiones']))
    else:
        print("Errores encontrados:", res['errores'])
