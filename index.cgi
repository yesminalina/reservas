#!/opt/alt/python311/bin/python3
"""
Punto de entrada CGI para cPanel sin Passenger ni Setup Python App.
Ejecuta la misma app WSGI (app/wsgi.py:application) a través de
wsgiref.handlers.CGIHandler, que viene incluida en la librería estándar.

ANTES DE SUBIR AL SERVIDOR:
  1. Ajustar el shebang si info.cgi reporta una ruta diferente de Python.
  2. Dar chmod 755 a este archivo (clic derecho -> Permisos en File Manager).
  3. Crear .env en la misma carpeta con las variables de entorno reales
     (NO la subas al repo; está en .gitignore).
"""
import sys
import os
from pathlib import Path

# --- sys.path ----------------------------------------------------------------
# 1. Raíz del proyecto (para que "from app.wsgi import application" funcione).
# 2. vendor/ con pymysql copiado (no hay pip en el hosting).
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "vendor"))

# --- Variables de entorno ----------------------------------------------------
# app/config.py lee os.environ al importarse, por lo que hay que cargar .env
# ANTES de "from app.wsgi import application".
# Mismo algoritmo que app/devserver.py:_cargar_dotenv().
def _cargar_dotenv():
    env_path = Path(HERE) / ".env"
    if not env_path.exists():
        return
    for linea in env_path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip())

_cargar_dotenv()

# --- WSGI via CGI ------------------------------------------------------------
from wsgiref.handlers import CGIHandler
from app.wsgi import application

CGIHandler().run(application)
