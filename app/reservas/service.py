"""
Lógica de negocio e interfaz pública del módulo reservas.
Otros módulos solo deben llamar funciones de este archivo.

Regla de acoplamiento entre módulos:
  Para validar que un espacio existe, se llama a espacios.service (no a su repository).
  Este es el único punto de cruce entre módulos de dominio.
"""
from app.reservas import repository as repo_real
from app.reservas.models import Reserva
from app.espacios import service as espacios_service


class EspacioOcupadoError(Exception):
    """El espacio ya tiene una reserva activa en ese horario."""


class ReservaNoAutorizadaError(Exception):
    """El usuario no tiene permiso para operar esta reserva."""


class ReservaNoEncontradaError(Exception):
    """La reserva solicitada no existe o ya fue cancelada."""


def crear_reserva(
    usuario_id: int,
    espacio_id: int,
    inicio: str,
    fin: str,
    repo=repo_real,
) -> int:
    """
    Crea una reserva para el usuario en el espacio indicado.
    Reglas de negocio:
      1. El espacio debe existir (delega en espacios.service).
      2. No se permiten reservas solapadas en el mismo espacio.
      3. La fecha de inicio debe ser anterior a la de fin.
    Devuelve el id de la reserva creada.
    """
    if inicio >= fin:
        raise ValueError("La fecha/hora de inicio debe ser anterior a la de fin.")

    # Cruce de módulos: validamos existencia del espacio vía su service (interfaz pública).
    espacios_service.obtener_espacio(espacio_id)

    if repo.hay_solapamiento(espacio_id, inicio, fin):
        raise EspacioOcupadoError("El espacio ya está reservado en ese horario.")

    reserva = Reserva(
        id=None,
        usuario_id=usuario_id,
        espacio_id=espacio_id,
        inicio=inicio,
        fin=fin,
        estado="activa",
    )
    return repo.crear(reserva)


def listar_de_usuario(usuario_id: int, repo=repo_real) -> list[Reserva]:
    """Devuelve las reservas del usuario ordenadas por inicio descendente."""
    return repo.listar_por_usuario(usuario_id)


def cancelar_reserva(reserva_id: int, usuario_id: int, repo=repo_real) -> None:
    """
    Cancela una reserva.
    Solo el dueño puede cancelarla (el repository filtra por usuario_id).
    Lanza ReservaNoAutorizadaError si la reserva no pertenece al usuario
    o no existe o ya estaba cancelada.
    """
    cancelado = repo.cancelar(reserva_id, usuario_id)
    if not cancelado:
        raise ReservaNoAutorizadaError(
            "No se pudo cancelar la reserva: no existe, ya fue cancelada "
            "o no tienes permiso."
        )
