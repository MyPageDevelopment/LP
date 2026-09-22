# =======================================================
# main.py - Punto de entrada del Intérprete
# =======================================================
import sys
import os
from parser import parsear

def main():
    print("=" * 80)
    print("   INTÉRPRETE DE TOPOLOGÍAS DE STREAM PROCESSING - CONTROL 1")
    print("   Asignatura: Lenguajes de Programación.")
    print("=" * 80)

    if len(sys.argv) < 2:
        print("\nTe falto el archivo jeje")
        print("Ejemplo: python main.py test.dsl\n")
        sys.exit(1)

    archivo = sys.argv[1]
    if not os.path.isfile(archivo):
        print(f"\n[Erroooor], te equivocaste en el nombre o no existe we :D, '{archivo}' no existe :C SAD.")
        sys.exit(1)

    print(f"[*] Leyendo archivo fuente: {archivo} ...")
    with open(archivo, 'r', encoding='utf-8') as f:
        codigo = f.read()

    print("[*] Ejecutando análisis léxico y sintáctico..., espere un momentito")
    topologia, errores_sintacticos = parsear(codigo)

    if errores_sintacticos:
        print(f"\n[!] Se encontraron {len(errores_sintacticos)} error(es) sintáctico(s):")
        for err in errores_sintacticos:
            print(f"    -> {err}")
        sys.exit(1)

    print(f"[+] Sintaxis válida. Nodos: {len(topologia.nodos)} | Eventos a simular: {topologia.eventos_a_simular}")

    print("\n[*] Validando reglas semánticas y estructura del grafo (DAG)...")
    if not topologia.validar():
        print(f"\n[!] Se encontraron {len(topologia.errores)} error(es) en la topología:")
        for err in topologia.errores:
            print(f"    -> {err}")
        sys.exit(1)

    print("[+] Grafo de topología validado exitosamente:")
    print("    - Contiene al menos una fuente y un sumidero.")
    print("    - Es un Grafo Dirigido Acíclico (DAG) sin ciclos.")
    print("    - Las fuentes no tienen entradas y los sumideros no tienen salidas.")
    print("    - Todos los nodos son alcanzables y llegan a un sumidero.")

    print("\n" + "-" * 80)
    print(" COMPONENTES Y CONEXIONES REGISTRADAS:")
    print("-" * 80)
    for nombre, nodo in topologia.nodos.items():
        if nodo.tipo == 'FUENTE':
            print(f"  * FUENTE   '{nombre}' -> Destinos: {topologia.adyacentes.get(nombre, [])}")
        elif nodo.tipo == 'OPERADOR':
            print(f"  * OPERADOR '{nombre}': {nodo.replicas} réplica(s) en paralelo -> Destinos: {topologia.adyacentes.get(nombre, [])}")
        elif nodo.tipo == 'SUMIDERO':
            print(f"  * SUMIDERO '{nombre}' <- Orígenes: {topologia.predecesores.get(nombre, [])}")
    print("-" * 80)

    # Iniciar simulación
    topologia.simular()

if __name__ == '__main__':
    main()
