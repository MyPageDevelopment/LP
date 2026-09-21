// =======================================================
// TEST: Error Semántico (Tiempo de Servicio Inválido)
// Descripción: Se intenta declarar un operador con
// TIEMPO_SERVICIO 0, lo cual viola la restricción de ser > 0.
// =======================================================

FUENTE sensor;
OPERADOR filtro TIEMPO_SERVICIO 0 REPLICAS 2;
SUMIDERO consola;

CONECTAR sensor A filtro;
CONECTAR filtro A consola;

SIMULAR 2;
