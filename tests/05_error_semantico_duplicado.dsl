// =======================================================
// TEST: Error Semántico (Identificador Duplicado)
// Descripción: Se declara 'sensor' primero como FUENTE y luego
// se intenta redeclarar el mismo identificador como OPERADOR.
// =======================================================

FUENTE sensor;
OPERADOR sensor TIEMPO_SERVICIO 5;

SUMIDERO consola;

CONECTAR sensor A consola;

SIMULAR 2;
