// ==============================================================================
// ARCHIVO: test.dsl
// TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
// CASO DE PRUEBA: Topología con operadores replicados adyacentes
// SINTAXIS: DSL OFICIAL del Control I (FUENTE/OPERADOR/SUMIDERO/CONECTAR.../
//           SIMULAR), no la sintaxis legacy en inglés (SOURCE/OPERATOR/SINK/
//           EMIT/->). Ver Readme.txt sección 5 para la sintaxis legacy de
//           compatibilidad, que ya no se usa en este archivo de demostración.
// ==============================================================================

// -----------------------------------------------------------------------------
// 1. DECLARACIÓN DE COMPONENTES
// -----------------------------------------------------------------------------

// Fuente de datos (punto de entrada del flujo)
FUENTE sensor_iot;

// Primer operador replicado: Limpieza y filtrado de datos (2 réplicas,
// tarda 4 unidades de tiempo en procesar cada tupla)
OPERADOR filtro_ruido TIEMPO_SERVICIO 4 REPLICAS 2;

// Segundo operador replicado adyacente: Clasificación de anomalías (3 réplicas,
// tarda 6 unidades de tiempo en procesar cada tupla)
// Este operador recibe datos provenientes de las réplicas del operador anterior
OPERADOR detector_anomalias TIEMPO_SERVICIO 6 REPLICAS 3;

// Sumidero final: Base de datos o consola donde se almacenan las tuplas procesadas
SUMIDERO consola_alertas;

// -----------------------------------------------------------------------------
// 2. CONEXIONES DE LA TOPOLOGÍA (DAG)
// Sintaxis oficial del Control: CONECTAR <id_origen> A <id_destino>;
// -----------------------------------------------------------------------------
CONECTAR sensor_iot A filtro_ruido;
CONECTAR filtro_ruido A detector_anomalias;
CONECTAR detector_anomalias A consola_alertas;

// -----------------------------------------------------------------------------
// 3. SIMULACIÓN (Control I: SIMULAR <cantidad_eventos>)
// Genera automáticamente 6 eventos con contenido sintético, para apreciar el
// mismo ciclo de Round-Robin en las 2 réplicas de 'filtro_ruido' y en las 3
// réplicas de 'detector_anomalias'. Cada evento debe acumular exactamente
// 4 + 6 = 10 unidades de tiempo (TIEMPO_SERVICIO de ambos operadores).
// -----------------------------------------------------------------------------
SIMULAR 6;
