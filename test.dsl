// ==============================================================================
// ARCHIVO: test.dsl
// TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
// CASO DE PRUEBA: Topología con operadores replicados adyacentes
// ==============================================================================

// 1. Declaración de Componentes
// Fuente de entrada de datos
FUENTE sensor_iot;

// Primer operador replicado: 2 réplicas y 4 unidades de tiempo de servicio
OPERADOR filtro_ruido TIEMPO_SERVICIO 4 REPLICAS 2;

// Segundo operador replicado adyacente: 3 réplicas y 6 unidades de tiempo de servicio
OPERADOR detector_anomalias TIEMPO_SERVICIO 6 REPLICAS 3;

// Sumidero donde se reciben las tuplas finales
SUMIDERO consola_alertas;

// 2. Conexiones de la Topología (DAG)
CONECTAR sensor_iot A filtro_ruido;
CONECTAR filtro_ruido A detector_anomalias;
CONECTAR detector_anomalias A consola_alertas;

// 3. Simulación de Eventos
// Genera 6 eventos para observar el balanceo Round-Robin en las réplicas
SIMULAR 6;
