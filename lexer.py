# =======================================================
# lexer.py - Analizador Léxico para el DSL (PLY Lex)
# =======================================================
# pyrefly: ignore [missing-import]
import ply.lex as lex

# Palabras reservadas del DSL
reservadas = {
    'fuente': 'FUENTE',
    'operador': 'OPERADOR',
    'tiempo_servicio': 'TIEMPO_SERVICIO',
    'replicas': 'REPLICAS',
    'sumidero': 'SUMIDERO',
    'conectar': 'CONECTAR',
    'a': 'A',
    'simular': 'SIMULAR'
}

# Lista de tokens reconocidos
tokens = [
    'IDENT',
    'NUMBER',
    'SEMICOLON'
] + list(reservadas.values())

# Tokens simples
t_SEMICOLON = r';'

# Ignoramos espacios y tabulaciones
t_ignore = ' \t\r'

# Comentarios de una sola línea: //
def t_COMMENT(t):
    r'//.*'
    pass

# Reconocer identificadores y palabras reservadas (insensible a mayúsculas/minúsculas)
def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reservadas.get(t.value.lower(), 'IDENT')
    return t

# Reconocer números enteros
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Rastrear números de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Manejo de caracteres no reconocidos
def t_error(t):
    print(f"[Errooooooooor Léxico] Carácter inválido '{t.value[0]}' en la línea {t.lineno}, revise su archivo dsl")
    t.lexer.skip(1)

def construir_lexer():
    return lex.lex()
