import os
import sys

# Agregar la raíz del proyecto al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

# Vercel WSGI runner busca 'app'
handler = app
