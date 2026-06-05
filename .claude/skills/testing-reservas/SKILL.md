---
name: testing-reservas
description: Escribe y ejecuta las pruebas del sistema de reservas — unitarias con pytest y de carga con Locust — y arma el informe de pruebas que pide la consigna. Úsala SIEMPRE que se escriban, corran o agreguen tests, se busque cubrir un módulo (usuarios, espacios, reservas), se mida rendimiento bajo carga, o se prepare el "Informe de pruebas" entregable. La consigna menciona JUnit, pero como el proyecto es en Python, el equivalente para unitarias es pytest y para carga es Locust. Aplícala incluso si el usuario solo dice "probemos esto" o "verifiquemos que funciona".
---

# Testing del Sistema de Reservas

El proyecto exige dos tipos de prueba: **unitarias** (verifican cada componente) y **de carga** (verifican el rendimiento con muchos usuarios concurrentes). Herramientas: `pytest` para unitarias, `locust` para carga. Ambas son dependencias de desarrollo (`requirements-dev.txt`), no van al runtime de producción.

## Principio: probar el `service` sin tocar MySQL

La capa de negocio (`service`) es donde viven las reglas, y es lo que más conviene probar. Para que las pruebas unitarias sean **rápidas y deterministas**, no deben conectarse a la base de datos real: se inyecta un **repository falso (fake)** en memoria. Esto es justo el pago del bajo acoplamiento del diseño — si el `service` no estuviera desacoplado del `repository`, no se podría testear así.

Por eso, escribe los `service` de modo que el repository sea sustituible. Patrón simple: que las funciones del `service` acepten el módulo repository como parámetro opcional con default al real.
```python
# service.py (forma testeable)
from app.reservas import repository as repo_real
from app.reservas.models import Reserva

def crear_reserva(usuario_id, espacio_id, inicio, fin, repo=repo_real):
    if repo.hay_solapamiento(espacio_id, inicio, fin):
        raise EspacioOcupadoError("Espacio ocupado.")
    return repo.crear(Reserva(None, usuario_id, espacio_id, inicio, fin, "activa"))
```

## Estructura de las pruebas unitarias

`tests/unit/` espeja los módulos: `test_usuarios.py`, `test_espacios.py`, `test_reservas.py`.

Ejemplo con un repository falso (sin BD):
```python
# tests/unit/test_reservas.py
import pytest
from app.reservas import service
from app.reservas.service import EspacioOcupadoError

class FakeRepo:
    def __init__(self, ocupado=False):
        self._ocupado = ocupado
        self.creadas = []
    def hay_solapamiento(self, espacio_id, inicio, fin):
        return self._ocupado
    def crear(self, reserva):
        self.creadas.append(reserva)
        return 1

def test_crea_reserva_cuando_espacio_libre():
    repo = FakeRepo(ocupado=False)
    rid = service.crear_reserva(1, 10, "2025-01-01 09:00", "2025-01-01 10:00", repo=repo)
    assert rid == 1
    assert len(repo.creadas) == 1

def test_rechaza_reserva_cuando_espacio_ocupado():
    repo = FakeRepo(ocupado=True)
    with pytest.raises(EspacioOcupadoError):
        service.crear_reserva(1, 10, "2025-01-01 09:00", "2025-01-01 10:00", repo=repo)
```

Qué cubrir como mínimo por módulo:
- **usuarios**: registro hashea la contraseña; login válido / inválido; no se guarda contraseña en texto plano.
- **espacios**: crear y listar espacios; validación de datos.
- **reservas**: crear cuando está libre; rechazar cuando hay solapamiento; cancelar cambia el estado a "cancelada".

Ejecutar:
```
pytest tests/unit -v
pytest --cov=app tests/unit        # reporte de cobertura
```
Apunta a cubrir todas las reglas de negocio del `service`. La cobertura no es un fin en sí mismo: prioriza los caminos con reglas (validaciones, errores), no los getters triviales.

## Pruebas de carga con Locust

Validan que el sistema mantenga un tiempo de respuesta bajo con múltiples usuarios concurrentes (aspecto de performance de la consigna).
```python
# tests/carga/locustfile.py
from locust import HttpUser, task, between

class UsuarioReservas(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def listar_espacios(self):
        self.client.get("/espacios")

    @task(1)
    def crear_reserva(self):
        self.client.post("/reservas", data={
            "espacio_id": 10,
            "inicio": "2025-01-01 09:00",
            "fin": "2025-01-01 10:00",
        })
```
Ejecutar (UI web en http://localhost:8089) o sin interfaz:
```
locust -f tests/carga/locustfile.py --host http://localhost:8000
locust -f tests/carga/locustfile.py --host http://localhost:8000 \
       --headless -u 50 -r 5 -t 1m --csv resultados_carga
```
`-u` usuarios simulados, `-r` cuántos por segundo se suman, `-t` duración. El flag `--csv` deja archivos con métricas para el informe.

## Informe de pruebas (entregable)

Documenta, en este orden:
1. **Pruebas unitarias**: qué módulos y reglas se probaron, total de tests y resultado, y el porcentaje de cobertura.
2. **Pruebas de carga**: configuración usada (usuarios, ramp-up, duración), y resultados clave → peticiones/segundo, tiempo de respuesta (mediana y percentil 95) y tasa de fallos.
3. **Hallazgos y soluciones**: cualquier problema detectado (ej. consulta lenta) y cómo se corrigió (ej. índice en la tabla `reservas`).

Mantén el informe en lenguaje claro y con los números directos de los reportes de pytest y los CSV de Locust; no inventes cifras.
