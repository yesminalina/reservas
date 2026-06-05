"""
Lógica de negocio e interfaz pública del módulo espacios.
Otros módulos solo deben llamar funciones de este archivo.
Nota: la autorización de rol (admin) se chequea en el handler de presentación,
no aquí, para que este service quede agnóstico de la sesión HTTP.
"""
from app.espacios import repository as repo_real
from app.espacios.models import Espacio


class EspacioNoEncontradoError(Exception):
    """El espacio solicitado no existe."""


def crear_espacio(
    nombre: str,
    descripcion: str,
    capacidad: int,
    repo=repo_real,
) -> int:
    """
    Crea un nuevo espacio.
    Valida que nombre no esté vacío y capacidad sea positiva.
    Devuelve el id del espacio creado.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del espacio es obligatorio.")
    if capacidad < 1:
        raise ValueError("La capacidad debe ser al menos 1.")

    espacio = Espacio(
        id=None,
        nombre=nombre.strip(),
        descripcion=(descripcion or "").strip(),
        capacidad=int(capacidad),
    )
    return repo.crear(espacio)


def listar_espacios(repo=repo_real) -> list[Espacio]:
    """Devuelve la lista de todos los espacios disponibles."""
    return repo.listar()


def obtener_espacio(espacio_id: int, repo=repo_real) -> Espacio:
    """
    Devuelve el espacio con ese id.
    Lanza EspacioNoEncontradoError si no existe.
    """
    espacio = repo.obtener_por_id(espacio_id)
    if espacio is None:
        raise EspacioNoEncontradoError(f"Espacio {espacio_id} no encontrado.")
    return espacio
