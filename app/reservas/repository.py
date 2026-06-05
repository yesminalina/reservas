"""
Acceso a datos del módulo reservas.
Solo SQL parametrizado; nunca lógica de negocio aquí.
El índice idx_reservas_solapamiento en (espacio_id, estado, inicio, fin)
optimiza la consulta hay_solapamiento.
"""
from app.db import obtener_conexion
from app.reservas.models import Reserva


def _fila_a_reserva(fila: dict) -> Reserva:
    return Reserva(
        id=fila["id"],
        usuario_id=fila["usuario_id"],
        espacio_id=fila["espacio_id"],
        inicio=str(fila["inicio"]),
        fin=str(fila["fin"]),
        estado=fila["estado"],
    )


def crear(reserva: Reserva) -> int:
    """Inserta una reserva nueva y devuelve su id."""
    sql = """
        INSERT INTO reservas (usuario_id, espacio_id, inicio, fin, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (
            reserva.usuario_id,
            reserva.espacio_id,
            reserva.inicio,
            reserva.fin,
            reserva.estado,
        ))
        conn.commit()
        return cur.lastrowid


def hay_solapamiento(espacio_id: int, inicio: str, fin: str) -> bool:
    """
    Verifica si existe alguna reserva activa que se solape con el rango dado.
    Solapamiento: inicio_existente < fin_nuevo AND fin_existente > inicio_nuevo
    """
    sql = """
        SELECT 1 FROM reservas
        WHERE espacio_id = %s
          AND estado = 'activa'
          AND inicio < %s
          AND fin   > %s
        LIMIT 1
    """
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (espacio_id, fin, inicio))
        return cur.fetchone() is not None


def listar_por_usuario(usuario_id: int) -> list[Reserva]:
    """Devuelve las reservas de un usuario ordenadas por inicio descendente."""
    sql = """
        SELECT id, usuario_id, espacio_id, inicio, fin, estado
        FROM reservas
        WHERE usuario_id = %s
        ORDER BY inicio DESC
    """
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (usuario_id,))
        filas = cur.fetchall()
    return [_fila_a_reserva(f) for f in filas]


def cancelar(reserva_id: int, usuario_id: int) -> bool:
    """
    Cambia el estado a 'cancelada'.
    Filtra también por usuario_id para que solo el dueño pueda cancelar.
    Devuelve True si se actualizó al menos una fila.
    """
    sql = """
        UPDATE reservas
        SET estado = 'cancelada'
        WHERE id = %s AND usuario_id = %s AND estado = 'activa'
    """
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (reserva_id, usuario_id))
        conn.commit()
        return cur.rowcount > 0


def obtener_por_id(reserva_id: int) -> Reserva | None:
    """Devuelve la reserva con ese id, o None si no existe."""
    sql = "SELECT id, usuario_id, espacio_id, inicio, fin, estado FROM reservas WHERE id = %s"
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (reserva_id,))
        fila = cur.fetchone()
    return _fila_a_reserva(fila) if fila else None
