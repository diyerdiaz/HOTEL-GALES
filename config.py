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

    # Correo saliente (SMTP). Si MAIL_SERVER está vacío no se envían correos.
    # Ejemplo Gmail: MAIL_SERVER=smtp.gmail.com, MAIL_PORT=587, MAIL_USE_TLS=true y una
    # "contraseña de aplicación" en MAIL_PASSWORD (no la contraseña normal de la cuenta).
    MAIL_SERVER = os.environ.get('MAIL_SERVER', '')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_SENDER = os.environ.get('MAIL_SENDER') or MAIL_USERNAME or 'no-reply@hotelgales.local'
    MAIL_SENDER_NAME = os.environ.get('MAIL_SENDER_NAME', 'Hotel Gales')
    MAIL_TIMEOUT = int(os.environ.get('MAIL_TIMEOUT', '15'))

    # Dirección pública del sitio para los enlaces de los correos (ej: https://hotelgales.com).
    # Si se deja vacía se usa la dirección con la que se hizo la solicitud.
    URL_PUBLICA = os.environ.get('URL_PUBLICA', '').rstrip('/')

    # Solo en desarrollo: mostrar en pantalla el token de recuperación de contraseña.
    # En producción debe ser false, o cualquiera que conozca un correo podría cambiar su contraseña.
    MOSTRAR_TOKEN_RECUPERACION = os.environ.get('MOSTRAR_TOKEN_RECUPERACION', 'false').lower() == 'true'

    # Configuración de Idiomas (Babel)
    LANGUAGES = ['es', 'en']
    BABEL_DEFAULT_LOCALE = 'es'

    # Credenciales de Administrador (desde .env)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'hotelgales#'

