"""
Acceso a datos del módulo usuarios.
Solo SQL parametrizado; nunca lógica de negocio aquí.
"""
from app.db import obtener_conexion
from app.usuarios.models import Usuario


def crear(usuario: Usuario) -> int:
    """Inserta un nuevo usuario y devuelve su id."""
    sql = """
        INSERT INTO usuarios (nombre, email, salt, password_hash, rol)
        VALUES (%s, %s, %s, %s, %s)
    """
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (
            usuario.nombre,
            usuario.email,
            usuario.salt,
            usuario.password_hash,
            usuario.rol,
        ))
        conn.commit()
        return cur.lastrowid


def buscar_por_email(email: str) -> Usuario | None:
    """Devuelve el Usuario con ese email, o None si no existe."""
    sql = "SELECT id, nombre, email, salt, password_hash, rol FROM usuarios WHERE email = %s"
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (email,))
        fila = cur.fetchone()
    if fila is None:
        return None
    return Usuario(
        id=fila["id"],
        nombre=fila["nombre"],
        email=fila["email"],
        salt=fila["salt"],
        password_hash=fila["password_hash"],
        rol=fila["rol"],
    )
