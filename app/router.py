"""
Router WSGI minimalista.
Mapea (método HTTP, path) → handler callable.
Los handlers devuelven (status_int, content_type, body_bytes, extra_headers_list).
"""

# Registro global de rutas: (METHOD, path) -> handler
RUTAS: dict = {}


def ruta(metodo: str, path: str):
    """
    Decorador para registrar un handler en el router.
    Uso:
        @ruta("GET", "/espacios")
        def ver_espacios(environ): ...
    """
    def decorador(fn):
        RUTAS[(metodo.upper(), path)] = fn
        return fn
    return decorador


def despachar(environ: dict):
    """
    Busca el handler para (REQUEST_METHOD, PATH_INFO).
    Devuelve el resultado del handler o una tupla 404 si no existe ruta.
    """
    # PATH_INFO puede venir vacío (p. ej. al ejecutarse como DirectoryIndex en
    # la raíz vía CGI); en ese caso se normaliza a "/" según el estándar WSGI.
    metodo = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO") or "/"
    clave = (metodo, path)
    handler = RUTAS.get(clave)
    if handler is None:
        return (404, "text/plain; charset=utf-8", b"404 No encontrado", [])
    return handler(environ)
