"""
Configuración de la aplicación leída desde variables de entorno.
Nunca escribas credenciales reales en este archivo.
"""
import os


DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = os.environ.get("DB_NAME", "reservas")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-inseguro-cambia-en-produccion")
