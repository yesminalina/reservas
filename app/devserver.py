"""
Servidor de desarrollo local usando wsgiref.
Carga las variables de entorno desde .env antes de arrancar la app.

Uso:
    python -m app.devserver
"""
import os
from pathlib import Path
from wsgiref.simple_server import make_server


def _cargar_dotenv():
    """Lee el archivo .env (si existe) y carga las variables en os.environ."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("[devserver] Advertencia: no se encontró .env — usando variables del sistema.")
        return
    with env_path.open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            os.environ.setdefault(clave.strip(), valor.strip())
    print("[devserver] Variables cargadas desde .env")


if __name__ == "__main__":
    _cargar_dotenv()

    from app.wsgi import application

    host, port = "127.0.0.1", 8000
    with make_server(host, port, application) as srv:
        print(f"[devserver] Servidor corriendo en http://{host}:{port}")
        print("[devserver] Ctrl+C para detener.")
        srv.serve_forever()
