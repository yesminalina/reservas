"""
Pruebas unitarias del módulo usuarios.
Usan un FakeRepo en memoria: sin conexión a MySQL.
"""
import pytest
from app.usuarios import service
from app.usuarios.service import EmailDuplicadoError, CredencialesInvalidasError
from app.usuarios.models import Usuario
from app.seguridad import hash_password


# ---------------------------------------------------------------------------
# Repositorio falso (fake) en memoria
# ---------------------------------------------------------------------------

class FakeRepo:
    """Simula el repository de usuarios sin base de datos."""

    def __init__(self):
        self._usuarios: list[Usuario] = []
        self._next_id = 1

    def crear(self, usuario: Usuario) -> int:
        usuario.id = self._next_id
        self._next_id += 1
        self._usuarios.append(usuario)
        return usuario.id

    def buscar_por_email(self, email: str) -> Usuario | None:
        for u in self._usuarios:
            if u.email == email:
                return u
        return None


# ---------------------------------------------------------------------------
# Tests de registro
# ---------------------------------------------------------------------------

def test_registro_crea_usuario():
    repo = FakeRepo()
    uid = service.registrar("Ana", "ana@test.cl", "pass1234", repo=repo)
    assert uid == 1
    assert len(repo._usuarios) == 1


def test_registro_asigna_rol_por_defecto():
    repo = FakeRepo()
    service.registrar("Ana", "ana@test.cl", "pass1234", repo=repo)
    assert repo._usuarios[0].rol == "usuario"


def test_registro_puede_asignar_rol_admin():
    repo = FakeRepo()
    service.registrar("Admin", "admin@test.cl", "pass1234", rol="admin", repo=repo)
    assert repo._usuarios[0].rol == "admin"


def test_registro_no_guarda_password_en_texto_plano():
    repo = FakeRepo()
    service.registrar("Ana", "ana@test.cl", "mipassword", repo=repo)
    u = repo._usuarios[0]
    # El hash no debe contener la contraseña en texto plano
    assert "mipassword" not in u.password_hash
    assert "mipassword" not in u.salt
    # El hash debe ser una cadena hexadecimal larga (SHA-256 = 64 chars)
    assert len(u.password_hash) == 64
    assert len(u.salt) == 32


def test_registro_rechaza_email_duplicado():
    repo = FakeRepo()
    service.registrar("Ana", "ana@test.cl", "pass1234", repo=repo)
    with pytest.raises(EmailDuplicadoError):
        service.registrar("Ana2", "ana@test.cl", "pass5678", repo=repo)


def test_registro_rechaza_campos_vacios():
    repo = FakeRepo()
    with pytest.raises(ValueError):
        service.registrar("", "ana@test.cl", "pass1234", repo=repo)
    with pytest.raises(ValueError):
        service.registrar("Ana", "", "pass1234", repo=repo)
    with pytest.raises(ValueError):
        service.registrar("Ana", "ana@test.cl", "", repo=repo)


def test_registro_normaliza_email_a_minusculas():
    repo = FakeRepo()
    service.registrar("Ana", "ANA@TEST.CL", "pass1234", repo=repo)
    assert repo._usuarios[0].email == "ana@test.cl"


# ---------------------------------------------------------------------------
# Tests de autenticación
# ---------------------------------------------------------------------------

def _repo_con_usuario(email: str, password: str, rol: str = "usuario") -> FakeRepo:
    """Crea un FakeRepo con un usuario ya registrado."""
    repo = FakeRepo()
    service.registrar("Usuario", email, password, rol=rol, repo=repo)
    return repo


def test_autenticar_con_credenciales_correctas():
    repo = _repo_con_usuario("juan@test.cl", "mipassword")
    usuario = service.autenticar("juan@test.cl", "mipassword", repo=repo)
    assert usuario.email == "juan@test.cl"


def test_autenticar_devuelve_objeto_usuario():
    repo = _repo_con_usuario("juan@test.cl", "mipassword")
    usuario = service.autenticar("juan@test.cl", "mipassword", repo=repo)
    assert isinstance(usuario, Usuario)


def test_autenticar_falla_con_password_incorrecta():
    repo = _repo_con_usuario("juan@test.cl", "mipassword")
    with pytest.raises(CredencialesInvalidasError):
        service.autenticar("juan@test.cl", "passwordmala", repo=repo)


def test_autenticar_falla_con_email_inexistente():
    repo = FakeRepo()
    with pytest.raises(CredencialesInvalidasError):
        service.autenticar("noexiste@test.cl", "cualquiera", repo=repo)


def test_autenticar_es_case_insensitive_en_email():
    repo = _repo_con_usuario("juan@test.cl", "mipassword")
    usuario = service.autenticar("JUAN@TEST.CL", "mipassword", repo=repo)
    assert usuario.email == "juan@test.cl"
