#!/opt/alt/python311/bin/python3
"""
Script de sondeo temporal — verifica Python, PyMySQL y otros interpretes.
BORRAR este archivo una vez terminado el diagnostico.
"""
import cgitb
cgitb.enable()  # muestra tracebacks en el navegador en vez de un 500 generico

import sys
import os
import glob

print("Content-Type: text/plain; charset=utf-8")
print()
print("python  :", sys.version)
print("exe     :", sys.executable)
print()
print("sys.path:")
for p in sys.path:
    print("  ", p)
print()

HERE = os.path.dirname(os.path.abspath(__file__))
vendor = os.path.join(HERE, "vendor")
if vendor not in sys.path:
    sys.path.insert(0, vendor)

try:
    import pymysql
    print("pymysql :", pymysql.__version__, "— OK")
except Exception as e:
    print("pymysql : ERROR —", repr(e))

# --- Interpretes Python alternativos (la version va en el nombre de la ruta) -
print()
print("=== Otros Python en el servidor (alt-python de CloudLinux) ===")
candidatos = sorted(set(
    glob.glob("/opt/alt/python*/bin/python3")
    + glob.glob("/usr/local/bin/python3.*")
    + glob.glob("/usr/bin/python3.*")
))
if not candidatos:
    print("  (no se encontraron en /opt/alt ni /usr/local)")
for ruta in candidatos:
    print("  ", ruta)
