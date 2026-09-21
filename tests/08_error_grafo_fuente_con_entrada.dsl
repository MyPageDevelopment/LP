// =======================================================
// TEST: Error Estructural (Fuente con Conexión de Entrada)
// Descripción: Las fuentes representan el origen de datos y
// tienen in-degree = 0. Aquí op_a intenta conectarse a la fuente.
// =======================================================

FUENTE sensor;
OPERADOR op_a TIEMPO_SERVICIO 3;
SUMIDERO consola;

CONECTAR sensor A op_a;
CONECTAR op_a A sensor;
CONECTAR op_a A consola;

SIMULAR 2;
