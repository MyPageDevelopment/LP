# ==============================================================================
# ARCHIVO: topology.py
# TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
# ASIGNATURA: Lenguajes y Autómatas / Compiladores
# DESCRIPCIÓN: Define las clases para representar los nodos de la topología,
#              la tabla de símbolos, las validaciones del grafo dirigido (DAG)
#              y el motor de simulación de eventos con Round-Robin independiente.
# ==============================================================================

# -----------------------------------------------------------------------------
# CLASES PARA REPRESENTAR LOS NODOS DE LA TOPOLOGÍA
# -----------------------------------------------------------------------------

class Nodo:
    """
    Clase base para cualquier componente de la topología.
    Guarda el nombre del nodo, su tipo y la línea donde se declaró en el archivo.
    """
    def __init__(self, nombre, tipo, linea):
        self.nombre = nombre
        self.tipo = tipo            # 'SOURCE', 'OPERATOR' o 'SINK'
        self.linea = linea          # Línea del código para dar buenos mensajes de error

    def __repr__(self):
        return f"Nodo({self.tipo}: '{self.nombre}')"


class SourceNode(Nodo):
    """
    Representa una Fuente (SOURCE):
    Es el punto de entrada de los datos al sistema. No recibe datos de otros nodos,
    solo emite tuplas hacia adelante en el grafo.
    """
    def __init__(self, nombre, linea):
        super().__init__(nombre, 'SOURCE', linea)
        self.eventos_emitidos = 0   # Contador para saber cuántas tuplas nacieron acá


class OperatorNode(Nodo):
    """
    Representa un Operador (OPERATOR):
    Procesa tuplas intermedias. Puede tener múltiples réplicas (paralelismo)
    para procesar eventos en paralelo mediante balanceo de carga Round-Robin.
    """
    def __init__(self, nombre, paralelismo, linea, tiempo_servicio=None):
        super().__init__(nombre, 'OPERATOR', linea)
        # Si el usuario no especificó réplicas, por defecto es 1
        self.paralelismo = paralelismo if paralelismo is not None and paralelismo > 0 else 1

        # Tiempo de servicio (Control I): unidades de tiempo que tarda esta réplica
        # en procesar una tupla. Queda en None si el operador se declaró con una
        # sintaxis antigua que todavía no lo especifica (ver Readme.txt, sección 5).
        self.tiempo_servicio = tiempo_servicio

        # Diccionario para llevar la cuenta de cuántas tuplas procesó cada réplica individual
        # Ejemplo: {0: 5, 1: 4} para 2 réplicas
        self.conteo_por_replica = {i: 0 for i in range(self.paralelismo)}

    def registrar_procesamiento(self, replica_id):
        """
        Aumenta el contador de tuplas procesadas por la réplica correspondiente.
        """
        if replica_id in self.conteo_por_replica:
            self.conteo_por_replica[replica_id] += 1


class SinkNode(Nodo):
    """
    Representa un Sumidero (SINK):
    Es el punto final del flujo de procesamiento (ej. una base de datos o consola).
    Recibe tuplas procesadas y no tiene conexiones de salida.
    """
    def __init__(self, nombre, linea):
        super().__init__(nombre, 'SINK', linea)
        # Lista donde guardamos todas las tuplas que llegaron exitosamente al sumidero
        self.tuplas_recibidas = []

    def recibir_tupla(self, tupla_info):
        """
        Guarda la tupla recibida junto con la información de su viaje por la topología.
        """
        self.tuplas_recibidas.append(tupla_info)


# -----------------------------------------------------------------------------
# TABLA DE SÍMBOLOS
# Maneja los identificadores declarados y previene errores semánticos básicos
# como declarar dos veces el mismo nodo o usar uno que nunca se creó.
# -----------------------------------------------------------------------------

class TablaSimbolos:
    """
    Tabla de símbolos encargada de almacenar y validar las declaraciones de nodos.
    """
    def __init__(self):
        # Diccionario nombre_nodo -> objeto Nodo
        self.simbolos = {}
        # Lista de errores semánticos encontrados durante el análisis
        self.errores = []

    def declarar_nodo(self, nombre, tipo, paralelismo, linea, tiempo_servicio=None):
        """
        Registra un nuevo nodo en la tabla. Si ya existe, añade un error semántico.

        'tiempo_servicio' solo aplica a nodos OPERATOR (Control I). Se deja como
        parámetro opcional para no romper las llamadas existentes de SOURCE/SINK
        y de las declaraciones de OPERATOR que todavía no lo especifican.
        """
        # Verificamos si el nombre ya fue usado antes
        if nombre in self.simbolos:
            nodo_previo = self.simbolos[nombre]
            mensaje = (f"[ERROR SEMÁNTICO] Línea {linea}: El identificador '{nombre}' ya fue "
                       f"declarado previamente como {nodo_previo.tipo} en la línea {nodo_previo.linea}.")
            self.errores.append(mensaje)
            return None

        # Validamos que el paralelismo no sea un número absurdo (como 0 o negativo)
        if tipo == 'OPERATOR' and paralelismo is not None and paralelismo <= 0:
            mensaje = (f"[ERROR SEMÁNTICO] Línea {linea}: El operador '{nombre}' debe tener al menos "
                       f"1 réplica (se especificó: {paralelismo}).")
            self.errores.append(mensaje)
            return None

        # Validamos que, si se especificó tiempo de servicio, sea un valor positivo
        if tipo == 'OPERATOR' and tiempo_servicio is not None and tiempo_servicio <= 0:
            mensaje = (f"[ERROR SEMÁNTICO] Línea {linea}: El operador '{nombre}' debe tener un "
                       f"TIEMPO_SERVICIO mayor a 0 (se especificó: {tiempo_servicio}).")
            self.errores.append(mensaje)
            return None

        # Creamos la instancia según el tipo de nodo
        if tipo == 'SOURCE':
            nuevo_nodo = SourceNode(nombre, linea)
        elif tipo == 'OPERATOR':
            nuevo_nodo = OperatorNode(nombre, paralelismo, linea, tiempo_servicio=tiempo_servicio)
        elif tipo == 'SINK':
            nuevo_nodo = SinkNode(nombre, linea)
        else:
            self.errores.append(f"[ERROR SEMÁNTICO] Línea {linea}: Tipo de nodo desconocido '{tipo}'.")
            return None

        # Guardamos en la tabla
        self.simbolos[nombre] = nuevo_nodo
        return nuevo_nodo

    def existe(self, nombre):
        """Revisa si el identificador existe en la tabla."""
        return nombre in self.simbolos

    def obtener(self, nombre):
        """Retorna el nodo asociado al nombre o None si no existe."""
        return self.simbolos.get(nombre, None)


# -----------------------------------------------------------------------------
# ESTRUCTURA Y VALIDACIÓN DEL GRAFO DE LA TOPOLOGÍA
# -----------------------------------------------------------------------------

class Topologia:
    """
    Representa el grafo dirigido de la topología de stream processing.
    Maneja las conexiones entre nodos y ejecuta las validaciones requeridas:
    - Grafo acíclico dirigido (DAG).
    - Fuentes sin entradas.
    - Sumideros sin salidas.
    - Conectividad completa (sin nodos aislados o huérfanos).
    """
    def __init__(self, tabla_simbolos):
        self.tabla = tabla_simbolos
        # Lista de aristas como tuplas (origen_nombre, destino_nombre, linea)
        self.aristas = []
        # Listas de adyacencia directa e inversa para recorrer el grafo con comodidad
        self.adyacentes = {}          # origen -> [destinos]
        self.predecesores = {}        # destino -> [orígenes]
        self.errores_grafo = []

        # Inicializamos las listas de adyacencia para cada nodo registrado en la tabla
        for nombre in self.tabla.simbolos:
            self.adyacentes[nombre] = []
            self.predecesores[nombre] = []

    def conectar(self, origen_nombre, destino_nombre, linea):
        """
        Agrega una arista dirigida entre dos nodos: origen -> destino.
        Valida que ambos nodos existan en la tabla de símbolos.
        """
        # Chequeamos que el nodo origen exista
        if not self.tabla.existe(origen_nombre):
            self.errores_grafo.append(
                f"[ERROR SEMÁNTICO] Línea {linea}: El nodo de origen '{origen_nombre}' no ha sido declarado."
            )
            return False

        # Chequeamos que el nodo destino exista
        if not self.tabla.existe(destino_nombre):
            self.errores_grafo.append(
                f"[ERROR SEMÁNTICO] Línea {linea}: El nodo de destino '{destino_nombre}' no ha sido declarado."
            )
            return False

        # Aseguramos que existan en los diccionarios de adyacencia
        if origen_nombre not in self.adyacentes:
            self.adyacentes[origen_nombre] = []
            self.predecesores[origen_nombre] = []
        if destino_nombre not in self.adyacentes:
            self.adyacentes[destino_nombre] = []
            self.predecesores[destino_nombre] = []

        # Evitamos aristas duplicadas exactas
        if destino_nombre in self.adyacentes[origen_nombre]:
            # Ya está conectado, avisamos pero no lo volvemos a meter
            return True

        # Agregamos la conexión en ambas listas
        self.aristas.append((origen_nombre, destino_nombre, linea))
        self.adyacentes[origen_nombre].append(destino_nombre)
        self.predecesores[destino_nombre].append(origen_nombre)
        return True

    def validar_topologia(self):
        """
        Ejecuta todas las reglas semánticas y estructurales sobre el grafo.
        Retorna True si la topología es válida, o False si tiene errores.
        """
        # 1. Validación de existencia de fuentes y sumideros
        fuentes = [n for n in self.tabla.simbolos.values() if n.tipo == 'SOURCE']
        sumideros = [n for n in self.tabla.simbolos.values() if n.tipo == 'SINK']

        if len(fuentes) == 0:
            self.errores_grafo.append(
                "[ERROR DE GRAFO] La topología no tiene ningún nodo SOURCE (fuente). Debe haber al menos uno."
            )

        if len(sumideros) == 0:
            self.errores_grafo.append(
                "[ERROR DE GRAFO] La topología no tiene ningún nodo SINK (sumidero). Debe haber al menos uno."
            )

        # 2. Validación de fuentes: no pueden tener conexiones entrantes (grado de entrada == 0)
        for f in fuentes:
            entrantes = self.predecesores.get(f.nombre, [])
            if len(entrantes) > 0:
                self.errores_grafo.append(
                    f"[ERROR DE GRAFO] El nodo SOURCE '{f.nombre}' no puede tener conexiones de entrada "
                    f"(recibe conexiones desde: {entrantes})."
                )

        # 3. Validación de sumideros: no pueden tener conexiones salientes (grado de salida == 0)
        for s in sumideros:
            salientes = self.adyacentes.get(s.nombre, [])
            if len(salientes) > 0:
                self.errores_grafo.append(
                    f"[ERROR DE GRAFO] El nodo SINK '{s.nombre}' no puede tener conexiones de salida "
                    f"(intenta conectarse a: {salientes})."
                )

        # 4. Detección de Ciclos (debe ser un DAG):
        # Usamos el algoritmo de coloreo de 3 estados:
        # BLANCO (0): no visitado, GRIS (1): visitando actualmente en la pila de recursión, NEGRO (2): completamente procesado.
        estado_visita = {nombre: 0 for nombre in self.tabla.simbolos}
        camino_actual = []

        def dfs_detectar_ciclo(nodo_actual):
            estado_visita[nodo_actual] = 1 # Pasamos a GRIS (en camino)
            camino_actual.append(nodo_actual)

            for vecino in self.adyacentes.get(nodo_actual, []):
                # Si encontramos un nodo en estado GRIS, ¡hay un ciclo!
                if estado_visita[vecino] == 1:
                    indice_inicio_ciclo = camino_actual.index(vecino)
                    ciclo_formado = camino_actual[indice_inicio_ciclo:] + [vecino]
                    texto_ciclo = " -> ".join(ciclo_formado)
                    self.errores_grafo.append(
                        f"[ERROR DE GRAFO] Se detectó un ciclo en la topología (debe ser un DAG): {texto_ciclo}"
                    )
                    return True
                elif estado_visita[vecino] == 0:
                    if dfs_detectar_ciclo(vecino):
                        return True

            # Marcamos como NEGRO (procesado por completo)
            estado_visita[nodo_actual] = 2
            camino_actual.pop()
            return False

        for nombre_nodo in self.tabla.simbolos:
            if estado_visita[nombre_nodo] == 0:
                dfs_detectar_ciclo(nombre_nodo)

        # 5. Validación de Alcanzabilidad desde Fuentes (sin nodos huérfanos)
        # Hacemos un recorrido hacia adelante desde todas las fuentes
        alcanzables_desde_fuente = set()
        cola = [f.nombre for f in fuentes]
        for f in fuentes:
            alcanzables_desde_fuente.add(f.nombre)

        while len(cola) > 0:
            actual = cola.pop(0)
            for sucesor in self.adyacentes.get(actual, []):
                if sucesor not in alcanzables_desde_fuente:
                    alcanzables_desde_fuente.add(sucesor)
                    cola.append(sucesor)

        # Revisamos qué nodos quedaron fuera
        for nombre, nodo in self.tabla.simbolos.items():
            if nombre not in alcanzables_desde_fuente:
                self.errores_grafo.append(
                    f"[ERROR DE GRAFO] El nodo '{nombre}' ({nodo.tipo}) no es alcanzable desde ninguna fuente."
                )

        # 6. Validación de Conexión a Sumideros (sin caminos ciegos)
        # Recorremos hacia atrás desde todos los sumideros
        llegan_a_sumidero = set()
        cola_inversa = [s.nombre for s in sumideros]
        for s in sumideros:
            llegan_a_sumidero.add(s.nombre)

        while len(cola_inversa) > 0:
            actual = cola_inversa.pop(0)
            for antecesor in self.predecesores.get(actual, []):
                if antecesor not in llegan_a_sumidero:
                    llegan_a_sumidero.add(antecesor)
                    cola_inversa.append(antecesor)

        for nombre, nodo in self.tabla.simbolos.items():
            if nombre not in llegan_a_sumidero:
                self.errores_grafo.append(
                    f"[ERROR DE GRAFO] El flujo desde el nodo '{nombre}' ({nodo.tipo}) nunca llega a ningún sumidero."
                )

        # Si no acumulamos ningún error en las listas, el grafo es válido
        total_errores = len(self.tabla.errores) + len(self.errores_grafo)
        return total_errores == 0


# -----------------------------------------------------------------------------
# SIMULADOR DE EVENTOS CON ROUND-ROBIN INDEPENDIENTE
# -----------------------------------------------------------------------------

class EventoEmision:
    """Representa una instrucción de emisión del DSL (EMIT "payload" TO fuente)."""
    def __init__(self, payload, fuente_nombre, linea):
        self.payload = payload
        self.fuente_nombre = fuente_nombre
        self.linea = linea


class Simulador:
    """
    Motor de simulación paso a paso de la topología.
    Implementa Round-Robin independiente por canal/arista de conexión.
    """
    def __init__(self, topologia):
        self.topologia = topologia
        self.contador_global_tuplas = 0

        # DECISIÓN DE DISEÑO CLAVE:
        # Diccionario para almacenar el puntero Round-Robin independiente por canal/arista.
        # Clave: (identificador_emisor, nombre_nodo_destino)
        # Donde identificador_emisor puede ser:
        # - El nombre de la fuente (ej. 'sensor')
        # - O la réplica específica de un operador (ej. 'filtro#0', 'filtro#1')
        # Así, si dos operadores replicados están conectados de forma adyacente (ej. Op1 -> Op2),
        # CADA réplica de Op1 mantiene su propio puntero local e independiente hacia las réplicas de Op2.
        self.punteros_round_robin = {}

    def obtener_siguiente_replica(self, id_emisor, nodo_destino):
        """
        Aplica Round-Robin para elegir la réplica del operador destino.
        Retorna el índice de la réplica seleccionada (de 0 a paralelismo - 1).
        """
        clave_canal = (id_emisor, nodo_destino.nombre)
        num_replicas = nodo_destino.paralelismo

        # Si es la primera vez que este emisor envía a este destino, iniciamos en 0
        if clave_canal not in self.punteros_round_robin:
            self.punteros_round_robin[clave_canal] = 0

        # Elegimos la réplica con la operación módulo (%)
        puntero_actual = self.punteros_round_robin[clave_canal]
        replica_elegida = puntero_actual % num_replicas

        # Avanzamos el puntero local del canal para el siguiente envío
        self.punteros_round_robin[clave_canal] = puntero_actual + 1

        return replica_elegida, puntero_actual

    def propagar_tupla(self, id_tupla, contenido, emisor_id, nombre_nodo_destino, ruta_recorrida, tiempo_acumulado=0):
        """
        Función recursiva que hace avanzar una tupla desde un emisor hacia un nodo destino.
        Maneja operadores replicados y sumideros finales.

        'tiempo_acumulado' viaja junto con 'ruta_recorrida' de la misma forma
        (por valor, en cada llamada recursiva), así que cada rama del recorrido
        mantiene su propio total sin depender de ningún acumulador global ni
        compartido entre eventos (Control I: tiempo total acumulado del evento).
        """
        nodo_destino = self.topologia.tabla.obtener(nombre_nodo_destino)
        if not nodo_destino:
            return

        # CASO 1: El destino es un OPERATOR
        if nodo_destino.tipo == 'OPERATOR':
            # Aplicamos Round-Robin independiente para este canal específico
            replica_id, turno = self.obtener_siguiente_replica(emisor_id, nodo_destino)

            # Registramos que esta réplica procesó la tupla
            nodo_destino.registrar_procesamiento(replica_id)

            # Identificador de esta réplica para sus propios envíos hacia adelante
            id_esta_replica = f"{nodo_destino.nombre}#r{replica_id}"
            nueva_ruta = ruta_recorrida + [f"{nodo_destino.nombre}[replica_{replica_id}]"]

            # Tiempo de servicio (Control I): se suma EXACTAMENTE UNA VEZ por
            # operador atravesado, sin importar cuál réplica lo procese (todas
            # las réplicas de un mismo OPERATOR comparten su único
            # TIEMPO_SERVICIO). Si el operador viene de una declaración legacy
            # sin TIEMPO_SERVICIO (tiempo_servicio=None), no aporta tiempo al
            # total -- pero tampoco se intenta sumar None (evita la excepción).
            if nodo_destino.tiempo_servicio is not None:
                nuevo_tiempo_acumulado = tiempo_acumulado + nodo_destino.tiempo_servicio
            else:
                nuevo_tiempo_acumulado = tiempo_acumulado
                print(f"    |   -> [ADVERTENCIA] '{nodo_destino.nombre}' no tiene TIEMPO_SERVICIO definido "
                      f"(sintaxis legacy); no aporta tiempo al total de este evento.")

            # Mostramos el paso por consola en estilo de simulación clara
            print(f"    |-- [CANAL] Desde '{emisor_id}' -> '{nodo_destino.nombre}'")
            print(f"    |   -> Round-Robin (turno {turno}): asignado a REPLICA #{replica_id} de '{nodo_destino.nombre}'")
            print(f"    |   -> [PROCESANDO] Replica #{replica_id} procesa: \"{contenido}\"")

            # La réplica reenvía la tupla a todos los nodos siguientes conectados a este operador
            siguientes_nodos = self.topologia.adyacentes.get(nodo_destino.nombre, [])
            for siguiente in siguientes_nodos:
                self.propagar_tupla(id_tupla, contenido, id_esta_replica, siguiente, nueva_ruta, nuevo_tiempo_acumulado)

        # CASO 2: El destino es un SINK
        elif nodo_destino.tipo == 'SINK':
            nueva_ruta = ruta_recorrida + [nodo_destino.nombre]
            info_final = {
                'id_tupla': id_tupla,
                'contenido': contenido,
                'origen': ruta_recorrida[0],
                'ruta_completa': nueva_ruta,
                'tiempo_total': tiempo_acumulado
            }
            nodo_destino.recibir_tupla(info_final)
            ruta_str = " -> ".join(nueva_ruta)
            print(f"    |-- [SUMIDERO] '{nodo_destino.nombre}' RECIBIO la tupla #{id_tupla}")
            print(f"    |   -> Camino recorrido: {ruta_str}")

            # Formato de salida literal exigido por el Control (Ejemplo de Salida
            # del enunciado): "Evento N: FUENTE f1 -> OPERADOR op1 (T: 5) -> SUMIDERO s1"
            # seguido de "Tiempo total acumulado: 5".
            print(f"    |   -> {self._formatear_linea_evento(id_tupla, nueva_ruta)}")
            print(f"    |   -> Tiempo total acumulado: {tiempo_acumulado}")

    def _formatear_linea_evento(self, id_tupla, ruta_completa):
        """
        Construye la línea con el formato literal del enunciado del Control a
        partir de la ruta completa de una rama del evento (FUENTE -> ... ->
        SUMIDERO), consultando el TIEMPO_SERVICIO real de cada operador
        atravesado en esa ruta.
        """
        partes = []
        ultimo_indice = len(ruta_completa) - 1
        for indice, paso in enumerate(ruta_completa):
            if indice == 0:
                partes.append(f"FUENTE {paso}")
            elif indice == ultimo_indice:
                partes.append(f"SUMIDERO {paso}")
            else:
                # 'paso' viene como 'nombre[replica_N]'; el TIEMPO_SERVICIO
                # pertenece al OPERATOR, no a la réplica individual.
                nombre_operador = paso.split('[')[0]
                nodo_operador = self.topologia.tabla.obtener(nombre_operador)
                if nodo_operador and nodo_operador.tiempo_servicio is not None:
                    partes.append(f"OPERADOR {nombre_operador} (T: {nodo_operador.tiempo_servicio})")
                else:
                    partes.append(f"OPERADOR {nombre_operador} (T: sin definir)")
        return f"Evento {id_tupla}: " + " -> ".join(partes)

    def simular(self, lista_emisiones):
        """
        Ejecuta la lista completa de emisiones definidas en el archivo DSL.
        """
        print("\n" + "=" * 80)
        print(" INICIANDO SIMULACIÓN DE EVENTOS EN LA TOPOLOGÍA")
        print("=" * 80)

        if len(lista_emisiones) == 0:
            print("[AVISO] No se encontraron instrucciones de emisión (EMIT) para simular.")
            return

        for emision in lista_emisiones:
            self.contador_global_tuplas += 1
            id_tupla = self.contador_global_tuplas
            fuente_nombre = emision.fuente_nombre
            contenido = emision.payload

            # Validamos que la fuente exista y sea realmente de tipo SOURCE
            nodo_fuente = self.topologia.tabla.obtener(fuente_nombre)
            if not nodo_fuente:
                print(f"[ERROR EN SIMULACIÓN] Línea {emision.linea}: La fuente '{fuente_nombre}' no existe.")
                continue

            if nodo_fuente.tipo != 'SOURCE':
                print(f"[ERROR EN SIMULACIÓN] Línea {emision.linea}: El nodo '{fuente_nombre}' no es un SOURCE.")
                continue

            # Registramos la emisión en la fuente
            nodo_fuente.eventos_emitidos += 1

            print(f"\n>>> [EVENTO #{id_tupla}] Emitiendo tupla desde SOURCE '{fuente_nombre}'...")
            print(f"    Payload: \"{contenido}\"")

            # Enviamos la tupla a todos los nodos conectados a la salida de esta fuente
            destinos = self.topologia.adyacentes.get(fuente_nombre, [])
            ruta_inicial = [fuente_nombre]

            for destino in destinos:
                self.propagar_tupla(id_tupla, contenido, fuente_nombre, destino, ruta_inicial)

        # Imprimimos el reporte final de estadísticas
        self.mostrar_reporte_estadisticas()

    def mostrar_reporte_estadisticas(self):
        """
        Muestra un resumen ordenado y profesional de las métricas de la simulación.
        """
        print("\n" + "=" * 80)
        print(" REPORTE FINAL DE LA SIMULACIÓN DE STREAM PROCESSING")
        print("=" * 80)

        print(f"\n[1] TOTAL DE TUPLAS EMITIDAS POR FUENTES: {self.contador_global_tuplas}")
        for nombre, nodo in self.topologia.tabla.simbolos.items():
            if nodo.tipo == 'SOURCE':
                print(f"    - Fuente '{nombre}': {nodo.eventos_emitidos} tupla(s) emitida(s)")

        print("\n[2] BALANCEO DE CARGA POR OPERADOR Y RÉPLICAS:")
        for nombre, nodo in self.topologia.tabla.simbolos.items():
            if nodo.tipo == 'OPERATOR':
                total_op = sum(nodo.conteo_por_replica.values())
                print(f"    - Operador '{nombre}' (Total: {total_op} tuplas procesadas, Paralelismo: {nodo.paralelismo}):")
                for rep_id, conteo in nodo.conteo_por_replica.items():
                    porcentaje = (conteo / total_op * 100) if total_op > 0 else 0.0
                    barra = "#" * int(porcentaje / 5)
                    print(f"        * Réplica #{rep_id}: {conteo:2d} tupla(s) [{porcentaje:5.1f}%] {barra}")

        print("\n[3] RESULTADOS EN SUMIDEROS (SINKS):")
        for nombre, nodo in self.topologia.tabla.simbolos.items():
            if nodo.tipo == 'SINK':
                print(f"    - Sumidero '{nombre}': {len(nodo.tuplas_recibidas)} tupla(s) recolectada(s)")
                for t in nodo.tuplas_recibidas:
                    print(f"        * Tupla #{t['id_tupla']} [\"{t['contenido']}\"]")

        print("=" * 80 + "\n")
