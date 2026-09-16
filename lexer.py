# ==============================================================================
# ARCHIVO: lexer.py
# TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
# ASIGNATURA: Lenguajes y Autómatas / Compiladores
# DESCRIPCIÓN: Analizador léxico implementado con la librería PLY (Python Lex-Yacc).
#              Se encarga de transformar el código fuente del DSL en un flujo
#              de tokens legibles por el parser, manejando líneas y errores.
# ==============================================================================

import ply.lex as lex

# -----------------------------------------------------------------------------
# PALABRAS RESERVADAS DEL DSL
# Definimos un diccionario para no confundir palabras clave con nombres de variables (identificadores).
# Mapeamos tanto en minúsculas como mayúsculas para que el lenguaje sea flexible y amigable.
# -----------------------------------------------------------------------------
palabras_reservadas = {
    'source': 'SOURCE',
    'operator': 'OPERATOR',
    'sink': 'SINK',
    'parallel': 'PARALLEL',
    'replicas': 'PARALLEL',    # permitimos 'replicas' como sinónimo de 'parallel'
    'connect': 'CONNECT',
    'to': 'TO',
    'emit': 'EMIT',
    'simulate': 'SIMULATE'
}

# -----------------------------------------------------------------------------
# LISTA DE TOKENS
# Acá juntamos las palabras reservadas con los símbolos y literales que reconoce el lexer.
# -----------------------------------------------------------------------------
tokens = [
    'IDENT',          # Nombres de fuentes, operadores, sumideros (ej. sensor1, filtro)
    'STRING',         # Cadenas de texto con comillas para la carga de los eventos
    'NUMBER',         # Números enteros (ej. cantidad de réplicas en paralelo)
    'ARROW',          # Flecha de conexión entre nodos (->)
    'SEMICOLON',      # Punto y coma de fin de instrucción (;)
    'LBRACKET',       # Corchete izquierdo ([)
    'RBRACKET',       # Corchete derecho (])
    'LBRACE',         # Llave izquierda ({)
    'RBRACE',         # Llave derecha (})
    'EQUALS',         # Signo igual (=)
] + list(set(palabras_reservadas.values()))

# -----------------------------------------------------------------------------
# REGLAS CON EXPRESIONES REGULARES SIMPLES
# Tokens que se reconocen con una sola expresión regular directa sin lógica extra.
# -----------------------------------------------------------------------------
t_ARROW     = r'->'
t_SEMICOLON = r';'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_EQUALS    = r'='

# Ignoramos espacios en blanco, tabulaciones y retornos de carro
t_ignore = ' \t\r'

# -----------------------------------------------------------------------------
# REGLAS CON FUNCIONES (Para lógica adicional como números de línea y tipos)
# -----------------------------------------------------------------------------

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    # Le quitamos las comillas al inicio y al final para quedarnos solo con el contenido del mensaje
    t.value = t.value[1:-1]
    return t

def t_NUMBER(t):
    r'\d+'
    # Convertimos el texto del número a un entero de Python para usarlo directamente en cálculos
    t.value = int(t.value)
    return t

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Revisamos si el identificador es en verdad una palabra reservada (ej: SOURCE, OPERATOR)
    # Lo pasamos a minúscula al buscar para que acepte tanto 'source' como 'SOURCE'
    nombre_minuscula = t.value.lower()
    if nombre_minuscula in palabras_reservadas:
        t.type = palabras_reservadas[nombre_minuscula]
    else:
        t.type = 'IDENT'
    return t

# -----------------------------------------------------------------------------
# MANEJO DE COMENTARIOS
# Permitimos comentarios de una sola línea con // o con # (estilo C y Python)
# y comentarios multilínea con /* ... */ para que sea cómodo documentar el DSL.
# -----------------------------------------------------------------------------

def t_COMMENT_LINE(t):
    r'(//|\#).*'
    # No retornamos nada para que el lexer simplemente descarte el comentario
    pass

def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    # Si el comentario tiene saltos de línea, sumamos al contador de líneas del lexer
    saltos = t.value.count('\n')
    t.lexer.lineno += saltos
    pass

def t_newline(t):
    r'\n+'
    # Cada vez que vemos un salto de línea aumentamos el número de línea para dar buenos mensajes de error
    t.lexer.lineno += len(t.value)

# -----------------------------------------------------------------------------
# MANEJO DE ERRORES LÉXICOS
# Si el usuario escribe un carácter raro (como @ o $), se avisa en qué línea ocurrió.
# -----------------------------------------------------------------------------
def t_error(t):
    # Imprimimos el error léxico con la línea exacta para que el profe o usuario sepa dónde corregir
    print(f"[ERROR LÉXICO] Carácter no reconocido '{t.value[0]}' en la línea {t.lineno}")
    # Saltamos ese carácter para intentar seguir analizando el resto del archivo
    t.lexer.skip(1)

# -----------------------------------------------------------------------------
# FUNCIÓN CONSTRUCTORA DEL ANALIZADOR LÉXICO
# Retorna una instancia lista de lexer de PLY.
# -----------------------------------------------------------------------------
def construir_lexer():
    """
    Construye y retorna el analizador léxico de PLY configurado con nuestras reglas.
    """
    return lex.lex()

# Si ejecutamos este archivo directamente en consola, hacemos una prueba rápida
if __name__ == '__main__':
    codigo_prueba = '''
    // Prueba de tokens
    SOURCE sensor;
    OPERATOR filtro PARALLEL 2;
    SINK bd;
    sensor -> filtro -> bd;
    EMIT "dato de prueba" TO sensor;
    '''
    analizador = construir_lexer()
    analizador.input(codigo_prueba)
    print("--- Probando tokens en lexer.py ---")
    while True:
        tok = analizador.token()
        if not tok:
            break
        print(f"Línea {tok.lineno} -> Tipo: {tok.type}, Valor: {repr(tok.value)}")
