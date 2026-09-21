# =======================================================
# parser.py - Analizador Sintáctico para el DSL (PLY Yacc)
# =======================================================
# pyrefly: ignore [missing-import]
import ply.yacc as yacc
from lexer import tokens, construir_lexer
from topology import Topologia, Nodo

# Estado global durante el parseo
topologia_actual = None
errores_sintacticos = []

# Regla inicial: lista de sentencias
def p_program(p):
    '''program : statement_list'''
    p[0] = topologia_actual

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement
                      | empty'''
    pass

def p_statement(p):
    '''statement : decl_fuente
                 | decl_operador
                 | decl_sumidero
                 | conexion
                 | simulacion'''
    pass

# Regla auxiliar: punto y coma opcional
def p_opt_semicolon(p):
    '''opt_semicolon : SEMICOLON
                     | empty'''
    pass

# Declaración de Fuente: FUENTE id [;]
def p_decl_fuente(p):
    '''decl_fuente : FUENTE IDENT opt_semicolon'''
    nodo = Nodo(nombre=p[2], tipo='FUENTE', linea=p.lineno(1))
    topologia_actual.agregar_nodo(nodo)

# Declaración de Operador con réplicas: OPERADOR id TIEMPO_SERVICIO n REPLICAS m [;]
def p_decl_operador_replicas(p):
    '''decl_operador : OPERADOR IDENT TIEMPO_SERVICIO NUMBER REPLICAS NUMBER opt_semicolon'''
    nodo = Nodo(nombre=p[2], tipo='OPERADOR', linea=p.lineno(1), tiempo_servicio=p[4], replicas=p[6])
    topologia_actual.agregar_nodo(nodo)

# Declaración de Operador simple (1 réplica por defecto): OPERADOR id TIEMPO_SERVICIO n [;]
def p_decl_operador_simple(p):
    '''decl_operador : OPERADOR IDENT TIEMPO_SERVICIO NUMBER opt_semicolon'''
    nodo = Nodo(nombre=p[2], tipo='OPERADOR', linea=p.lineno(1), tiempo_servicio=p[4], replicas=1)
    topologia_actual.agregar_nodo(nodo)

# Declaración de Sumidero: SUMIDERO id [;]
def p_decl_sumidero(p):
    '''decl_sumidero : SUMIDERO IDENT opt_semicolon'''
    nodo = Nodo(nombre=p[2], tipo='SUMIDERO', linea=p.lineno(1))
    topologia_actual.agregar_nodo(nodo)

# Conexión: CONECTAR id A id [;]
def p_conexion(p):
    '''conexion : CONECTAR IDENT A IDENT opt_semicolon'''
    topologia_actual.conectar(origen=p[2], destino=p[4], linea=p.lineno(1))

# Simulación: SIMULAR n [;]
def p_simulacion(p):
    '''simulacion : SIMULAR NUMBER opt_semicolon'''
    topologia_actual.eventos_a_simular = p[2]

def p_empty(p):
    '''empty :'''
    pass

# Manejo de errores sintácticos
def p_error(p):
    if p:
        msg = f"[Error Sintáctico] Token inesperado '{p.value}' en la línea {p.lineno}"
    else:
        msg = "[Error Sintáctico] Fin de archivo inesperado"
    errores_sintacticos.append(msg)
    print(msg)

def parsear(codigo_fuente):
    global topologia_actual, errores_sintacticos
    topologia_actual = Topologia()
    errores_sintacticos = []

    lexer = construir_lexer()
    parser = yacc.yacc(write_tables=False, debug=False)
    parser.parse(codigo_fuente, lexer=lexer)

    return topologia_actual, errores_sintacticos
