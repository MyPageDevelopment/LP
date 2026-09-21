================================================================================
  TAREA SEMESTRAL: INTÉRPRETE DE TOPOLOGÍAS DE STREAM PROCESSING
  Asignatura : Lenguajes y Autómatas / Compiladores
  Grupo      : Grupo [COMPLETAR NUMERO]
  Integrantes: [COMPLETAR NOMBRES DE INTEGRANTES]
================================================================================

1. DESCRIPCIÓN GENERAL
--------------------------------------------------------------------------------
Este proyecto implementa un compilador e intérprete para un Lenguaje de Dominio
Específico (DSL) que permite modelar, validar y simular topologías de
procesamiento de flujos de datos en tiempo real (Stream Processing).

El sistema valida que la topología constituya un Grafo Dirigido Acíclico (DAG)
válido y simula el paso de tuplas/eventos a través de réplicas en paralelo
usando una política de balanceo de carga Round-Robin.


2. ESTRUCTURA DE ARCHIVOS
--------------------------------------------------------------------------------
  * lexer.py    : Analizador léxico (PLY Lex). Reconoce los tokens del lenguaje,
                  números de línea y omite comentarios y espacios en blanco.
  * parser.py   : Analizador sintáctico (PLY Yacc). Implementa la gramática formal
                  en formato BNF (LALR(1)) y construye la topología.
  * topology.py : Lógica del dominio: representación de nodos, validaciones
                  semánticas y estructurales del DAG (detección de ciclos por DFS,
                  alcanzabilidad) y motor de simulación Round-Robin.
  * main.py     : Punto de entrada (CLI). Coordina la lectura del archivo .dsl,
                  la compilación, la validación y el despliegue del reporte.
  * test.dsl    : Archivo de prueba con una topología de operadores replicados.
  * Makefile    : Automatizador de instalación, ejecución y limpieza.
  * Readme.txt  : Instrucciones y documentación del proyecto.


3. REQUISITOS E INSTALACIÓN
--------------------------------------------------------------------------------
El proyecto requiere Python 3.8 o superior y la biblioteca PLY (Python Lex-Yacc).

Instalación automática mediante Make:
    make install

Instalación manual con pip:
    pip install ply


4. MODO DE USO Y EJECUCIÓN
--------------------------------------------------------------------------------
Para ejecutar el caso de prueba incluido (test.dsl):

    Opción 1 (Usando Make):
        make run

    Opción 2 (Python directo):
        python main.py test.dsl

Para limpiar los archivos temporales y caché:
    make clean


5. SINTAXIS DEL DSL
--------------------------------------------------------------------------------
El lenguaje soporta las siguientes instrucciones:

  - Declarar Fuente:
      FUENTE <nombre_fuente>;

  - Declarar Operador (TIEMPO_SERVICIO obligatorio, REPLICAS opcional):
      OPERADOR <nombre> TIEMPO_SERVICIO <tiempo>;
      OPERADOR <nombre> TIEMPO_SERVICIO <tiempo> REPLICAS <cantidad>;

  - Declarar Sumidero:
      SUMIDERO <nombre_sumidero>;

  - Conectar Nodos:
      CONECTAR <origen> A <destino>;

  - Iniciar Simulación:
      SIMULAR <cantidad_eventos>;


6. VALIDACIONES SEMÁNTICAS Y ESTRUCTURALES DEL GRAFO
--------------------------------------------------------------------------------
Antes de simular, el intérprete valida:
  1. Identificadores únicos en la tabla de símbolos y referencias válidas.
  2. Que TIEMPO_SERVICIO y REPLICAS sean enteros estrictamente mayores a 0.
  3. Que exista al menos una FUENTE y al menos un SUMIDERO.
  4. Que las FUENTES no tengan entradas y los SUMIDEROS no tengan salidas.
  5. Que no existan ciclos en la topología (verificado mediante DFS con estados
     blanco-gris-negro).
  6. Que no existan nodos aislados: todos deben ser alcanzables desde una fuente
     y tener camino hacia un sumidero.


7. SIMULACIÓN Y BALANCEO ROUND-ROBIN
--------------------------------------------------------------------------------
La simulación inyecta los eventos solicitados y los propaga por los canales:
  - Cada operador distribuye las tuplas entre sus réplicas de forma alternada.
  - Cada evento registra el camino recorrido y el tiempo de servicio acumulado.

Justificación de diseño para operadores replicados adyacentes:
El enunciado indica que la situación donde dos operadores adyacentes se
encuentran replicados simultáneamente (ej. 2 réplicas conectadas a 3 réplicas)
no está completamente especificada y debe ser resuelta y justificada por los
estudiantes en el Readme:
  - Decisión tomada: Se implementó un Round-Robin independiente por canal emisor,
    identificado por la tupla (nodo_emisor, replica_emisor, nodo_destino).
  - Justificación: En sistemas distribuidos reales (como Apache Storm o Apache Flink),
    cada réplica emisora toma decisiones de balanceo de forma local. Mantener un
    puntero independiente por cada réplica emisora evita un estado global compartido
    (que crearía un cuello de botella o condiciones de carrera), logrando una
    distribución equilibrada y uniforme de la carga a lo largo del flujo.


8. USO DE HERRAMIENTAS DE INTELIGENCIA ARTIFICIAL
--------------------------------------------------------------------------------
En conformidad con la autorización explícita emitida por el profesor al curso
vía correo electrónico, se emplearon herramientas de Inteligencia Artificial
como apoyo para la consulta de documentación, diseño de pruebas y refactorización
del código.
