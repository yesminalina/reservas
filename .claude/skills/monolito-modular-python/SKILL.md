---
name: monolito-modular-python
description: Construye y mantiene los módulos del sistema de reservas en Python puro (sin frameworks), respetando la arquitectura en capas y el bajo acoplamiento. Úsala SIEMPRE que se cree o edite un módulo de dominio (usuarios, espacios, reservas), se agregue una ruta o handler al WSGI, se escriba código de repository/service/models, se conecte a MySQL, o haya dudas sobre cómo organizar las capas y la comunicación entre módulos en este proyecto. Aplícala aunque el usuario no mencione "arquitectura" explícitamente: cualquier código nuevo del backend debe pasar por estas reglas.
---

# Monolito Modular en Python puro

Reglas y patrones para escribir el backend del sistema de reservas. El objetivo es un **monolito modular**: una sola app desplegable, internamente dividida en módulos cohesivos y débilmente acoplados, en **tres capas** (presentación, lógica de negocio, datos). Sin frameworks: solo librería estándar de Python + PyMySQL para la base de datos.

## Las tres capas y la regla de oro

- **Presentación** (`app/presentacion/`): genera HTML. No contiene lógica de negocio ni SQL.
- **Lógica de negocio** (módulos `usuarios`, `espacios`, `reservas`): reglas del dominio.
- **Datos** (`app/db.py` + cada `repository.py`): acceso a MySQL.

**Regla de oro del acoplamiento:** dentro de un módulo el flujo es `service` → `repository` → `db`. Entre módulos, uno solo llama al **`service`** de otro (su interfaz pública). Nunca importes el `repository` ni leas las tablas de otro módulo directamente. Esto es lo que mantiene el bajo acoplamiento y permite extraer un módulo a futuro sin romper el resto.

## Anatomía de un módulo

Cada módulo de dominio tiene exactamente tres archivos:

```
app/<modulo>/
├── models.py       # dataclasses (estructuras de datos del dominio)
├── repository.py   # funciones que ejecutan SQL y devuelven dataclasses
└── service.py      # reglas de negocio + interfaz pública del módulo
```

**`models.py`** — usa `@dataclass`, nada de lógica:
```python
from dataclasses import dataclass

@dataclass
class Reserva:
    id: int | None
    usuario_id: int
    espacio_id: int
    inicio: str
    fin: str
    estado: str  # "activa" | "cancelada"
```

**`repository.py`** — solo acceso a datos, siempre con consultas parametrizadas:
```python
from app.db import obtener_conexion
from app.reservas.models import Reserva

def crear(reserva: Reserva) -> int:
    sql = """INSERT INTO reservas (usuario_id, espacio_id, inicio, fin, estado)
             VALUES (%s, %s, %s, %s, %s)"""
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (reserva.usuario_id, reserva.espacio_id,
                          reserva.inicio, reserva.fin, reserva.estado))
        conn.commit()
        return cur.lastrowid

def hay_solapamiento(espacio_id: int, inicio: str, fin: str) -> bool:
    sql = """SELECT 1 FROM reservas
             WHERE espacio_id = %s AND estado = 'activa'
               AND inicio < %s AND fin > %s LIMIT 1"""
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(sql, (espacio_id, fin, inicio))
        return cur.fetchone() is not None
```

**`service.py`** — reglas de negocio; es lo único que otros módulos pueden llamar:
```python
from app.reservas import repository
from app.reservas.models import Reserva

class EspacioOcupadoError(Exception):
    pass

def crear_reserva(usuario_id: int, espacio_id: int, inicio: str, fin: str) -> int:
    # Regla de negocio: no se permite doble reserva del mismo espacio.
    if repository.hay_solapamiento(espacio_id, inicio, fin):
        raise EspacioOcupadoError("El espacio ya está reservado en ese horario.")
    return repository.crear(Reserva(None, usuario_id, espacio_id, inicio, fin, "activa"))
```

## Acceso a datos (`app/db.py`)

Una sola función de conexión, parametrizada por variables de entorno. **Nunca** credenciales en el código.
```python
import os, pymysql

def obtener_conexion():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
```
Reglas SQL: usa siempre placeholders `%s`, nunca f-strings ni concatenación con datos del usuario (previene inyección SQL).

## Enrutamiento WSGI sin framework (`app/wsgi.py` + `app/router.py`)

El punto de entrada es un callable WSGI estándar. El router mapea `(método, ruta)` a un handler.
```python
# router.py
RUTAS = {}  # (metodo, ruta) -> handler

def ruta(metodo, path):
    def deco(fn):
        RUTAS[(metodo, path)] = fn
        return fn
    return deco

def despachar(environ):
    clave = (environ["REQUEST_METHOD"], environ["PATH_INFO"])
    handler = RUTAS.get(clave)
    return handler(environ) if handler else (404, "text/plain", b"No encontrado")
```
```python
# wsgi.py
from app.router import despachar

def application(environ, start_response):
    status, content_type, body = despachar(environ)
    start_response(f"{status} OK", [("Content-Type", content_type)])
    return [body if isinstance(body, bytes) else body.encode("utf-8")]
```
Los handlers viven en la capa de presentación, parsean el input y llaman al `service` correspondiente. Un handler **nunca** ejecuta SQL directamente.

## Presentación (`app/presentacion/`)

Renderiza HTML con `string.Template` (stdlib), separando la plantilla de la lógica:
```python
from string import Template
from pathlib import Path

def render(nombre: str, **contexto) -> str:
    plantilla = Path(__file__).parent / "templates" / f"{nombre}.html"
    return Template(plantilla.read_text(encoding="utf-8")).safe_substitute(**contexto)
```
Escapa siempre los valores que vengan del usuario antes de inyectarlos en HTML (usa `html.escape`).

## Seguridad (`app/seguridad.py`)

Contraseñas con `pbkdf2_hmac` (stdlib), salt único por usuario:
```python
import hashlib, os, hmac

def hash_password(password: str) -> tuple[str, str]:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex(), dk.hex()

def verificar_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
    return hmac.compare_digest(dk.hex(), hash_hex)
```

## Checklist al agregar funcionalidad

1. ¿La lógica de negocio quedó en `service`, no en el handler ni en el repository?
2. ¿El SQL está parametrizado y aislado en `repository`?
3. ¿Si un módulo necesita datos de otro, lo pide al `service` del otro (no a su repository)?
4. ¿La presentación escapa el input del usuario?
5. ¿Hay una prueba unitaria nueva en `tests/unit/` para esta lógica? (ver skill `testing-reservas`)
