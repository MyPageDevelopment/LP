// =======================================================
// TEST: Caso Válido con Bifurcación (Branching)
// Descripción: 1 Fuente que se divide hacia 2 operadores
// distintos, y ambos convergen en el mismo Sumidero.
// =======================================================

FUENTE sensor_temperatura;

OPERADOR filtro_rapido TIEMPO_SERVICIO 2 REPLICAS 2;
OPERADOR filtro_lento TIEMPO_SERVICIO 5 REPLICAS 2;

SUMIDERO base_datos;

CONECTAR sensor_temperatura A filtro_rapido;
CONECTAR sensor_temperatura A filtro_lento;

CONECTAR filtro_rapido A base_datos;
CONECTAR filtro_lento A base_datos;

SIMULAR 4;
