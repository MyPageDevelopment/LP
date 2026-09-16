// ==============================================================================
// ARCHIVO: test.dsl
// TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
// CASO DE PRUEBA: Topología con operadores replicados adyacentes
// ==============================================================================

// -----------------------------------------------------------------------------
// 1. DECLARACIÓN DE COMPONENTES
// -----------------------------------------------------------------------------

// Fuente de datos (punto de entrada del flujo)
SOURCE sensor_iot;

// Primer operador replicado: Limpieza y filtrado de datos (2 réplicas)
OPERATOR filtro_ruido PARALLEL 2;

// Segundo operador replicado adyacente: Clasificación de anomalías (3 réplicas)
// Este operador recibe datos provenientes de las réplicas del operador anterior
OPERATOR detector_anomalias PARALLEL 3;

// Sumidero final: Base de datos o consola donde se almacenan las tuplas procesadas
SINK consola_alertas;

// -----------------------------------------------------------------------------
// 2. CONEXIONES DE LA TOPOLOGÍA (DAG)
// Permite sintaxis encadenada usando el operador '->'
// sensor_iot -> filtro_ruido -> detector_anomalias -> consola_alertas;
// -----------------------------------------------------------------------------
sensor_iot -> filtro_ruido;
filtro_ruido -> detector_anomalias;
detector_anomalias -> consola_alertas;

// -----------------------------------------------------------------------------
// 3. EVENTOS A SIMULAR (Inyección de tuplas al flujo)
// Emitimos 6 eventos para apreciar el ciclo de Round-Robin en las 2 réplicas
// de 'filtro_ruido' y en las 3 réplicas de 'detector_anomalias'.
// -----------------------------------------------------------------------------
EMIT "LECTURA #1: temp=21.4C, hum=45%" TO sensor_iot;
EMIT "LECTURA #2: temp=48.9C, hum=80%" TO sensor_iot;
EMIT "LECTURA #3: temp=22.1C, hum=43%" TO sensor_iot;
EMIT "LECTURA #4: temp=92.3C, hum=15%" TO sensor_iot;
EMIT "LECTURA #5: temp=23.0C, hum=50%" TO sensor_iot;
EMIT "LECTURA #6: temp=88.7C, hum=78%" TO sensor_iot;
