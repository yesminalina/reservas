"""
Pruebas unitarias del módulo reservas.
Usan FakeRepo en memoria: sin conexión a MySQL.
También se mockea espacios.service para no necesitar BD.
"""
import pytest
from unittest.mock import patch
from app.reservas import service
from app.reservas.service import EspacioOcupadoError, ReservaNoAutorizadaError
from app.reservas.models import Reserva
from app.espacios.models import Espacio


# ---------------------------------------------------------------------------
# Repositorio falso (fake) en memoria
# ---------------------------------------------------------------------------

class FakeRepo:
    """Simula el repository de reservas sin base de datos."""

    def __init__(self, ocupado: bool = False):
        self._ocupado = ocupado
        self._reservas: list[Reserva] = []
        self._next_id = 1

    def crear(self, reserva: Reserva) -> int:
        reserva.id = self._next_id
        self._next_id += 1
        self._reservas.append(reserva)
        return reserva.id

    def hay_solapamiento(self, espacio_id: int, inicio: str, fin: str) -> bool:
        return self._ocupado

    def listar_por_usuario(self, usuario_id: int) -> list[Reserva]:
        return [r for r in self._reservas if r.usuario_id == usuario_id]

    def cancelar(self, reserva_id: int, usuario_id: int) -> bool:
        for r in self._reservas:
            if r.id == reserva_id and r.usuario_id == usuario_id and r.estado == "activa":
                r.estado = "cancelada"
                return True
        return False

    def obtener_por_id(self, reserva_id: int) -> Reserva | None:
        for r in self._reservas:
            if r.id == reserva_id:
                return r
        return None


# Espacio ficticio para devolver cuando se valida existencia
_ESPACIO_FAKE = Espacio(id=10, nombre="Sala Test", descripcion="", capacidad=5)


# ---------------------------------------------------------------------------
# Tests de creación
# ---------------------------------------------------------------------------

def test_crear_reserva_espacio_libre():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        rid = service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
    assert rid == 1
    assert len(repo._reservas) == 1


def test_crear_reserva_guarda_estado_activa():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
    assert repo._reservas[0].estado == "activa"


def test_crear_reserva_espacio_ocupado_lanza_error():
    repo = FakeRepo(ocupado=True)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        with pytest.raises(EspacioOcupadoError):
            service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)


def test_crear_reserva_inicio_igual_fin_lanza_error():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        with pytest.raises(ValueError):
            service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 09:00", repo=repo)


def test_crear_reserva_fin_antes_de_inicio_lanza_error():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        with pytest.raises(ValueError):
            service.crear_reserva(1, 10, "2026-01-01 10:00", "2026-01-01 09:00", repo=repo)


# ---------------------------------------------------------------------------
# Tests de listado
# ---------------------------------------------------------------------------

def test_listar_de_usuario_sin_reservas():
    repo = FakeRepo()
    resultado = service.listar_de_usuario(99, repo=repo)
    assert resultado == []


def test_listar_de_usuario_filtra_por_usuario():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
        service.crear_reserva(2, 10, "2026-01-02 09:00", "2026-01-02 10:00", repo=repo)
    assert len(service.listar_de_usuario(1, repo=repo)) == 1
    assert len(service.listar_de_usuario(2, repo=repo)) == 1


# ---------------------------------------------------------------------------
# Tests de cancelación
# ---------------------------------------------------------------------------

def test_cancelar_reserva_cambia_estado():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        rid = service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
    service.cancelar_reserva(rid, 1, repo=repo)
    assert repo._reservas[0].estado == "cancelada"


def test_cancelar_reserva_de_otro_usuario_lanza_error():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        rid = service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
    with pytest.raises(ReservaNoAutorizadaError):
        service.cancelar_reserva(rid, 99, repo=repo)  # usuario 99 no es el dueño


def test_cancelar_reserva_ya_cancelada_lanza_error():
    repo = FakeRepo(ocupado=False)
    with patch("app.reservas.service.espacios_service.obtener_espacio", return_value=_ESPACIO_FAKE):
        rid = service.crear_reserva(1, 10, "2026-01-01 09:00", "2026-01-01 10:00", repo=repo)
    service.cancelar_reserva(rid, 1, repo=repo)
    with pytest.raises(ReservaNoAutorizadaError):
        service.cancelar_reserva(rid, 1, repo=repo)  # ya estaba cancelada


def test_cancelar_reserva_inexistente_lanza_error():
    repo = FakeRepo()
    with pytest.raises(ReservaNoAutorizadaError):
        service.cancelar_reserva(999, 1, repo=repo)
