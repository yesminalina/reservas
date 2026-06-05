"""
Acceso a datos del módulo espacios.
Solo SQL parametrizado; nunca lógica de negocio aquí.
"""
from app.db import obtener_conexion
from app.espacios.models import Espacio


def _fila_a_espacio(fila: dict) -> Espacio:
    return Espacio(
        id=fila["id"],
        nombre=fila["nombre"],
        descripcion=fila["descripcion"] or "",
        capacidad=fila["capacidad"],
    )


def crear(espacio: Espacio) -> int:
    """Inserta un espacio nuevo y devuelve su id."""
    sql = "INSERT INTO espacios (nombre, descripcion, capacidad) VALUES (%s, %s, %s)"
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (espacio.nombre, espacio.descripcion, espacio.capacidad))
        conn.commit()
        return cur.lastrowid


def listar() -> list[Espacio]:
    """Devuelve todos los espacios ordenados por nombre."""
    sql = "SELECT id, nombre, descripcion, capacidad FROM espacios ORDER BY nombre"
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql)
        filas = cur.fetchall()
    return [_fila_a_espacio(f) for f in filas]


def obtener_por_id(espacio_id: int) -> Espacio | None:
    """Devuelve el Espacio con ese id, o None si no existe."""
    sql = "SELECT id, nombre, descripcion, capacidad FROM espacios WHERE id = %s"
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (espacio_id,))
        fila = cur.fetchone()
    return _fila_a_espacio(fila) if fila else None
