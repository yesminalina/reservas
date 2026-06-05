"""
Acceso a la base de datos MySQL mediante PyMySQL.
Una sola función de conexión, parametrizada por variables de entorno.
Nunca credenciales en el código.
"""
import pymysql
import pymysql.cursors

from app import config


def obtener_conexion():
    """Devuelve una conexión PyMySQL con DictCursor y autocommit desactivado."""
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )
