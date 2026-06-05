"""
Seguridad: hashing de contraseñas con pbkdf2_hmac y firma de cookies con hmac.
Solo stdlib, sin dependencias externas.
"""
import hashlib
import hmac
import os

from app import config


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------

def hash_password(password: str) -> tuple[str, str]:
    """
    Genera un salt aleatorio y devuelve (salt_hex, hash_hex).
    Usa pbkdf2_hmac con SHA-256 y 200 000 iteraciones.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), dk.hex()


def verificar_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Compara de forma segura (timing-safe) el hash de la contraseña."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        200_000,
    )
    return hmac.compare_digest(dk.hex(), hash_hex)


# ---------------------------------------------------------------------------
# Cookies de sesión
# ---------------------------------------------------------------------------
# Formato del valor de la cookie: "<usuario_id>:<rol>:<firma_hmac_hex>"
# La firma protege contra manipulación del lado del cliente.

_SEP = ":"


def firmar_cookie(usuario_id: int, rol: str) -> str:
    """Devuelve el valor firmado para la cookie de sesión."""
    payload = f"{usuario_id}{_SEP}{rol}"
    firma = hmac.new(
        config.SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}{_SEP}{firma}"


def verificar_cookie(valor: str) -> tuple[int, str] | None:
    """
    Verifica la cookie de sesión.
    Devuelve (usuario_id, rol) si es válida, o None si fue manipulada/inexistente.
    """
    if not valor:
        return None
    partes = valor.split(_SEP, 2)
    if len(partes) != 3:
        return None
    uid_str, rol, firma_recibida = partes
    payload = f"{uid_str}{_SEP}{rol}"
    firma_esperada = hmac.new(
        config.SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(firma_esperada, firma_recibida):
        return None
    try:
        return int(uid_str), rol
    except ValueError:
        return None
