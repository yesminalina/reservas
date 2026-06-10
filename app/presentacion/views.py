"""
Capa de presentación: handlers HTTP + función render().
Los handlers registran rutas con @ruta, parsean el input,
leen la sesión y delegan en los services.
NUNCA ejecutan SQL directamente.
"""
import html
import urllib.parse
from http.cookies import SimpleCookie
from pathlib import Path
from string import Template

from app.router import ruta
from app.seguridad import firmar_cookie, verificar_cookie
from app.usuarios import service as usuarios_svc
from app.usuarios.service import EmailDuplicadoError, CredencialesInvalidasError
from app.espacios import service as espacios_svc
from app.espacios.service import EspacioNoEncontradoError
from app.reservas import service as reservas_svc
from app.reservas.service import EspacioOcupadoError, ReservaNoAutorizadaError


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------

_TPL_DIR = Path(__file__).parent / "templates"


def render(plantilla: str, **contexto) -> str:
    """
    Renderiza la plantilla <plantilla>.html con string.Template.safe_substitute.
    Los valores del contexto deben llegar ya escapados con html.escape()
    cuando provengan de datos de usuario.
    """
    plantilla_path = _TPL_DIR / f"{plantilla}.html"
    return Template(plantilla_path.read_text(encoding="utf-8")).safe_substitute(**contexto)


def _esc(valor) -> str:
    """Escapa un valor para insertar de forma segura en HTML."""
    return html.escape(str(valor))


def _error_block(msg: str) -> str:
    """Genera el bloque HTML de error, o cadena vacía si no hay mensaje."""
    if not msg:
        return ""
    return f'<div class="error">{msg}</div>'


def _leer_body(environ) -> dict:
    """Lee y parsea el body de una petición POST (application/x-www-form-urlencoded)."""
    try:
        length = int(environ.get("CONTENT_LENGTH", 0) or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length).decode("utf-8")
    return urllib.parse.parse_qs(raw, keep_blank_values=True)


def _campo(form: dict, nombre: str) -> str:
    """Extrae el primer valor de un campo del formulario, o '' si no existe."""
    valores = form.get(nombre, [""])
    return valores[0] if valores else ""


def _usuario_actual(environ) -> tuple[int, str] | None:
    """
    Lee la cookie de sesión y devuelve (usuario_id, rol) o None.
    """
    cookie_header = environ.get("HTTP_COOKIE", "")
    if not cookie_header:
        return None
    jar = SimpleCookie()
    jar.load(cookie_header)
    morsel = jar.get("sesion")
    if morsel is None:
        return None
    return verificar_cookie(morsel.value)


def _redir(path: str) -> tuple:
    """Genera una respuesta de redirección 302."""
    return (302, "text/plain", b"", [("Location", path)])


def _html(contenido: str, status: int = 200) -> tuple:
    """Envuelve HTML en una respuesta 200 (o status dado)."""
    return (status, "text/html; charset=utf-8", contenido.encode("utf-8"), [])


def _set_cookie_header(valor: str) -> tuple:
    """Devuelve el header Set-Cookie para la cookie de sesión."""
    # HttpOnly: no accesible desde JS. SameSite=Lax: protege CSRF básico.
    # Secure se activa en producción (HTTPS) — Passenger lo maneja via HTTPS.
    return ("Set-Cookie", f"sesion={valor}; HttpOnly; SameSite=Lax; Path=/")


def _clear_cookie_header() -> tuple:
    """Devuelve el header Set-Cookie para eliminar la cookie de sesión."""
    return ("Set-Cookie", "sesion=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

#@ruta("GET", "/")
#def inicio(environ):
#   return _redir("/espacios")
@ruta("GET", "/")
def inicio(environ):
    sesion = _usuario_actual(environ)
    if sesion:
        return _redir("/espacios") # Si está logueado, va a espacios
    else:
        return _redir("/login")    # Si no, va al login


# --- Registro ---

@ruta("GET", "/registro")
def registro_get(environ):
    sesion = _usuario_actual(environ)
    if sesion:
        return _redir("/espacios")
    return _html(render("registro", error_block="", nombre="", email=""))


@ruta("POST", "/registro")
def registro_post(environ):
    form = _leer_body(environ)
    nombre = _campo(form, "nombre")
    email = _campo(form, "email")
    password = _campo(form, "password")

    try:
        usuarios_svc.registrar(nombre, email, password)
    except EmailDuplicadoError as e:
        return _html(render("registro", error_block=_error_block(_esc(str(e))),
                             nombre=_esc(nombre), email=_esc(email)), 400)
    except ValueError as e:
        return _html(render("registro", error_block=_error_block(_esc(str(e))),
                             nombre=_esc(nombre), email=_esc(email)), 400)

    return _html(render("mensaje",
                        titulo="¡Registro exitoso!",
                        mensaje="Tu cuenta fue creada. Ahora puedes iniciar sesión.",
                        enlace="/login",
                        texto_enlace="Iniciar sesión"))


# --- Login / Logout ---

@ruta("GET", "/login")
def login_get(environ):
    sesion = _usuario_actual(environ)
    if sesion:
        return _redir("/espacios")
    return _html(render("login", error_block="", email=""))


@ruta("POST", "/login")
def login_post(environ):
    form = _leer_body(environ)
    email = _campo(form, "email")
    password = _campo(form, "password")

    try:
        usuario = usuarios_svc.autenticar(email, password)
    except CredencialesInvalidasError as e:
        return _html(render("login", error_block=_error_block(_esc(str(e))),
                             email=_esc(email)), 401)

    valor_cookie = firmar_cookie(usuario.id, usuario.rol)
    extra = [_set_cookie_header(valor_cookie), ("Location", "/espacios")]
    return (302, "text/plain", b"", extra)


@ruta("POST", "/logout")
def logout(environ):
    return (302, "text/plain", b"", [_clear_cookie_header(), ("Location", "/login")])


# --- Espacios ---

@ruta("GET", "/espacios")
def espacios_get(environ):
    sesion = _usuario_actual(environ)
    lista = espacios_svc.listar_espacios()

    filas_html = ""
    for e in lista:
        filas_html += (
            f"<tr>"
            f"<td>{_esc(e.nombre)}</td>"
            f"<td>{_esc(e.descripcion)}</td>"
            f"<td>{_esc(e.capacidad)}</td>"
            f"</tr>\n"
        )

    es_admin = sesion and sesion[1] == "admin"
    form_crear = render("_form_espacio") if es_admin else ""
    nav = _nav_html(sesion)

    return _html(render("espacios",
                         nav=nav,
                         filas=filas_html,
                         form_crear=form_crear,
                         error_block=""))


@ruta("POST", "/espacios")
def espacios_post(environ):
    sesion = _usuario_actual(environ)
    if not sesion:
        return _redir("/login")
    if sesion[1] != "admin":
        return _html(render("mensaje",
                             titulo="Acceso denegado",
                             mensaje="Solo los administradores pueden crear espacios.",
                             enlace="/espacios",
                             texto_enlace="Volver"), 403)

    form = _leer_body(environ)
    nombre = _campo(form, "nombre")
    descripcion = _campo(form, "descripcion")
    capacidad_str = _campo(form, "capacidad")

    try:
        capacidad = int(capacidad_str) if capacidad_str else 0
        espacios_svc.crear_espacio(nombre, descripcion, capacidad)
    except (ValueError, Exception) as e:
        lista = espacios_svc.listar_espacios()
        filas_html = "".join(
            f"<tr><td>{_esc(e2.nombre)}</td><td>{_esc(e2.descripcion)}</td>"
            f"<td>{_esc(e2.capacidad)}</td></tr>"
            for e2 in lista
        )
        nav = _nav_html(sesion)
        form_crear = render("_form_espacio")
        return _html(render("espacios",
                             nav=nav,
                             filas=filas_html,
                             form_crear=form_crear,
                             error_block=_error_block(_esc(str(e)))), 400)

    return _redir("/espacios")


# --- Reservas ---

@ruta("GET", "/reservas")
def reservas_get(environ):
    sesion = _usuario_actual(environ)
    if not sesion:
        return _redir("/login")

    usuario_id, _ = sesion
    lista_reservas = reservas_svc.listar_de_usuario(usuario_id)
    lista_espacios = espacios_svc.listar_espacios()

    # Mapa espacio_id → nombre para mostrar en la tabla
    mapa = {e.id: e.nombre for e in lista_espacios}

    filas_html = ""
    for r in lista_reservas:
        nombre_espacio = _esc(mapa.get(r.espacio_id, f"Espacio #{r.espacio_id}"))
        boton_cancelar = ""
        if r.estado == "activa":
            boton_cancelar = (
                f'<form method="post" action="/reservas/cancelar" style="display:inline">'
                f'<input type="hidden" name="reserva_id" value="{r.id}">'
                f'<button type="submit" class="btn-cancelar"'
                f' onclick="return confirm(\'¿Cancelar esta reserva?\')">Cancelar</button>'
                f'</form>'
            )
        estado_badge = (
            '<span class="badge-activa">Activa</span>' if r.estado == "activa"
            else '<span class="badge-cancelada">Cancelada</span>'
        )
        filas_html += (
            f"<tr>"
            f"<td>{nombre_espacio}</td>"
            f"<td>{_esc(r.inicio)}</td>"
            f"<td>{_esc(r.fin)}</td>"
            f"<td>{estado_badge}</td>"
            f"<td>{boton_cancelar}</td>"
            f"</tr>\n"
        )

    # Opciones del select de espacios para el formulario
    opciones_html = "".join(
        f'<option value="{e.id}">{_esc(e.nombre)} (cap. {e.capacidad})</option>'
        for e in lista_espacios
    )
    nav = _nav_html(sesion)

    return _html(render("reservas",
                         nav=nav,
                         filas=filas_html,
                         opciones_espacios=opciones_html,
                         error_block=""))


@ruta("POST", "/reservas")
def reservas_post(environ):
    sesion = _usuario_actual(environ)
    if not sesion:
        return _redir("/login")

    usuario_id, _ = sesion
    form = _leer_body(environ)
    espacio_id_str = _campo(form, "espacio_id")
    inicio = _campo(form, "inicio")
    fin = _campo(form, "fin")

    try:
        espacio_id = int(espacio_id_str)
        reservas_svc.crear_reserva(usuario_id, espacio_id, inicio, fin)
    except EspacioOcupadoError as e:
        return _reservas_error(sesion, str(e))
    except EspacioNoEncontradoError as e:
        return _reservas_error(sesion, str(e))
    except ValueError as e:
        return _reservas_error(sesion, str(e))

    return _redir("/reservas")


@ruta("POST", "/reservas/cancelar")
def reservas_cancelar(environ):
    sesion = _usuario_actual(environ)
    if not sesion:
        return _redir("/login")

    usuario_id, _ = sesion
    form = _leer_body(environ)
    reserva_id_str = _campo(form, "reserva_id")

    try:
        reserva_id = int(reserva_id_str)
        reservas_svc.cancelar_reserva(reserva_id, usuario_id)
    except ReservaNoAutorizadaError as e:
        return _reservas_error(sesion, str(e))
    except ValueError:
        return _reservas_error(sesion, "ID de reserva inválido.")

    return _redir("/reservas")


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _nav_html(sesion) -> str:
    """Genera el bloque de navegación según si hay sesión activa o no."""
    if sesion:
        return (
            '<nav>'
            '<a href="/espacios">Espacios</a> | '
            '<a href="/reservas">Mis reservas</a> | '
            '<form method="post" action="/logout" style="display:inline">'
            '<button type="submit" class="btn-nav">Cerrar sesión</button>'
            '</form>'
            '</nav>'
        )
    return (
        '<nav>'
        '<a href="/espacios">Espacios</a> | '
        '<a href="/login">Iniciar sesión</a> | '
        '<a href="/registro">Registrarse</a>'
        '</nav>'
    )


def _reservas_error(sesion, error_msg: str):
    """Vuelve a mostrar la página de reservas con un mensaje de error."""
    usuario_id, _ = sesion
    lista_reservas = reservas_svc.listar_de_usuario(usuario_id)
    lista_espacios = espacios_svc.listar_espacios()
    mapa = {e.id: e.nombre for e in lista_espacios}

    filas_html = ""
    for r in lista_reservas:
        nombre_espacio = _esc(mapa.get(r.espacio_id, f"Espacio #{r.espacio_id}"))
        boton_cancelar = ""
        if r.estado == "activa":
            boton_cancelar = (
                f'<form method="post" action="/reservas/cancelar" style="display:inline">'
                f'<input type="hidden" name="reserva_id" value="{r.id}">'
                f'<button type="submit" class="btn-cancelar"'
                f' onclick="return confirm(\'¿Cancelar?\')">Cancelar</button>'
                f'</form>'
            )
        estado_badge = (
            '<span class="badge-activa">Activa</span>' if r.estado == "activa"
            else '<span class="badge-cancelada">Cancelada</span>'
        )
        filas_html += (
            f"<tr><td>{nombre_espacio}</td><td>{_esc(r.inicio)}</td>"
            f"<td>{_esc(r.fin)}</td><td>{estado_badge}</td>"
            f"<td>{boton_cancelar}</td></tr>\n"
        )

    opciones_html = "".join(
        f'<option value="{e.id}">{_esc(e.nombre)}</option>'
        for e in lista_espacios
    )
    nav = _nav_html(sesion)
    return _html(render("reservas",
                         nav=nav,
                         filas=filas_html,
                         opciones_espacios=opciones_html,
                         error_block=_error_block(_esc(error_msg))), 400)
