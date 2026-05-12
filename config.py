import os
import urllib.parse
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # Priorizar la URL de la base de datos del entorno
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        db_user = os.environ.get('DB_USER')
        db_pass = os.environ.get('DB_PASS')
        db_host = os.environ.get('DB_HOST')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME')
        
        if db_user and db_pass and db_host and db_name:
            # Codificar la contraseña para evitar que los caracteres especiales rompan la URL
            encoded_pass = urllib.parse.quote_plus(db_pass)
            db_url = f"postgresql://{db_user}:{encoded_pass}@{db_host}:{db_port}/{db_name}"
        else:
            import os
            basedir = os.path.abspath(os.path.dirname(__file__))
            db_url = 'sqlite:///' + os.path.join(basedir, 'instance', 'flaskdb.sqlite')
            
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # La SECRET_KEY es vital para la seguridad de las sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-por-defecto-insegura'

    # Configuración de Idiomas (Babel)
    LANGUAGES = ['es', 'en']
    BABEL_DEFAULT_LOCALE = 'es'

    # Credenciales de Administrador (desde .env)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123456'
