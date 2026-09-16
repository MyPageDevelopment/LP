================================================================================
  TAREA SEMESTRAL: INTÉRPRETE DE TOPOLOGÍAS DE STREAM PROCESSING
  Asignatura : Lenguajes y Autómatas / Compiladores
  Carrera    : Ingeniería Civil en Informática / Ingeniería de Ejecución en Computación
  Semestre   : Primer Semestre
================================================================================

1. DESCRIPCIÓN GENERAL DEL PROYECTO
--------------------------------------------------------------------------------
Este proyecto consiste en la implementación completa de un compilador e intérprete
para un Lenguaje Específico de Dominio (DSL) orientado a la definición, validación
y simulación de topologías de procesamiento de flujos de datos en tiempo real
(Stream Processing).

El sistema permite declarar componentes distribuidos (Fuentes, Operadores con
múltiples réplicas en paralelo y Sumideros), conectar dichos componentes formando
un Grafo Dirigido Acíclico (DAG), validar las reglas estructurales y semánticas
de la topología, y finalmente simular la inyección y tránsito paso a paso de tuplas
o eventos a través de los nodos y canales de comunicación.


2. ESTRUCTURA DE ARCHIVOS DE LA ENTREGA
--------------------------------------------------------------------------------
El proyecto se entrega dividido en módulos claros, legibles y comentados:

  * lexer.py    : Analizador léxico implementado con PLY (lex). Reconoce tokens,
                  palabras reservadas, literales, comentarios y rastrea los
                  números de línea para un reporte preciso de errores.
  * parser.py   : Analizador sintáctico implementado con PLY (yacc). Define la
                  gramática BNF del DSL, procesa declaraciones, conexiones
                  simples y encadenadas, e instrucciones de emisión.
  * topology.py : Contiene la lógica del dominio:
                  - Clases de nodos (SourceNode, OperatorNode, SinkNode).
                  - Tabla de símbolos para control de identificadores y duplicados.
                  - Estructura del Grafo y validación completa de DAG (detección
                    de ciclos, grados de entrada/salida y alcanzabilidad).
                  - Motor de simulación de eventos con Round-Robin independiente.
  * main.py     : Punto de entrada de la aplicación por consola (CLI). Lee el
                  archivo .dsl pasado por argumento (sys.argv), orquesta el parser,
                  valida la topología y despliega la simulación.
  * Makefile    : Automatizador de tareas con reglas estándar: install, run,
                  clean y test.
  * test.dsl    : Archivo de prueba con un caso representativo que incluye fuente,
                  dos operadores adyacentes replicados, sumidero y eventos.
  * Readme.txt  : Este documento con instrucciones y justificación de diseño.


3. REQUISITOS E INSTALACIÓN
--------------------------------------------------------------------------------
El proyecto requiere Python 3.8 o superior y la biblioteca PLY (Python Lex-Yacc).

Instalación automática mediante Make:
    make install

Instalación manual mediante pip:
    pip install ply


4. MODO DE USO Y EJECUCIÓN
--------------------------------------------------------------------------------
Para ejecutar el intérprete con el archivo de prueba incluido:

  Opción 1 (Usando Make):
      make run

  Opción 2 (Usando Python directamente):
      python main.py test.dsl

Para ejecutar con cualquier otro archivo .dsl personalizado:
      python main.py ruta/a/mi_topologia.dsl

Para limpiar los archivos temporales y la caché de Python / PLY:
      make clean


5. SINTAXIS DEL LENGUAJE (DSL)
--------------------------------------------------------------------------------
El DSL admite una sintaxis intuitiva y flexible:

a) Declaración de Fuentes (SOURCE):
   SOURCE nombre_fuente;

b) Declaración de Operadores (OPERATOR):
   OPERATOR nombre_operador;                 // Asume paralelismo 1 por defecto
   OPERATOR nombre_operador PARALLEL 3;      // Con 3 réplicas en paralelo
   OPERATOR nombre_operador [PARALLEL = 3];  // Sintaxis alternativa con corchetes

c) Declaración de Sumideros (SINK):
   SINK nombre_sumidero;

d) Conexiones del Grafo:
   fuente -> operador -> sumidero;           // Conexiones encadenadas
   CONNECT fuente -> operador;               // Palabra opcional CONNECT

e) Emisión de Eventos / Tuplas:
   EMIT "Carga útil del evento" TO nombre_fuente;

f) Comentarios:
   // Comentario de una línea
   # Comentario de una línea estilo script
   /* Comentario
      multilínea en bloque */


6. VALIDACIONES SEMÁNTICAS Y ESTRUCTURALES DEL GRAFO
--------------------------------------------------------------------------------
El intérprete no se limita a revisar la sintaxis; antes de simular, valida que
el grafo represente una topología coherente de Stream Processing:

  1. Tabla de Símbolos:
     - No se permiten identificadores duplicados.
     - No se pueden conectar o emitir tuplas a nodos que no hayan sido declarados.
     - El paralelismo de los operadores debe ser un entero estrictamente mayor a 0.

  2. Estructura de la Topología:
     - Debe existir al menos una Fuente (SOURCE) y al menos un Sumidero (SINK).
     - Fuentes puras: Las fuentes tienen grado de entrada 0 (no pueden recibir
       conexiones de otros nodos).
     - Sumideros puros: Los sumideros tienen grado de salida 0 (no pueden enviar
       conexiones hacia otros nodos).
     - Aciclicidad (DAG): Se ejecuta un algoritmo DFS con coloreo de 3 estados
       (blanco, gris, negro) para detectar y reportar ciclos dirigidos.
     - Alcanzabilidad desde Fuentes: Todo operador y sumidero debe ser alcanzable
       mediante un camino directo desde alguna fuente (sin nodos aislados).
     - Salida a Sumidero: Todo camino en el grafo debe terminar en un sumidero
       (evita "caminos ciegos" u operadores huérfanos).


================================================================================
7. JUSTIFICACIÓN DE DISEÑO: OPERADORES REPLICADOS ADYACENTES
================================================================================
Uno de los desafíos conceptuales más importantes en el diseño de motores de
Stream Processing surge cuando existen dos operadores replicados adyacentes, es
decir, una conexión lógica entre un operador A (con N réplicas) y un operador B
(con M réplicas):

        [ OpA_0 ] ----\ /---- [ OpB_0 ]
                       X  ---- [ OpB_1 ]
        [ OpA_1 ] ----/ \---- [ OpB_2 ]

¿Cómo deben distribuirse las tuplas generadas o procesadas por las réplicas de OpA
hacia las réplicas de OpB?

Para resolver esto, evaluamos dos alternativas de diseño:

--------------------------------------------------------------------------------
ALTERNATIVA 1 (Descartada): Round-Robin Centralizado / Estado Global Compartido
--------------------------------------------------------------------------------
En este esquema existe un único puntero global para la arista abstracta (OpA -> OpB).
Cada vez que CUALQUIER réplica de OpA termina de procesar una tupla y quiere emitir
hacia OpB, consulta y modifica este contador global:
    replica_elegida = (contador_global++) % M;

¿Por qué se descartó esta alternativa?
  1. Cuello de botella y contención: En un entorno de procesamiento distribuido
     o concurrente real, un estado global compartido obliga a usar cerrojos
     (locks / mutexes) o variables atómicas. Cuando el caudal de tuplas es alto,
     las réplicas de OpA compiten por acceder al mismo recurso, degradando el
     rendimiento del sistema.
  2. Ruptura del desacoplamiento: Si una réplica de OpA se ejecuta en un nodo
     físico distinto (worker separado), depender de un contador centralizado
     genera latencia de red innecesaria y constituye un punto único de falla (SPOF).
  3. No refleja la arquitectura de sistemas reales: Motores industriales como
     Apache Storm, Apache Flink o Spark Streaming no utilizan un coordinador
     centralizado para cada emisión individual de tuplas entre tareas.

--------------------------------------------------------------------------------
ALTERNATIVA 2 (Adoptada): Round-Robin Independiente por Arista/Canal de Conexión
--------------------------------------------------------------------------------
Nuestra decisión de diseño consiste en que CADA réplica emisora (y cada fuente)
mantiene su propio contador/puntero Round-Robin local e independiente para cada
nodo de destino al que está conectada:

    Clave de Canal = (id_instancia_emisora, id_nodo_destino)
    Ejemplo: ('filtro_ruido#r0', 'detector_anomalias') -> puntero local
             ('filtro_ruido#r1', 'detector_anomalias') -> puntero local

Ventajas y Fundamentos de esta Decisión:
  1. Autonomía y Desacoplamiento de Réplicas:
     Cada réplica de OpA es un worker completamente autónomo. Al enviar una tupla
     a OpB, consulta únicamente su puntero local:
         replica_OpB = (puntero_local_de_esta_replica++) % M;
     No requiere comunicarse ni sincronizarse con las demás réplicas de OpA.
  2. Ausencia de Locks y Escalabilidad Horizontal:
     Al no compartir memoria ni variables entre emisores, no existe contención.
     Si aumentamos las réplicas de OpA de 2 a 100, la lógica de balanceo no sufre
     ninguna penalización de concurrencia.
  3. Coherencia con la Realidad de Sistemas Distribuidos:
     En Apache Storm y Apache Flink, cada tarea de origen (upstream task) posee
     un buffer de salida por cada canal hacia las tareas de destino (downstream tasks).
     La estrategia "Shuffle Grouping" o "Round-Robin" se ejecuta localmente en la
     tarea emisora, seleccionando cíclicamente el canal de salida hacia las réplicas
     del siguiente paso.
  4. Distribución Uniforme a Largo Plazo:
     Como cada réplica emisora distribuye sus propias tuplas de forma balanceada
     (0, 1, 2, 0, 1, 2...), la sumatoria global de tuplas que llega a las réplicas
     de destino se mantiene perfectamente balanceada cuando el flujo de entrada
     es constante.

En el reporte final generado por nuestro simulador para el caso `test.dsl`, se
puede observar claramente este comportamiento: las 6 tuplas emitidas por la fuente
se dividen en partes iguales (3 y 3) entre las 2 réplicas de `filtro_ruido`, y
luego cada una de esas réplicas reparte sus tuplas de forma independiente entre
las 3 réplicas de `detector_anomalias`, logrando que cada réplica de este último
procese exactamente 2 tuplas (33.3% cada una), demostrando el balance perfecto.


8. CONCLUSIONES DEL DESARROLLO
--------------------------------------------------------------------------------
El desarrollo de este intérprete permitió aplicar de forma práctica los conceptos
teóricos de la asignatura:
  - Análisis Léxico: Manejo de expresiones regulares, tokens y números de línea.
  - Análisis Sintáctico: Especificación de gramáticas formales libres de contexto,
    resolución de reglas de reducción y construcción de estructuras en memoria.
  - Análisis Semántico: Validación en dos fases (tabla de símbolos para tipos
    y unicidad; algoritmos sobre grafos para validar propiedades de DAG).
  - Sistemas Distribuidos: Modelado de balanceo de carga sin estado compartido
    mediante Round-Robin local por canal.
