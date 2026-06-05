"""Estructuras de datos del módulo reservas."""
from dataclasses import dataclass


@dataclass
class Reserva:
    id: int | None
    usuario_id: int
    espacio_id: int
    inicio: str   # formato ISO: 'YYYY-MM-DD HH:MM'
    fin: str      # formato ISO: 'YYYY-MM-DD HH:MM'
    estado: str   # 'activa' | 'cancelada'
