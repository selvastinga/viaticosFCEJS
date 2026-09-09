import os
import sys

# Agregar la raíz del proyecto al sys.path para importaciones en Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Exportar la app para el entorno serverless de Vercel
app_handler = app
