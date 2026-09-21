// =======================================================
// TEST: Error Estructural del Grafo (Detección de Ciclo)
// Descripción: Se crea un ciclo cerrado entre op_a y op_b:
// op_a -> op_b -> op_a. La topología deja de ser un DAG.
// =======================================================

FUENTE sensor;
OPERADOR op_a TIEMPO_SERVICIO 3;
OPERADOR op_b TIEMPO_SERVICIO 4;
SUMIDERO consola;

CONECTAR sensor A op_a;
CONECTAR op_a A op_b;
CONECTAR op_b A op_a;
CONECTAR op_b A consola;

SIMULAR 2;
