// =======================================================
// TEST: Error Sintáctico (Estructura Invertida o Inválida)
// Descripción: La sentencia de conexión está invertida:
// 'A filtro CONECTAR sensor;' violando la gramática formal.
// =======================================================

FUENTE sensor_iot;
OPERADOR filtro TIEMPO_SERVICIO 4 REPLICAS 2;
SUMIDERO consola;

A filtro CONECTAR sensor_iot;

SIMULAR 2;
