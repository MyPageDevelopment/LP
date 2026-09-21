# =======================================================
# topology.py - Modelo de Topología, Validación y Simulación
# =======================================================

class Nodo:
    def __init__(self, nombre, tipo, linea, tiempo_servicio=0, replicas=1):
        self.nombre = nombre
        self.tipo = tipo  # 'FUENTE', 'OPERADOR' o 'SUMIDERO'
        self.linea = linea
        self.tiempo_servicio = tiempo_servicio
        self.replicas = replicas
        self.conteo_replicas = [0] * replicas
        self.tuplas_recibidas = []  # para sumideros


class Topologia:
    def __init__(self):
        self.nodos = {}
        self.adyacentes = {}      # origen -> [destinos]
        self.predecesores = {}    # destino -> [origenes]
        self.errores = []
        self.eventos_a_simular = 0

    def agregar_nodo(self, nodo):
        if nodo.nombre in self.nodos:
            previo = self.nodos[nodo.nombre]
            self.errores.append(
                f"[Error Semántico] Línea {nodo.linea}: El identificador '{nodo.nombre}' ya fue declarado en la línea {previo.linea}."
            )
            return False

        if nodo.tipo == 'OPERADOR':
            if nodo.tiempo_servicio <= 0:
                self.errores.append(
                    f"[Error Semántico] Línea {nodo.linea}: OPERADOR '{nodo.nombre}' debe tener un TIEMPO_SERVICIO mayor a 0."
                )
                return False
            if nodo.replicas <= 0:
                self.errores.append(
                    f"[Error Semántico] Línea {nodo.linea}: OPERADOR '{nodo.nombre}' debe tener al menos 1 réplica."
                )
                return False

        self.nodos[nodo.nombre] = nodo
        self.adyacentes[nodo.nombre] = []
        self.predecesores[nodo.nombre] = []
        return True

    def conectar(self, origen, destino, linea):
        if origen not in self.nodos:
            self.errores.append(f"[Error Semántico] Línea {linea}: El nodo origen '{origen}' no existe.")
            return False
        if destino not in self.nodos:
            self.errores.append(f"[Error Semántico] Línea {linea}: El nodo destino '{destino}' no existe.")
            return False

        if destino not in self.adyacentes[origen]:
            self.adyacentes[origen].append(destino)
            self.predecesores[destino].append(origen)
        return True

    def validar(self):
        """Valida que la topología cumpla las restricciones de un DAG válido de Stream Processing."""
        fuentes = [n for n in self.nodos.values() if n.tipo == 'FUENTE']
        sumideros = [n for n in self.nodos.values() if n.tipo == 'SUMIDERO']

        # 1. Existencia mínima de fuente y sumidero
        if not fuentes:
            self.errores.append("[Error Grafo] La topología debe tener al menos una FUENTE.")
        if not sumideros:
            self.errores.append("[Error Grafo] La topología debe tener al menos un SUMIDERO.")

        # 2. Fuentes sin entradas y Sumideros sin salidas
        for f in fuentes:
            if len(self.predecesores[f.nombre]) > 0:
                self.errores.append(f"[Error Grafo] La FUENTE '{f.nombre}' no puede tener conexiones de entrada.")

        for s in sumideros:
            if len(self.adyacentes[s.nombre]) > 0:
                self.errores.append(f"[Error Grafo] El SUMIDERO '{s.nombre}' no puede tener conexiones de salida.")

        # 3. Detección de ciclos con DFS (Coloreo: 0=Blanco, 1=Gris, 2=Negro)
        estado = {nombre: 0 for nombre in self.nodos}

        def hay_ciclo(actual, camino):
            estado[actual] = 1  # Marcamos como gris (en proceso)
            camino.append(actual)

            for vecino in self.adyacentes.get(actual, []):
                if estado[vecino] == 1:
                    idx = camino.index(vecino)
                    ciclo_str = " -> ".join(camino[idx:] + [vecino])
                    self.errores.append(f"[Error Grafo] Se detectó un ciclo en la topología: {ciclo_str}")
                    return True
                elif estado[vecino] == 0:
                    if hay_ciclo(vecino, camino):
                        return True

            estado[actual] = 2  # Marcamos como negro (completado)
            camino.pop()
            return False

        for nombre in self.nodos:
            if estado[nombre] == 0:
                hay_ciclo(nombre, [])

        # 4. Alcanzabilidad desde fuentes (no permitir componentes desconectados)
        alcanzables = set()
        cola = [f.nombre for f in fuentes]
        for f in fuentes:
            alcanzables.add(f.nombre)

        while cola:
            curr = cola.pop(0)
            for v in self.adyacentes.get(curr, []):
                if v not in alcanzables:
                    alcanzables.add(v)
                    cola.append(v)

        for nombre in self.nodos:
            if nombre not in alcanzables:
                self.errores.append(f"[Error Grafo] El nodo '{nombre}' no es alcanzable desde ninguna FUENTE.")

        # 5. Todo nodo debe alcanzar al menos un sumidero
        llega_sumidero = set()
        cola_rev = [s.nombre for s in sumideros]
        for s in sumideros:
            llega_sumidero.add(s.nombre)

        while cola_rev:
            curr = cola_rev.pop(0)
            for pred in self.predecesores.get(curr, []):
                if pred not in llega_sumidero:
                    llega_sumidero.add(pred)
                    cola_rev.append(pred)

        for nombre in self.nodos:
            if nombre not in llega_sumidero:
                self.errores.append(f"[Error Grafo] El nodo '{nombre}' no tiene camino hacia ningún SUMIDERO.")

        return len(self.errores) == 0

    def simular(self):
        """Simula la emisión de tuplas y el procesamiento con balanceo Round-Robin."""
        print("\n" + "=" * 80)
        print(" INICIANDO SIMULACIÓN DE EVENTOS EN LA TOPOLOGÍA")
        print("=" * 80)

        # Estado independiente de Round-Robin por canal: (nodo_emisor, replica_emisor, nodo_destino) -> turno
        turnos_rr = {}

        def obtener_siguiente_replica(emisor, replica_emisor, destino, num_replicas):
            clave = (emisor, replica_emisor, destino)
            turno = turnos_rr.get(clave, 0)
            replica_elegida = turno % num_replicas
            turnos_rr[clave] = turno + 1
            return replica_elegida, turno

        def propagar(id_evento, emisor_id, emisor_rep, destino_nombre, ruta, tiempo_acumulado):
            nodo_dest = self.nodos[destino_nombre]

            if nodo_dest.tipo == 'OPERADOR':
                rep_id, turno = obtener_siguiente_replica(
                    emisor_id, emisor_rep, destino_nombre, nodo_dest.replicas
                )
                nodo_dest.conteo_replicas[rep_id] += 1
                tiempo_acumulado += nodo_dest.tiempo_servicio
                ruta.append(f"{destino_nombre}[replica_{rep_id}]")

                print(f"    |-- [CANAL] Desde '{emisor_id}' -> '{destino_nombre}'")
                print(f"    |   -> Round-Robin (turno {turno}): asignado a REPLICA #{rep_id} de '{destino_nombre}'")
                print(f"    |   -> [PROCESANDO] Replica #{rep_id} procesa: \"tupla_sintetica_{id_evento}\"")

                for siguiente in self.adyacentes.get(destino_nombre, []):
                    propagar(id_evento, f"{destino_nombre}#r{rep_id}", rep_id, siguiente, list(ruta), tiempo_acumulado)

            elif nodo_dest.tipo == 'SUMIDERO':
                ruta.append(destino_nombre)
                nodo_dest.tuplas_recibidas.append(id_evento)

                print(f"    |-- [SUMIDERO] '{destino_nombre}' RECIBIO la tupla #{id_evento}")
                print(f"    |   -> Camino recorrido: {' -> '.join(ruta)}")

                # Formato oficial del Control:
                # "Evento N: FUENTE f1 -> OPERADOR op1 (T: 5) -> SUMIDERO s1"
                partes = []
                for idx, paso in enumerate(ruta):
                    if idx == 0:
                        partes.append(f"FUENTE {paso}")
                    elif idx == len(ruta) - 1:
                        partes.append(f"SUMIDERO {paso}")
                    else:
                        op_nombre = paso.split('[')[0]
                        op_obj = self.nodos[op_nombre]
                        partes.append(f"OPERADOR {op_nombre} (T: {op_obj.tiempo_servicio})")

                print(f"    |   -> Evento {id_evento}: {' -> '.join(partes)}")
                print(f"    |   -> Tiempo total acumulado: {tiempo_acumulado}")

        # Ejecutar los eventos
        fuentes = [n for n in self.nodos.values() if n.tipo == 'FUENTE']
        for ev in range(1, self.eventos_a_simular + 1):
            for f in fuentes:
                print(f"\n>>> [EVENTO #{ev}] Emitiendo tupla desde SOURCE '{f.nombre}'...")
                print(f"    Payload: \"tupla_sintetica_{ev}\"")
                for destino in self.adyacentes.get(f.nombre, []):
                    propagar(ev, f.nombre, 0, destino, [f.nombre], 0)

        # Reporte final
        print("\n" + "=" * 80)
        print(" REPORTE FINAL DE LA SIMULACIÓN DE STREAM PROCESSING")
        print("=" * 80)
        print(f"\n[1] TOTAL DE TUPLAS EMITIDAS POR FUENTES: {self.eventos_a_simular}")
        for f in fuentes:
            print(f"    - Fuente '{f.nombre}': {self.eventos_a_simular} tupla(s) emitida(s)")

        print("\n[2] BALANCEO DE CARGA POR OPERADOR Y RÉPLICAS:")
        for nodo in self.nodos.values():
            if nodo.tipo == 'OPERADOR':
                total = sum(nodo.conteo_replicas)
                print(f"    - Operador '{nodo.nombre}' (Total: {total} tuplas, Paralelismo: {nodo.replicas}):")
                for rep, cnt in enumerate(nodo.conteo_replicas):
                    porc = (cnt / total * 100) if total > 0 else 0
                    barras = "#" * int(porc / 5)
                    print(f"        * Réplica #{rep}:  {cnt} tupla(s) [{porc:5.1f}%] {barras}")

        print("\n[3] RESULTADOS EN SUMIDEROS (SINKS):")
        for nodo in self.nodos.values():
            if nodo.tipo == 'SUMIDERO':
                print(f"    - Sumidero '{nodo.nombre}': {len(nodo.tuplas_recibidas)} tupla(s) recolectada(s)")
                for t_id in nodo.tuplas_recibidas:
                    print(f"        * Tupla #{t_id} [\"tupla_sintetica_{t_id}\"]")

        print("=" * 80)
        print("\n[ÉXITO] Ejecución y simulación finalizadas correctamente.\n")
