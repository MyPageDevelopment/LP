// =======================================================
// TEST: Error Léxico
// Descripción: Contiene caracteres inválidos ($ y @) que el
// lexer no reconoce en el alfabeto del lenguaje.
// =======================================================

FUENTE sensor_$1;

OPERADOR filtro@ TIEMPO_SERVICIO 4 REPLICAS 2;

SUMIDERO consola;

CONECTAR sensor_$1 A filtro@;
CONECTAR filtro@ A consola;

SIMULAR 2;
