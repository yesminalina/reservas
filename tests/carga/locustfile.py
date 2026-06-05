"""
Pruebas de carga con Locust.
Simula usuarios concurrentes realizando las operaciones más frecuentes del sistema.

Ejecutar con UI:
    locust -f tests/carga/locustfile.py --host http://localhost:8000

Ejecutar sin interfaz (headless):
    locust -f tests/carga/locustfile.py --host http://localhost:8000 \
           --headless -u 50 -r 5 -t 1m --csv resultados_carga
"""
from locust import HttpUser, task, between


class UsuarioReservas(HttpUser):
    """
    Simula un usuario autenticado que lista espacios y hace reservas.
    Pesos: listar espacios (frecuente) vs. crear reserva (menos frecuente).
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Inicia sesión antes de comenzar las tareas."""
        self.client.post("/login", data={
            "email": "usuario@demo.cl",
            "password": "Usuario1234",
        }, allow_redirects=True)

    @task(3)
    def listar_espacios(self):
        """Operación más frecuente: consultar espacios disponibles."""
        self.client.get("/espacios")

    @task(2)
    def ver_reservas(self):
        """Consultar reservas propias."""
        self.client.get("/reservas")

    @task(1)
    def crear_reserva(self):
        """Crear una reserva (operación de escritura, menos frecuente)."""
        self.client.post("/reservas", data={
            "espacio_id": 1,
            "inicio": "2027-01-15 09:00",
            "fin": "2027-01-15 10:00",
        }, allow_redirects=False)


class UsuarioAnonimo(HttpUser):
    """
    Simula un visitante no autenticado consultando la página de espacios.
    Representa el tráfico de descubrimiento.
    """
    wait_time = between(2, 5)

    @task
    def listar_espacios_publico(self):
        self.client.get("/espacios")
