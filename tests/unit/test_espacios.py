"""
Pruebas unitarias del módulo espacios.
Usan un FakeRepo en memoria: sin conexión a MySQL.
"""
import pytest
from app.espacios import service
from app.espacios.service import EspacioNoEncontradoError
from app.espacios.models import Espacio


# ---------------------------------------------------------------------------
# Repositorio falso (fake) en memoria
# ---------------------------------------------------------------------------

class FakeRepo:
    """Simula el repository de espacios sin base de datos."""

    def __init__(self):
        self._espacios: list[Espacio] = []
        self._next_id = 1

    def crear(self, espacio: Espacio) -> int:
        espacio.id = self._next_id
        self._next_id += 1
        self._espacios.append(espacio)
        return espacio.id

    def listar(self) -> list[Espacio]:
        return list(self._espacios)

    def obtener_por_id(self, espacio_id: int) -> Espacio | None:
        for e in self._espacios:
            if e.id == espacio_id:
                return e
        return None


# ---------------------------------------------------------------------------
# Tests de creación
# ---------------------------------------------------------------------------

def test_crear_espacio_retorna_id():
    repo = FakeRepo()
    eid = service.crear_espacio("Sala A", "Descripción", 10, repo=repo)
    assert eid == 1


def test_crear_espacio_persiste_datos():
    repo = FakeRepo()
    service.crear_espacio("Sala A", "Para reuniones", 10, repo=repo)
    e = repo._espacios[0]
    assert e.nombre == "Sala A"
    assert e.descripcion == "Para reuniones"
    assert e.capacidad == 10


def test_crear_espacio_rechaza_nombre_vacio():
    repo = FakeRepo()
    with pytest.raises(ValueError):
        service.crear_espacio("", "desc", 10, repo=repo)


def test_crear_espacio_rechaza_nombre_solo_espacios():
    repo = FakeRepo()
    with pytest.raises(ValueError):
        service.crear_espacio("   ", "desc", 10, repo=repo)


def test_crear_espacio_rechaza_capacidad_cero():
    repo = FakeRepo()
    with pytest.raises(ValueError):
        service.crear_espacio("Sala A", "desc", 0, repo=repo)


def test_crear_espacio_rechaza_capacidad_negativa():
    repo = FakeRepo()
    with pytest.raises(ValueError):
        service.crear_espacio("Sala A", "desc", -5, repo=repo)


def test_crear_espacio_trim_nombre():
    repo = FakeRepo()
    service.crear_espacio("  Sala A  ", "desc", 5, repo=repo)
    assert repo._espacios[0].nombre == "Sala A"


# ---------------------------------------------------------------------------
# Tests de listado
# ---------------------------------------------------------------------------

def test_listar_espacios_vacio():
    repo = FakeRepo()
    resultado = service.listar_espacios(repo=repo)
    assert resultado == []


def test_listar_espacios_retorna_todos():
    repo = FakeRepo()
    service.crear_espacio("Sala A", "", 10, repo=repo)
    service.crear_espacio("Sala B", "", 20, repo=repo)
    resultado = service.listar_espacios(repo=repo)
    assert len(resultado) == 2


# ---------------------------------------------------------------------------
# Tests de obtención por id
# ---------------------------------------------------------------------------

def test_obtener_espacio_existente():
    repo = FakeRepo()
    eid = service.crear_espacio("Sala A", "desc", 10, repo=repo)
    espacio = service.obtener_espacio(eid, repo=repo)
    assert espacio.nombre == "Sala A"


def test_obtener_espacio_inexistente_lanza_error():
    repo = FakeRepo()
    with pytest.raises(EspacioNoEncontradoError):
        service.obtener_espacio(999, repo=repo)
