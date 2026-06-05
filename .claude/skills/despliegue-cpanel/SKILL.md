---
name: despliegue-cpanel
description: Despliega la app WSGI de reservas (Python puro) en cPanel usando Passenger y MySQL, sin AWS ni Docker. Úsala SIEMPRE que se hable de subir/publicar la app, configurar el servidor, el panel cPanel, Passenger, el archivo passenger_wsgi.py, crear la base de datos MySQL, importar el esquema, configurar variables de entorno en el panel, instalar dependencias en el hosting, o activar HTTPS/AutoSSL. Aplícala aunque el usuario solo diga "ya quiero probarlo en el servidor" o "cómo lo publico". El servidor del curso es g21.origenet.cl.
---

# Despliegue en cPanel (Passenger + MySQL)

Guía para publicar el monolito modular en el hosting del curso. La app es **Python puro** y se expone como callable WSGI que Passenger ejecuta. Los nombres exactos de los menús pueden variar según la versión de cPanel del hosting; si un menú no aparece con el nombre indicado, busca el equivalente.

## Regla de seguridad antes de empezar

Las credenciales (de la base de datos y la `SECRET_KEY`) se cargan **como variables de entorno dentro del panel**, nunca en el código ni en archivos del repositorio. El `.env` y los secretos van en `.gitignore`. Esto evita que las credenciales del servidor terminen publicadas en GitHub.

## Paso 1 — Base de datos MySQL

En cPanel → **MySQL® Databases**:
1. Crea una base de datos (el panel le antepone un prefijo, ej. `g21origenet_reservas`).
2. Crea un usuario de base de datos con contraseña fuerte.
3. Asocia el usuario a la base con **ALL PRIVILEGES**.
4. Anota host, nombre de base, usuario y contraseña → irán como variables de entorno (paso 3), no al repo.

Importa el esquema en cPanel → **phpMyAdmin** → selecciona la base → pestaña **Importar** → sube `db/schema.sql`.

## Paso 2 — Crear la aplicación Python

En cPanel → **Setup Python App** (a veces "Aplicaciones de Python"):
1. **Create Application**.
2. Elige la versión de Python disponible.
3. **Application root**: carpeta donde subirás el código (ej. `reservas`).
4. **Application URL**: el dominio/subdominio (ej. `g21.origenet.cl`).
5. **Application startup file**: `passenger_wsgi.py`.
6. **Application Entry point**: `application`.
7. Crea la app. cPanel genera un **virtualenv** y muestra el comando para activarlo por SSH.

Sube el código del proyecto al *Application root* (vía Git, Administrador de archivos o FTP). No subas `.env`, `.venv` ni `__pycache__`.

## Paso 3 — Variables de entorno

En la misma pantalla de la app Python, sección **Environment variables**, agrega:
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`.
(En hosting compartido `DB_HOST` suele ser `localhost`.)

## Paso 4 — Instalar dependencias

Opción A — desde la UI: en "Configuration files" indica `requirements.txt` y usa **Run Pip Install**.
Opción B — por SSH: activa el virtualenv (el panel da el comando exacto) y ejecuta:
```
pip install -r requirements.txt
```
Solo el runtime (`pymysql`); las dependencias de testing no se instalan en producción.

## Paso 5 — passenger_wsgi.py

En la raíz de la app, este archivo conecta Passenger con el callable WSGI:
```python
# passenger_wsgi.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.wsgi import application  # noqa: F401
```
Passenger busca un objeto llamado `application`. No pongas lógica aquí; solo el import.

## Paso 6 — Reiniciar y verificar

En la pantalla de la app Python pulsa **Restart**. Luego abre la Application URL en el navegador.
Si hay error 500, revisa el log de la app (botón de logs en el panel o `stderr.log` en la carpeta de la app). Los fallos más comunes: variable de entorno faltante, dependencia no instalada, o ruta incorrecta en `passenger_wsgi.py`.

## Paso 7 — HTTPS (AutoSSL)

En cPanel → **SSL/TLS Status** → ejecuta **Run AutoSSL** sobre el dominio para emitir el certificado Let's Encrypt. Verifica que el sitio cargue por `https://`. La app debe asumir HTTPS en producción (cookies de sesión con flag `Secure`).

## Checklist de despliegue

1. Base creada y `schema.sql` importado.
2. App Python creada con `passenger_wsgi.py` como startup y `application` como entry point.
3. Variables de entorno cargadas en el panel (no en el repo).
4. `pip install -r requirements.txt` ejecutado en el virtualenv de la app.
5. App reiniciada y respondiendo.
6. AutoSSL activo, sitio por HTTPS.
