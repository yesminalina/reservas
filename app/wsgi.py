"""
Callable WSGI principal.
Traduce la tupla (status, content_type, body, headers) de los handlers
a la interfaz estándar WSGI.
Importa las vistas para que los handlers queden registrados en el router.
"""
import traceback

from app.router import despachar
import app.presentacion.views  # noqa: F401 — registra todos los handlers


def application(environ, start_response):
    """Callable WSGI compatible con Passenger y wsgiref."""
    try:
        resultado = despachar(environ)
        if isinstance(resultado, tuple) and len(resultado) == 4:
            status_code, content_type, body, extra_headers = resultado
        else:
            # Fallback defensivo
            status_code, content_type, body, extra_headers = 500, "text/plain", b"Error interno", []

        if isinstance(body, str):
            body = body.encode("utf-8")

        status_str = f"{status_code} {'OK' if status_code == 200 else _STATUS_TEXTS.get(status_code, 'Error')}"
        headers = [("Content-Type", content_type)] + (extra_headers or [])
        start_response(status_str, headers)
        return [body]

    except Exception:
        tb = traceback.format_exc()
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [f"500 Error interno\n\n{tb}".encode("utf-8")]


_STATUS_TEXTS = {
    200: "OK",
    201: "Created",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
}
