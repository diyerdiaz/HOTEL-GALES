import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # Priorizar la URL de la base de datos del entorno, si no cargar sqlite local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///flaskdb.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # La SECRET_KEY es vital para la seguridad de las sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-por-defecto-insegura'

    # Configuración de Idiomas (Babel)
    LANGUAGES = ['es', 'en']
    BABEL_DEFAULT_LOCALE = 'es'

    # Credenciales de Administrador (desde .env)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123456'
