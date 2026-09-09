import os
import sys

# Agregar la raíz del proyecto al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, VercelPathMiddleware

# Envolver la aplicación WSGI con el middleware de rutas de Vercel
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Exportar handler y app para Vercel Serverless
handler = app
