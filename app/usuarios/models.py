"""Estructuras de datos del módulo usuarios."""
from dataclasses import dataclass


@dataclass
class Usuario:
    id: int | None
    nombre: str
    email: str
    salt: str
    password_hash: str
    rol: str  # 'admin' | 'usuario'
