// =======================================================
// TEST: Error Estructural (Nodo Aislado / Desconectado)
// Descripción: El operador 'filtro_huerfano' fue declarado pero
// nunca se conectó en la topología, quedando como componente aislado.
// =======================================================

FUENTE sensor;
OPERADOR filtro_util TIEMPO_SERVICIO 3;
OPERADOR filtro_huerfano TIEMPO_SERVICIO 5;
SUMIDERO consola;

CONECTAR sensor A filtro_util;
CONECTAR filtro_util A consola;

SIMULAR 2;
