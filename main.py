# ==============================================================================
# ARCHIVO: main.py
# TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
# ASIGNATURA: Lenguajes y Autómatas / Compiladores
# DESCRIPCIÓN: Punto de entrada principal para ejecutar el intérprete.
#              Lee el archivo con la definición de la topología (.dsl),
#              ejecuta el parser (lexer + yacc), valida semánticamente
#              el grafo (DAG) y corre la simulación paso a paso.
# ==============================================================================

import sys
import os
from parser import parsear_codigo
from topology import Simulador

def imprimir_banner():
    """
    Imprime una cabecera para que la salida en terminal sea ordenada y visualmente clara.
    """
    print("=" * 80)
    print("   INTÉRPRETE DE TOPOLOGÍAS DE STREAM PROCESSING - CONTROL 1")
    print("   Asignatura: Lenguajes y Autómatas / Compiladores")
    print("=" * 80)

def imprimir_ayuda():
    """
    Explica cómo invocar el script desde la línea de comandos.
    """
    print("\nModo de uso:")
    print("    python main.py <archivo_topologia.dsl>\n")
    print("Ejemplo:")
    print("    python main.py test.dsl\n")

def main():
    imprimir_banner()

    # 1. Validación de argumentos de la línea de comandos
    if len(sys.argv) < 2:
        print("[ERROR] Falta especificar el archivo de la topología.")
        imprimir_ayuda()
        sys.exit(1)

    ruta_archivo = sys.argv[1]

    # Permitir ver ayuda si el usuario pone --help o -h
    if ruta_archivo in ['-h', '--help']:
        imprimir_ayuda()
        sys.exit(0)

    # 2. Verificamos que el archivo realmente exista en el sistema
    if not os.path.isfile(ruta_archivo):
        print(f"[ERROR] El archivo '{ruta_archivo}' no existe o no se puede leer.")
        sys.exit(1)

    print(f"[*] Leyendo archivo fuente: {ruta_archivo} ...")

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido_dsl = f.read()
    except Exception as e:
        print(f"[ERROR] Ocurrió un problema al abrir el archivo: {e}")
        sys.exit(1)

    # 3. Fase de Análisis Léxico y Sintáctico (PLY)
    print("[*] Ejecutando análisis léxico y sintáctico...")
    resultado_parser = parsear_codigo(contenido_dsl)

    if not resultado_parser:
        print("[ERROR CRÍTICO] El parser falló y no pudo generar estructuras.")
        sys.exit(1)

    # Si hubo errores de sintaxis, los mostramos y paramos
    if len(resultado_parser['errores']) > 0:
        print(f"\n[!] Se encontraron {len(resultado_parser['errores'])} error(es) sintáctico(s):")
        for err in resultado_parser['errores']:
            print(f"    -> {err}")
        print("\n[FIN] Corrija la sintaxis del archivo antes de continuar.")
        sys.exit(1)

    tabla = resultado_parser['tabla']
    topologia = resultado_parser['topologia']
    emisiones = resultado_parser['emisiones']

    print(f"[+] Sintaxis valida. Nodos encontrados: {len(tabla.simbolos)} | Conexiones: {len(topologia.aristas)} | Eventos a simular: {len(emisiones)}")

    # 4. Fase de Validación Semántica y de Grafo (DAG)
    print("\n[*] Validando reglas semanticas y estructura del grafo (DAG)...")
    es_valido = topologia.validar_topologia()

    # Recolectamos todos los errores (de la tabla de símbolos y de la validación del grafo)
    todos_errores = tabla.errores + topologia.errores_grafo

    if not es_valido or len(todos_errores) > 0:
        print(f"\n[!] Se encontraron {len(todos_errores)} error(es) en la topologia:")
        for err in todos_errores:
            print(f"    -> {err}")
        print("\n[FIN] La topología no cumple con las restricciones requeridas. Abortando simulación.")
        sys.exit(1)

    print("[+] Grafo de topología validado exitosamente:")
    print("    - Contiene al menos una fuente y un sumidero.")
    print("    - Es un Grafo Dirigido Acíclico (DAG) sin ciclos.")
    print("    - Las fuentes no tienen entradas y los sumideros no tienen salidas.")
    print("    - Todos los nodos son alcanzables y llegan a un sumidero.")

    # Mostramos resumen de la topología cargada
    print("\n" + "-" * 80)
    print(" COMPONENTES Y CONEXIONES REGISTRADAS:")
    print("-" * 80)
    for nombre, nodo in tabla.simbolos.items():
        if nodo.tipo == 'OPERATOR':
            destinos = topologia.adyacentes.get(nombre, [])
            print(f"  * OPERADOR '{nombre}': {nodo.paralelismo} réplica(s) en paralelo -> Destinos: {destinos}")
        elif nodo.tipo == 'SOURCE':
            destinos = topologia.adyacentes.get(nombre, [])
            print(f"  * FUENTE   '{nombre}' -> Destinos: {destinos}")
        elif nodo.tipo == 'SINK':
            origenes = topologia.predecesores.get(nombre, [])
            print(f"  * SUMIDERO '{nombre}' <- Orígenes: {origenes}")
    print("-" * 80)

    # 5. Fase de Simulación
    simulador = Simulador(topologia)
    simulador.simular(emisiones)

    print("[ÉXITO] Ejecución y simulación finalizadas correctamente.\n")

if __name__ == '__main__':
    main()
