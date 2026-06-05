"""
Lógica de negocio e interfaz pública del módulo usuarios.
Otros módulos solo deben llamar funciones de este archivo.
"""
from app.usuarios import repository as repo_real
from app.usuarios.models import Usuario
from app.seguridad import hash_password, verificar_password


class EmailDuplicadoError(Exception):
    """El correo electrónico ya está registrado."""


class CredencialesInvalidasError(Exception):
    """Email o contraseña incorrectos."""


def registrar(
    nombre: str,
    email: str,
    password: str,
    rol: str = "usuario",
    repo=repo_real,
) -> int:
    """
    Registra un nuevo usuario.
    - Valida que el email no esté en uso.
    - Nunca almacena la contraseña en texto plano.
    Devuelve el id del usuario creado.
    """
    if not nombre or not email or not password:
        raise ValueError("Nombre, email y contraseña son obligatorios.")
    if repo.buscar_por_email(email) is not None:
        raise EmailDuplicadoError(f"El email '{email}' ya está registrado.")

    salt, hashed = hash_password(password)
    usuario = Usuario(
        id=None,
        nombre=nombre.strip(),
        email=email.strip().lower(),
        salt=salt,
        password_hash=hashed,
        rol=rol,
    )
    return repo.crear(usuario)


def autenticar(email: str, password: str, repo=repo_real) -> Usuario:
    """
    Verifica las credenciales.
    Devuelve el Usuario si son correctas.
    Lanza CredencialesInvalidasError si el email no existe o la contraseña falla.
    """
    usuario = repo.buscar_por_email(email.strip().lower() if email else "")
    if usuario is None:
        raise CredencialesInvalidasError("Credenciales inválidas.")
    if not verificar_password(password, usuario.salt, usuario.password_hash):
        raise CredencialesInvalidasError("Credenciales inválidas.")
    return usuario
