// =======================================================
// TEST: Error Semántico (Nodo Inexistente / No Declarado)
// Descripción: Se intenta conectar hacia 'nodo_fantasma',
// el cual nunca fue declarado en la tabla de símbolos.
// =======================================================

FUENTE sensor_iot;
OPERADOR filtro TIEMPO_SERVICIO 3;
SUMIDERO consola;

CONECTAR sensor_iot A filtro;
CONECTAR filtro A nodo_fantasma;
CONECTAR nodo_fantasma A consola;

SIMULAR 2;
