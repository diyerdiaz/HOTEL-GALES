from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, gettext as _
from flask_wtf.csrf import CSRFProtect, CSRFError
from markupsafe import escape
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)    
    app.config.from_object('config.Config')

    db.init_app(app)
    # Protección CSRF: todo formulario POST debe incluir el token de la sesión
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    def get_locale():
        if 'language' in session:
            return session['language']
        return request.accept_languages.best_match(app.config['LANGUAGES'])
    
    babel.init_app(app, locale_selector=get_locale)

    # Importar modelos
    from app.models.users import User
    from app.models.cliente import Cliente
    from app.models.rolempleado import RolEmpleado
    from app.models.empleado import Empleado
    from app.models.tipohabitacion import TipoHabitacion
    from app.models.habitacion import Habitacion
    from app.models.mantenimiento import MantenimientoHabitacion
    from app.models.tiposervicio import TipoServicio
    from app.models.servicio import Servicio
    from app.models.reserva import Reserva
    from app.models.pago import Pago
    from app.models.factura import Factura
    from app.models.consumo import Consumo
    from app.models.tarea_limpieza import TareaLimpieza
    from app.models.comentario import Comentario
    from app.models.password_reset import PasswordResetToken
    from app.models.notificacion import Notificacion

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Registrar blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.usuarios import bp as usuarios_bp
    from app.routes.clientes import bp as clientes_bp
    from app.routes.empleados import bp as empleados_bp
    from app.routes.rolempleados import bp as rolempleados_bp
    from app.routes.habitaciones import bp as habitaciones_bp
    from app.routes.tipohabitaciones import bp as tipohabitaciones_bp
    from app.routes.mantenimientos import bp as mantenimientos_bp
    from app.routes.servicios import bp as servicios_bp
    from app.routes.tiposervicios import bp as tiposervicios_bp
    from app.routes.reservas import bp as reservas_bp
    from app.routes.pagos import bp as pagos_bp
    from app.routes.facturas import bp as facturas_bp
    from app.routes.consumos import bp as consumos_bp
    from app.routes.limpieza import bp as limpieza_bp
    from app.routes.reportes import bp as reportes_bp
    from app.routes.comentarios import bp as comentarios_bp
    from app.routes.notificaciones import bp as notificaciones_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(empleados_bp)
    app.register_blueprint(rolempleados_bp)
    app.register_blueprint(habitaciones_bp)
    app.register_blueprint(tipohabitaciones_bp)
    app.register_blueprint(mantenimientos_bp)
    app.register_blueprint(servicios_bp)
    app.register_blueprint(tiposervicios_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(facturas_bp)
    app.register_blueprint(consumos_bp)
    app.register_blueprint(limpieza_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(comentarios_bp)
    app.register_blueprint(notificaciones_bp)

    # Filtro personalizado para Pesos Colombianos (COP)
    @app.template_filter('cop')
    def format_cop(value):
        try:
            return "$ {:,.0f} COP".format(value).replace(',', '.')
        except (ValueError, TypeError):
            return value

    @app.template_filter('trans')
    def trans_filter(value):
        if not value:
            return value
        normalized = str(value).replace('_', ' ').strip()
        if normalized.isupper():
            return _(normalized).upper()
        return _(normalized.title())
            
    # --- Manejo global de Errores (Evita que la app colapse) ---
    @app.errorhandler(404)
    def page_not_found(e):
        return "<h1>404 - " + _('Página no encontrada') + "</h1><p>" + _('Lo sentimos, la página que buscas no existe.') + "</p><a href='/'>" + _('Volver al inicio') + "</a>", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        return "<h1>500 - " + _('Error Interno del Servidor') + "</h1><p>" + _('Ha ocurrido un problema inesperado. Por favor, inténtalo más tarde.') + "</p><a href='/'>" + _('Volver al inicio') + "</a>", 500

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return "<h1>400 - " + _('Solicitud inválida') + "</h1><p>" + _('El formulario expiró o no es válido. Recarga la página e inténtalo de nuevo.') + "</p><a href='/'>" + _('Volver al inicio') + "</a>", 400

    @app.errorhandler(413)
    def archivo_muy_grande(e):
        return "<h1>413 - " + _('Archivo demasiado grande') + "</h1><p>" + _('Las imágenes no pueden superar los 16 MB en total.') + "</p><a href='javascript:history.back()'>" + _('Volver') + "</a>", 413

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Los errores HTTP (404, 405, 403...) conservan su código original
        if isinstance(e, HTTPException):
            return e
        db.session.rollback()
        # El detalle técnico va al registro del servidor, nunca a la página
        app.logger.exception(e)
        return "<h1>" + str(escape(_('Error Inesperado'))) + "</h1><p>" + str(escape(_('Ha ocurrido un problema inesperado. Por favor, inténtalo más tarde.'))) + "</p><a href='/'>" + str(escape(_('Volver al inicio'))) + "</a>", 500

    @app.after_request
    def cabeceras_de_seguridad(response):
        # Evita que la app se cargue dentro de un iframe de otro sitio (clickjacking)
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        # Evita que el navegador interprete archivos con un tipo distinto al declarado
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return response
        
    return app