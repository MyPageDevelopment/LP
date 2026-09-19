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
                  gramática BNF del DSL oficial y legacy (ver sección 5),
                  procesa declaraciones (incluyendo TIEMPO_SERVICIO), conexiones
                  simples y encadenadas, instrucciones de emisión y SIMULAR <n>.
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
  * test.dsl    : Archivo de prueba con un caso representativo (sintaxis OFICIAL
                  del Control, sección 5.1) que incluye una fuente, dos
                  operadores adyacentes replicados con TIEMPO_SERVICIO, un
                  sumidero, y SIMULAR para generar los eventos.
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
El DSL implementa la sintaxis OFICIAL exigida por el Control I (5.1). También
conserva, como compatibilidad técnica claramente separada (5.2), el dialecto
en inglés con el que se construyó originalmente el proyecto. test.dsl (la
demostración principal) usa únicamente la sintaxis oficial de 5.1.

5.1 SINTAXIS OFICIAL (Control I)
--------------------------------------------------------------------------------

a) Declaración de una Fuente:
   FUENTE nombre_fuente;

b) Declaración de un Operador (TIEMPO_SERVICIO es OBLIGATORIO):
   OPERADOR nombre_operador TIEMPO_SERVICIO 5;              // 1 réplica por defecto
   OPERADOR nombre_operador TIEMPO_SERVICIO 5 REPLICAS 2;   // con réplicas

   IMPORTANTE: al usar la palabra OFICIAL "OPERADOR", TIEMPO_SERVICIO es
   obligatorio. "OPERADOR nombre;" o "OPERADOR nombre REPLICAS 2;" (sin
   TIEMPO_SERVICIO) se RECHAZAN con un error semántico explícito -- el nodo no
   se registra -- porque el Control exige que todo operador declare su tiempo
   de servicio. Esta restricción NO aplica a la palabra legacy "OPERATOR"
   (ver 5.2), que existe solo como compatibilidad técnica.

   TIEMPO_SERVICIO durante la simulación: cada vez que una tupla atraviesa un
   operador, su TIEMPO_SERVICIO se suma EXACTAMENTE UNA VEZ al tiempo total
   acumulado de ese evento (todas las réplicas de un mismo operador comparten
   su único TIEMPO_SERVICIO). FUENTE y SUMIDERO no aportan tiempo (el Control
   solo pide sumar "los tiempos de servicio de los operadores atravesados").

c) Declaración de un Sumidero:
   SUMIDERO nombre_sumidero;

d) Conexión entre nodos:
   CONECTAR id_origen A id_destino;

   Reutiliza exactamente la misma validación de existencia de nodos que el
   resto del lenguaje (Topologia.conectar). No admite encadenamiento -- el
   Control especifica únicamente la forma binaria; encadenar conexiones sigue
   siendo una extensión exclusiva de la sintaxis legacy con '->' (ver 5.2).

e) Simulación automática de eventos:
   SIMULAR cantidad_eventos;

   Genera automáticamente esa cantidad TOTAL de eventos (no por fuente) con
   contenido sintético ("tupla_sintetica_N"). El enunciado del Control no
   especifica qué ocurre con múltiples FUENTEs; decidimos (análogamente a
   como ya resolvimos el Round-Robin de réplicas) repartir los N eventos de
   forma circular entre todas las FUENTEs declaradas ANTES de la instrucción
   SIMULAR en el archivo (las FUENTEs deben declararse antes de usarse, igual
   que para CONECTAR). Ejemplo: con 2 fuentes y SIMULAR 5, la primera recibe
   3 eventos y la segunda 2 (orden: fuente1, fuente2, fuente1, fuente2,
   fuente1).

   Salida por evento (formato literal exigido por el Control): al llegar a un
   SUMIDERO se imprime, además de la traza detallada existente ([CANAL],
   [PROCESANDO], [SUMIDERO]):
       Evento 1: FUENTE f1 -> OPERADOR op1 (T: 5) -> SUMIDERO s1
       Tiempo total acumulado: 5
   Si la ruta atraviesa varios operadores, cada uno aparece con su propio
   "(T: n)" en el orden real recorrido.

f) Punto y coma (";") al final de cada instrucción: el Control NO especifica
   ningún terminador de instrucción -- ninguno de sus ejemplos de sintaxis
   muestra ";". Su uso es una DECISIÓN PROPIA del equipo, heredada del diseño
   original del DSL, no una exigencia del enunciado. Se documenta aquí
   explícitamente para no atribuir al Control algo que no dice.

g) Comentarios (extensión propia, no exigida por el Control):
   // Comentario de una línea
   # Comentario de una línea estilo script
   /* Comentario
      multilínea en bloque */

5.2 SINTAXIS LEGACY (compatibilidad técnica -- NO es la sintaxis oficial)
--------------------------------------------------------------------------------
Dialecto en inglés con el que se construyó originalmente el proyecto,
conservado únicamente como compatibilidad técnica. NO se usa en test.dsl (la
demostración principal usa exclusivamente la sintaxis oficial de 5.1).

   SOURCE nombre_fuente;                     // alias legacy de FUENTE
   OPERATOR nombre_operador;                 // NO exige TIEMPO_SERVICIO (ver nota)
   OPERATOR nombre_operador PARALLEL 3;
   OPERATOR nombre_operador [PARALLEL = 3];  // sintaxis alternativa con corchetes
   SINK nombre_sumidero;                     // alias legacy de SUMIDERO
   fuente -> operador -> sumidero;           // conexión encadenada con flecha
   CONNECT fuente -> operador;               // alias legacy de CONECTAR (con '->')
   EMIT "texto" TO fuente;                   // evento manual, contenido explícito
   SIMULATE { EMIT "..." TO fuente; }        // bloque agrupador, sin efecto propio

   NOTA (por qué "OPERATOR" sí puede omitir TIEMPO_SERVICIO): la exigencia de
   TIEMPO_SERVICIO obligatorio está atada específicamente a la palabra OFICIAL
   "OPERADOR" (así lo pide el Control). La palabra legacy "OPERATOR" puede
   seguir declarándose sin TIEMPO_SERVICIO por compatibilidad técnica
   temporal; en ese caso tiempo_servicio queda en None (no se inventa un
   valor) y el simulador imprime una advertencia visible en cada evento que
   lo atraviesa -- nunca provoca una excepción.

   NOTA (relación EMIT / SIMULATE{} / SIMULAR): los tres coexisten sobre el
   mismo motor de simulación (Simulador, Round-Robin, propagación por el
   grafo). EMIT es un evento manual con contenido elegido por quien escribe
   el .dsl (útil para pruebas dirigidas); SIMULATE{} solo agrupa sentencias,
   sin generar eventos por sí solo; SIMULAR <n> (sección 5.1) es la forma
   oficial que exige el Control y genera contenido sintético automáticamente.

5.3 EXPRESIONES REGULARES (lexer.py)
--------------------------------------------------------------------------------
Documentación exigida por el Control ("defina las ER... que sean necesarias").
Las expresiones regulares reales son las definidas en lexer.py; ninguna otra
existe en el código:

   IDENT      [a-zA-Z_][a-zA-Z0-9_]*
              Identificador de nodo (nombre de fuente/operador/sumidero).
              TODO identificador -- incluidas las palabras clave -- se
              reconoce PRIMERO por esta misma ER (t_IDENT). Después, el
              lexer compara el texto (en minúsculas) contra el diccionario
              `palabras_reservadas` y, si calza, reclasifica el token al
              tipo correspondiente (por ejemplo 'fuente' o 'source' pasan de
              IDENT a SOURCE); si no calza con ninguna palabra reservada,
              el token queda como IDENT.

   NUMBER     \d+
              Entero sin signo (usado en TIEMPO_SERVICIO, REPLICAS/PARALLEL
              y SIMULAR/SIMULATE).

   STRING     \"([^\\\n]|(\\.))*?\"
              Cadena entre comillas dobles, con soporte de caracteres de
              escape (\"); se usa en EMIT (sintaxis legacy).

   ARROW      ->            SEMICOLON  ;
   LBRACKET   \[            RBRACKET   \]
   LBRACE     \{            RBRACE     \}
   EQUALS     =

   Comentarios (no generan token, se descartan):
     línea:   (//|\#).*
     bloque:  /\*(.|\n)*?\*/

   Espacios/tabs/retorno de carro se ignoran (t_ignore = ' \t\r'); los saltos
   de línea (\n+) solo actualizan el contador de línea para los mensajes de
   error.

   Palabras reservadas (reclasificadas desde IDENT vía el diccionario
   palabras_reservadas de lexer.py), vocabulario OFICIAL primero:

     fuente          -> SOURCE            operador        -> OPERATOR
     tiempo_servicio -> TIEMPO_SERVICIO   replicas        -> PARALLEL
     sumidero        -> SINK              conectar        -> CONNECT
     a               -> TO                simular         -> SIMULATE

   Vocabulario LEGACY (sección 5.2), mismos tokens que su contraparte oficial:

     source -> SOURCE   operator -> OPERATOR   sink -> SINK
     parallel -> PARALLEL   connect -> CONNECT   to -> TO
     emit -> EMIT   simulate -> SIMULATE

   La comparación es insensible a mayúsculas/minúsculas (se compara
   t.value.lower() contra el diccionario).

5.4 GRAMÁTICA LIBRE DE CONTEXTO (GLC) OFICIAL (parser.py)
--------------------------------------------------------------------------------
Documentación exigida por el Control ("defina... la GLC que sea necesaria").
Gramática BNF correspondiente EXACTAMENTE a las producciones de parser.py que
implementan la sintaxis oficial de 5.1 (no se mezcla con las producciones
legacy de 5.2, que existen aparte en el mismo archivo bajo los mismos
no-terminales `declaration_stmt` / `connection_stmt` / `simulation_block`):

   programa            -> lista_instrucciones

   lista_instrucciones -> lista_instrucciones instruccion
                        | instruccion
                        | ε

   instruccion         -> declaracion_fuente
                        | declaracion_operador
                        | declaracion_sumidero
                        | conexion
                        | simulacion

   declaracion_fuente  -> FUENTE IDENT ';'

   declaracion_operador -> OPERADOR IDENT TIEMPO_SERVICIO NUMBER ';'
                         | OPERADOR IDENT TIEMPO_SERVICIO NUMBER REPLICAS NUMBER ';'

   declaracion_sumidero -> SUMIDERO IDENT ';'

   conexion            -> CONECTAR IDENT A IDENT ';'

   simulacion          -> SIMULAR NUMBER ';'

   NOTA sobre el ';': el Control NO especifica ningún terminador de
   instrucción en sus ejemplos de sintaxis. Su presencia en esta GLC es una
   DECISIÓN PROPIA del equipo (heredada del diseño original del DSL), no una
   exigencia del enunciado -- ver también 5.1.f.

   Esta GLC corresponde a las funciones p_declaration_source,
   p_declaration_operator_tiempo_servicio,
   p_declaration_operator_tiempo_servicio_parallel, p_declaration_sink,
   p_connection_conectar_a y p_simulation_run de parser.py. La forma
   `declaracion_operador` SIN TIEMPO_SERVICIO no forma parte de esta GLC
   oficial porque el Control la exige siempre (ver 5.1.b); esa forma sin
   tiempo solo existe en la gramática legacy de 5.2.


6. VALIDACIONES SEMÁNTICAS Y ESTRUCTURALES DEL GRAFO
--------------------------------------------------------------------------------
El intérprete no se limita a revisar la sintaxis; antes de simular, valida que
el grafo represente una topología coherente de Stream Processing:

  1. Tabla de Símbolos:
     - No se permiten identificadores duplicados.
     - No se pueden conectar o emitir tuplas a nodos que no hayan sido declarados.
     - El paralelismo de los operadores debe ser un entero estrictamente mayor a 0.
     - Si se especifica TIEMPO_SERVICIO, debe ser un entero estrictamente mayor a 0
       (si no se especifica, el operador queda con tiempo_servicio = None, ver
       sección 5).
     - Con la palabra OFICIAL "OPERADOR", TIEMPO_SERVICIO es obligatorio: su
       ausencia se rechaza como error semántico y el nodo no se registra
       (ver sección 5.1). Esta exigencia no aplica a la palabra legacy
       "OPERATOR" (sección 5.2).

  2. Estructura de la Topología:
     - Debe existir al menos una Fuente (FUENTE/SOURCE) y al menos un Sumidero
       (SUMIDERO/SINK).
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
puede observar claramente este comportamiento: las 6 tuplas (generadas ahora
mediante `SIMULAR 6;` en sintaxis oficial, en vez de 6 EMIT manuales como en
versiones anteriores de este archivo) se dividen en partes iguales (3 y 3)
entre las 2 réplicas de `filtro_ruido`, y luego cada una de esas réplicas
reparte sus tuplas de forma independiente entre las 3 réplicas de
`detector_anomalias`, logrando que cada réplica de este último procese
exactamente 2 tuplas (33.3% cada una), demostrando el balance perfecto. El
mecanismo de Round-Robin en sí (`Simulador.obtener_siguiente_replica`) no
cambió: solo cambió cómo se generan los eventos que lo ejercitan.


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


9. USO DE HERRAMIENTAS DE INTELIGENCIA ARTIFICIAL
--------------------------------------------------------------------------------
El enunciado original del Control I restringía el uso de IA para la generación
de código. Posteriormente, el profesor autorizó explícitamente su uso mediante
comunicación directa al curso (correo).

Se utilizaron herramientas de Inteligencia Artificial durante el desarrollo de
este proyecto conforme a esa autorización posterior del profesor.

Alcance exacto de la autorización y detalle de uso (herramienta, prompts):
[COMPLETAR CON EL ALCANCE EXACTO DE LA AUTORIZACIÓN DEL PROFESOR]
