# Plan: Creación del Sistema de Reservas (Monolito Modular en Python puro)

## Contexto

El directorio del proyecto está vacío salvo `CLAUDE.md` y las tres skills (`monolito-modular-python`, `testing-reservas`, `despliegue-cpanel`). Hay que construir **desde cero** la aplicación web de reservas del Módulo 2: un monolito modular en **Python puro** (sin frameworks), con MySQL vía PyMySQL, desplegable como app WSGI bajo Passenger en cPanel. El diseño no es abierto: `CLAUDE.md` fija la estructura de carpetas y las skills fijan los patrones de código por capa. Este plan materializa esa especificación en una app **funcional de punta a punta**.

**Decisiones del usuario:**
- **Alcance**: app completa end-to-end (3 módulos + presentación + datos + seguridad + devserver + tests unitarios + carga + artefactos de despliegue).
- **Roles**: el modelo `Usuario` tiene campo `rol` (`'admin'` | `'usuario'`). Solo `admin` crea/edita espacios; cualquier usuario autenticado reserva.
- **Seed**: se incluye `db/seed.sql` con un usuario demo (hash pregenerado) y espacios de ejemplo.

## Principios que rigen cada archivo (no negociables)

- **Tres capas**: presentación (HTML, sin lógica/SQL) → negocio (`service`) → datos (`repository` + `db.py`).
- **Regla de oro del acoplamiento**: dentro del módulo `service → repository → db`; entre módulos solo se llama al `service` del otro (interfaz pública), nunca su `repository` ni sus tablas.
- **SQL siempre parametrizado** (`%s`), nunca f-strings con datos de usuario → anti inyección.
- **Servicios testeables**: cada función de `service` acepta `repo=<repo_real>` como parámetro opcional, para inyectar un fake en los tests (patrón de la skill `testing-reservas`).
- **Sin secretos en el repo**: credenciales solo por variables de entorno; `.env` en `.gitignore`.

## Estructura a crear

Replica exactamente el árbol de `CLAUDE.md`. Archivos clave y su responsabilidad:

### Raíz
- `requirements.txt` → `pymysql`.
- `requirements-dev.txt` → `pytest`, `pytest-cov`, `locust`.
- `.env.example` → `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY` (sin valores reales).
- `.gitignore` → `.env`, `.venv`, `__pycache__/`, `*.pyc`, `resultados_carga*`.
- `passenger_wsgi.py` → solo `sys.path.insert(...)` + `from app.wsgi import application` (skill despliegue, paso 5).
- `README.md` → setup local, comandos, arquitectura, despliegue (resumen).

### `app/` (núcleo)
- `app/config.py` → lee variables de entorno (con defaults seguros para `DB_PORT`); expone `SECRET_KEY`.
- `app/db.py` → `obtener_conexion()` con PyMySQL, `DictCursor`, `autocommit=False`, parámetros desde entorno (patrón exacto de la skill `monolito-modular-python`).
- `app/seguridad.py` → `hash_password`/`verificar_password` con `pbkdf2_hmac` + salt; **además** `firmar_cookie`/`verificar_cookie` con `hmac` para la sesión (cookie firmada `usuario_id:rol:firma`). Flag `Secure` asumido en prod.
- `app/router.py` → registro `(metodo, path) -> handler` con decorador `@ruta`, función `despachar(environ)`. Soporta rutas exactas; el body POST se parsea en el handler.
- `app/wsgi.py` → callable `application(environ, start_response)`; traduce `(status, content_type, body, headers)` del handler a la respuesta WSGI; maneja cookies (`Set-Cookie`) y 404/500.
- `app/devserver.py` → `wsgiref.simple_server` en `http://localhost:8000` cargando `.env` (lectura simple del archivo) para desarrollo.

### `app/presentacion/`
- `views.py` → `render(nombre, **ctx)` con `string.Template.safe_substitute`; **escapa** todo input de usuario con `html.escape`. Aquí viven los **handlers** registrados con `@ruta`: parsean input, leen la cookie de sesión, llaman al `service` correcto y devuelven HTML. Nunca SQL aquí.
- `templates/` → `base.html`, `login.html`, `registro.html`, `espacios.html` (listado + form admin), `reservas.html` (mis reservas + form crear), `mensaje.html` (errores/confirmaciones).

### Módulos de dominio (cada uno: `models.py`, `repository.py`, `service.py`)
- **`app/usuarios/`**
  - `models.py`: `@dataclass Usuario(id, nombre, email, salt, password_hash, rol)`.
  - `repository.py`: `crear`, `buscar_por_email`.
  - `service.py`: `registrar(nombre, email, password, rol='usuario')` (hashea, valida email único), `autenticar(email, password)` (verifica hash, devuelve `Usuario` o `None`). Reglas: nunca password en texto plano.
- **`app/espacios/`**
  - `models.py`: `@dataclass Espacio(id, nombre, descripcion, capacidad)`.
  - `repository.py`: `crear`, `listar`, `obtener_por_id`.
  - `service.py`: `crear_espacio(...)` (validación de datos; **la autorización admin se chequea en el handler** con el rol de la sesión, no en el service, para que el service quede agnóstico de sesión), `listar_espacios`, `obtener_espacio`.
- **`app/reservas/`**
  - `models.py`: `@dataclass Reserva(id, usuario_id, espacio_id, inicio, fin, estado)`.
  - `repository.py`: `crear`, `hay_solapamiento`, `listar_por_usuario`, `cancelar` (estado→`'cancelada'`).
  - `service.py`: `crear_reserva(usuario_id, espacio_id, inicio, fin, repo=repo_real)` con la **regla de no solapamiento** (`EspacioOcupadoError`); `listar_de_usuario`; `cancelar_reserva(reserva_id, usuario_id)` (solo el dueño cancela). Cruce de módulos: para validar que el `espacio_id` existe, `reservas.service` llama a `espacios.service.obtener_espacio` (no a su repository).

### `db/`
- `schema.sql` → DDL de `usuarios` (con `rol`, `email UNIQUE`), `espacios`, `reservas` (FKs a usuarios/espacios, `estado`, **índice** sobre `(espacio_id, estado, inicio, fin)` para acelerar `hay_solapamiento` y soportar el hallazgo del informe de carga).
- `seed.sql` → 1 usuario admin demo + 1 usuario normal (hashes pregenerados con el mismo `pbkdf2_hmac`) + 3–4 espacios de ejemplo.

### `tests/`
- `tests/unit/test_usuarios.py` → registro hashea (no guarda texto plano), login válido/ inválido.
- `tests/unit/test_espacios.py` → crear y listar, validación de datos.
- `tests/unit/test_reservas.py` → crea cuando libre, rechaza por solapamiento (`EspacioOcupadoError`), cancelar cambia estado. Todos con **FakeRepo en memoria** (sin MySQL), patrón de la skill.
- `tests/carga/locustfile.py` → `UsuarioReservas` con tareas `GET /espacios` (peso 3) y `POST /reservas` (peso 1), `wait_time = between(1,3)`.

## Rutas WSGI (mapa handler ↔ service)

| Método | Ruta | Handler → Service |
|---|---|---|
| GET | `/` | redirige a `/espacios` |
| GET/POST | `/registro` | `usuarios.service.registrar` |
| GET/POST | `/login` | `usuarios.service.autenticar` → set cookie firmada |
| POST | `/logout` | limpia cookie |
| GET | `/espacios` | `espacios.service.listar_espacios` |
| POST | `/espacios` | (solo rol admin) `espacios.service.crear_espacio` |
| GET | `/reservas` | `reservas.service.listar_de_usuario` (requiere sesión) |
| POST | `/reservas` | `reservas.service.crear_reserva` (requiere sesión) |
| POST | `/reservas/cancelar` | `reservas.service.cancelar_reserva` (dueño) |

Helper de presentación `usuario_actual(environ)` que lee/verifica la cookie firmada y devuelve `(usuario_id, rol)` o `None`; los handlers protegidos redirigen a `/login` si no hay sesión.

## Orden de implementación

1. Andamiaje raíz: `requirements*.txt`, `.env.example`, `.gitignore`, `passenger_wsgi.py`, `README.md`.
2. Núcleo: `config.py`, `db.py`, `seguridad.py`.
3. Datos: `db/schema.sql`, `db/seed.sql`.
4. Módulos de dominio en orden `usuarios → espacios → reservas` (models, repository, service).
5. WSGI: `router.py`, `wsgi.py`, `devserver.py`.
6. Presentación: `views.py` + handlers + `templates/`.
7. Tests unitarios (los 3) + `locustfile.py`.

Aplicar las skills al construir cada parte: `monolito-modular-python` para los módulos/WSGI/seguridad, `testing-reservas` para los tests, `despliegue-cpanel` para `passenger_wsgi.py` y el README de despliegue.

## Verificación (end-to-end)

1. **Unitarias** (sin BD, deben pasar sin MySQL):
   ```
   pytest tests/unit -v
   pytest --cov=app tests/unit
   ```
2. **App local** (requiere MySQL con `schema.sql`+`seed.sql` cargados y `.env` completo):
   ```
   python -m app.devserver        # http://localhost:8000
   ```
   Flujo manual: registro → login → `/espacios` (admin crea uno) → crear reserva → intentar reserva solapada (debe rechazar) → cancelar → logout.
3. **Carga**:
   ```
   locust -f tests/carga/locustfile.py --host http://localhost:8000 \
          --headless -u 50 -r 5 -t 1m --csv resultados_carga
   ```
   Con los CSV + el output de cobertura se arma el **Informe de pruebas** (unitarias, carga, hallazgos) descrito en la skill `testing-reservas`.

## Entregables que cubre este plan

Código fuente + README, informe de pruebas (estructura lista para llenar con números reales), y todo el árbol listo para subir a GitHub y desplegar en cPanel siguiendo la skill `despliegue-cpanel`. (El diagrama de arquitectura ya existe según la consigna; el de clases se deriva de los `models.py`/`service.py` resultantes.)
