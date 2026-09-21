// =======================================================
// TEST: Error Estructural (Sumidero con Conexión Saliente)
// Descripción: Los sumideros representan puntos finales y
// tienen out-degree = 0. Aquí consola intenta enviar datos a op.
// =======================================================

FUENTE sensor;
OPERADOR op TIEMPO_SERVICIO 3;
SUMIDERO consola;

CONECTAR sensor A op;
CONECTAR op A consola;
CONECTAR consola A op;

SIMULAR 2;
