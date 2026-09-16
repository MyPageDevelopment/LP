# ==============================================================================
# ARCHIVO: Makefile
# TAREA SEMESTRAL: Intérprete de Topologías de Stream Processing
# ASIGNATURA: Lenguajes y Autómatas / Compiladores
# ==============================================================================

PYTHON = python
PIP = pip

.PHONY: all run clean install test help

all: run

# Instala las dependencias del proyecto (PLY)
install:
	$(PIP) install ply

# Ejecuta el intérprete con el archivo de prueba test.dsl
run:
	$(PYTHON) main.py test.dsl

# Ejecuta la prueba estándar
test: run

# Limpia los archivos temporales generados por Python y PLY
clean:
	python -c "import os, glob, shutil; [shutil.rmtree(p) for p in glob.glob('**/__pycache__', recursive=True) if os.path.exists(p)]; [os.remove(f) for f in glob.glob('*.pyc') + glob.glob('parsetab.py') + glob.glob('lextab.py') + glob.glob('parser.out') if os.path.exists(f)]"
	@echo "Archivos temporales y cache eliminados con exito."

# Muestra la ayuda de comandos disponibles
help:
	@echo "Comandos disponibles en este Makefile:"
	@echo "  make install  - Instala la libreria PLY via pip"
	@echo "  make run      - Ejecuta el interprete con el caso de prueba test.dsl"
	@echo "  make test     - Alias de 'run'"
	@echo "  make clean    - Elimina cache de Python (__pycache__) y tablas generadas por PLY"
