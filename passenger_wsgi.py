"""
Punto de entrada para Passenger en cPanel.
No pongas lógica aquí; solo expone el callable WSGI de la app.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.wsgi import application  # noqa: F401
