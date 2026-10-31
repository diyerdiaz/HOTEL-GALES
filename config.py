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
            db_url = f"postgresql+psycopg2://{db_user}:{encoded_pass}@{db_host}:{db_port}/{db_name}"

        else:
            import os
            basedir = os.path.abspath(os.path.dirname(__file__))
            instance_path = os.path.join(basedir, 'instance')
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
            db_url = 'sqlite:///' + os.path.join(instance_path, 'flaskdb.sqlite')
            
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # La SECRET_KEY es vital para la seguridad de las sesiones.
    # Si no está definida se genera una aleatoria (las sesiones se cierran al reiniciar),
    # nunca una clave fija conocida con la que se podrían falsificar sesiones.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print("[!] SECRET_KEY no está definida: se usará una clave temporal. Defínela en .env", flush=True)

    # Cookies de sesión protegidas contra robo por JavaScript y envío desde otros sitios
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    # Activar en producción con HTTPS (COOKIE_SECURE=true en .env)
    SESSION_COOKIE_SECURE = os.environ.get('COOKIE_SECURE', 'false').lower() == 'true'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # Tamaño máximo de una petición (3 imágenes de habitación + formulario)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Solo en desarrollo: mostrar en pantalla el token de recuperación de contraseña.
    # En producción debe ser false, o cualquiera que conozca un correo podría cambiar su contraseña.
    MOSTRAR_TOKEN_RECUPERACION = os.environ.get('MOSTRAR_TOKEN_RECUPERACION', 'false').lower() == 'true'

    # Configuración de Idiomas (Babel)
    LANGUAGES = ['es', 'en']
    BABEL_DEFAULT_LOCALE = 'es'

    # Credenciales de Administrador (desde .env)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'hotelgales#'

