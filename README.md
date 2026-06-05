# Sistema de Reservas — Módulo 2

Aplicación web para reservar espacios y recursos. Monolito modular en **Python puro** (sin frameworks), con MySQL y despliegue en cPanel como app WSGI bajo Passenger.

## Arquitectura

```
Presentación  →  Lógica de negocio  →  Datos
(views.py)       (service.py x3)       (repository.py x3 + db.py)
```

Tres módulos de dominio: `usuarios`, `espacios`, `reservas`.  
Regla de acoplamiento: un módulo solo llama al `service` de otro (nunca a su `repository` ni a sus tablas).

## Setup local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # completar con tus credenciales MySQL locales
```

Cargar el esquema y los datos de ejemplo en MySQL:

```bash
mysql -u <user> -p <db> < db/schema.sql
mysql -u <user> -p <db> < db/seed.sql
```

Correr el servidor de desarrollo:

```bash
python -m app.devserver        # http://localhost:8000
```

### Usuarios de prueba (seed)

| Email | Contraseña | Rol |
|---|---|---|
| admin@demo.cl | Admin1234 | admin |
| usuario@demo.cl | Usuario1234 | usuario |

## Pruebas

```bash
# Unitarias (sin MySQL)
pytest tests/unit -v
pytest --cov=app tests/unit

# Carga (requiere la app corriendo en localhost:8000)
locust -f tests/carga/locustfile.py --host http://localhost:8000
# Headless:
locust -f tests/carga/locustfile.py --host http://localhost:8000 \
       --headless -u 50 -r 5 -t 1m --csv resultados_carga
```

## Rutas disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Redirige a `/espacios` |
| GET/POST | `/registro` | Crear cuenta |
| GET/POST | `/login` | Iniciar sesión |
| POST | `/logout` | Cerrar sesión |
| GET | `/espacios` | Listar espacios |
| POST | `/espacios` | Crear espacio (solo admin) |
| GET | `/reservas` | Mis reservas (requiere sesión) |
| POST | `/reservas` | Crear reserva (requiere sesión) |
| POST | `/reservas/cancelar` | Cancelar reserva propia |

## Despliegue en cPanel (`g21.origenet.cl`)

1. En **MySQL® Databases**: crear base, usuario y asignar ALL PRIVILEGES.
2. Importar `db/schema.sql` (y opcionalmente `db/seed.sql`) vía phpMyAdmin.
3. En **Setup Python App**: Application root = carpeta del proyecto, startup file = `passenger_wsgi.py`, entry point = `application`.
4. En **Environment variables**: agregar `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`.
5. Ejecutar `pip install -r requirements.txt` en el virtualenv del panel (solo PyMySQL, sin dev).
6. Pulsar **Restart**. Verificar en el navegador.
7. En **SSL/TLS Status**: ejecutar **Run AutoSSL** para habilitar HTTPS.

Ver skill `despliegue-cpanel` para la guía completa paso a paso.

## Seguridad

- Contraseñas con `pbkdf2_hmac` (SHA-256, 200 000 iteraciones) + salt único por usuario.
- Sesión: cookie firmada con `hmac` (SHA-256) usando `SECRET_KEY`.
- Toda consulta SQL usa placeholders `%s` (anti inyección).
- Secretos solo en variables de entorno; `.env` en `.gitignore`.
