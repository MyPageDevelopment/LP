// =======================================================
// TEST: Error Sintáctico / Semántico
// Descripción: El operador intenta declararse sin la cláusula
// obligatoria TIEMPO_SERVICIO (exigida por el Control I).
// =======================================================

FUENTE sensor_iot;

OPERADOR filtro_invalido REPLICAS 2;

SUMIDERO consola;

CONECTAR sensor_iot A filtro_invalido;
CONECTAR filtro_invalido A consola;

SIMULAR 2;
