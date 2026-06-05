"""Estructuras de datos del módulo espacios."""
from dataclasses import dataclass


@dataclass
class Espacio:
    id: int | None
    nombre: str
    descripcion: str
    capacidad: int
