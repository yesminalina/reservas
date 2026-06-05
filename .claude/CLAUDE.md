# Sistema de Reservas — Monolito Modular en Python

Aplicación web para reservar espacios y recursos. Proyecto evaluativo del **Módulo 2** del curso de Arquitectura Cloud (Talento Digital / Alkemy).

## Objetivo

Construir una arquitectura de reservas **escalable, segura y eficiente** que permita a los usuarios **crear, consultar y cancelar** reservas en tiempo real, con autenticación de usuarios y datos protegidos.

## Restricciones del proyecto (definidas por el docente, NO negociables)

- **Python puro**: sin frameworks web (nada de Flask/Django). El enrutamiento, el renderizado de HTML, las sesiones y el hashing se resuelven con la librería estándar.
- **Despliegue en cPanel** (no AWS): la app corre como aplicación **WSGI bajo Passenger** en `g21.origenet.cl`.
- **Base de datos MySQL**, accedida con **PyMySQL** (driver escrito en Python puro, no requiere compilar nada en el hosting compartido).
- **Lo más simple posible**: monolito modular. Sin colas, sin caché externa, sin cron, sin notificaciones.

## Arquitectura

Monolito modular en **tres capas** (visión funcional del manual L2):

- **Presentación**: vistas y plantillas HTML.
- **Lógica de negocio**: tres módulos cohesivos → `usuarios`, `espacios`, `reservas`.
- **Datos**: MySQL como fuente única de verdad.

Pilares que guían cada decisión (manual L4): **alta cohesión, bajo acoplamiento, modularidad y mantenibilidad**.

### Regla de acoplamiento (clave para defender el diseño)

Dentro de un módulo el flujo es: `service` → `repository` → `db`.
Entre módulos, uno SOLO se comunica con otro a través de su capa **`service`** (su interfaz pública); nunca toca directamente el `repository` ni las tablas de otro módulo. Esto mantiene el bajo acoplamiento y permite, a futuro, extraer un módulo como servicio independiente sin reescribir el resto.

## Estructura de carpetas

```
reservas/
├── CLAUDE.md
├── README.md
├── requirements.txt          # runtime: pymysql
├── requirements-dev.txt      # desarrollo: pytest, pytest-cov, locust
├── passenger_wsgi.py         # punto de entrada para cPanel/Passenger
├── .env.example              # plantilla de variables (SIN secretos reales)
├── .gitignore                # ignora .env, .venv, __pycache__
├── app/
│   ├── __init__.py
│   ├── wsgi.py               # callable application(environ, start_response)
│   ├── router.py             # mapeo ruta+método -> handler
│   ├── db.py                 # conexión MySQL (PyMySQL), consultas parametrizadas
│   ├── config.py             # lee variables de entorno
│   ├── seguridad.py          # hashing de contraseñas + firma de cookies
│   ├── devserver.py          # servidor local (wsgiref) para desarrollo
│   ├── presentacion/
│   │   ├── __init__.py
│   │   ├── views.py          # render de vistas
│   │   └── templates/        # plantillas HTML (string.Template)
│   ├── usuarios/             # módulo Autenticación/Usuarios
│   │   ├── __init__.py
│   │   ├── models.py         # dataclass Usuario
│   │   ├── repository.py     # SQL de usuarios
│   │   └── service.py        # lógica + interfaz pública del módulo
│   ├── espacios/             # módulo Espacios/Recursos (misma estructura)
│   └── reservas/             # módulo Reservas (misma estructura)
├── db/
│   └── schema.sql            # DDL de las tablas
└── tests/
    ├── unit/                 # pruebas unitarias por módulo (pytest)
    └── carga/
        └── locustfile.py     # pruebas de carga (Locust)
```

## Stack y dependencias

- **Runtime**: Python 3.x (el que ofrezca el "Setup Python App" de cPanel).
- **DB driver**: PyMySQL (pure-Python).
- **Hashing de contraseñas**: `hashlib.pbkdf2_hmac` (stdlib) + salt único por usuario.
- **Sesiones**: cookie firmada con `hmac` (stdlib), sin dependencias externas.
- **Testing**: `pytest` (unitarias) + `locust` (carga). Son dependencias de desarrollo; NO van al runtime de producción.

## Comandos

Setup local:
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # completar valores locales
```
Cargar el esquema en MySQL:
```
mysql -u <user> -p <db> < db/schema.sql
```
Correr en local:
```
python -m app.devserver        # wsgiref en http://localhost:8000
```
Pruebas unitarias y cobertura:
```
pytest tests/unit -v
pytest --cov=app tests/unit
```
Pruebas de carga:
```
locust -f tests/carga/locustfile.py --host http://localhost:8000
```

## Configuración (variables de entorno)

La app lee TODO de variables de entorno (ver `.env.example`). Variables esperadas:
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`.

## Seguridad — reglas

- **Nunca** escribir credenciales reales en el código ni en archivos versionados. `.env`, secretos y las credenciales del cPanel van en `.gitignore` y jamás se commitean. En producción se cargan como variables de entorno **dentro del panel**, no en el repo.
- Contraseñas: siempre con `pbkdf2_hmac` + salt; nunca en texto plano.
- **Toda** consulta SQL usa parámetros (placeholders `%s`), nunca concatenación de strings → evita inyección SQL.
- HTTPS obligatorio en producción (AutoSSL de cPanel).

## Skills del proyecto (`.claude/skills/`)

- **`monolito-modular-python`**: cómo crear y mantener módulos respetando las capas y el bajo acoplamiento.
- **`testing-reservas`**: cómo escribir pruebas unitarias (pytest) y de carga (Locust), y armar el informe de pruebas.
- **`despliegue-cpanel`**: cómo desplegar la app WSGI en cPanel con Passenger y MySQL.

## Entregables (consigna del Módulo 2)

Código fuente + README, diagrama de arquitectura (ya generado) y de clases, informe de pruebas (unitarias + carga), presentación final, y todo subido a un repositorio de GitHub.
