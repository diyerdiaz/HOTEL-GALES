from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()

def create_app():
    app = Flask(__name__)    
    app.config.from_object('config.Config')

    db.init_app(app)
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

    # Filtro personalizado para Pesos Colombianos (COP)
    @app.template_filter('cop')
    def format_cop(value):
        try:
            return "$ {:,.0f} COP".format(value).replace(',', '.')
        except (ValueError, TypeError):
            return value
            
    # --- Manejo global de Errores (Evita que la app colapse) ---
    @app.errorhandler(404)
    def page_not_found(e):
        return "<h1>404 - Página no encontrada</h1><p>Lo sentimos, la página que buscas no existe.</p><a href='/'>Volver al inicio</a>", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # Aquí se maneja cualquier error interno o colapso
        db.session.rollback() # Revertimos cualquier transacción fallida
        return "<h1>500 - Error Interno del Servidor</h1><p>Ha ocurrido un problema inesperado. Por favor, inténtalo más tarde.</p><a href='/'>Volver al inicio</a>", 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Maneja cualquier otra excepción no controlada
        db.session.rollback()
        return f"<h1>Error Inesperado</h1><p>La aplicación pudo recuperarse de un error: {str(e)}</p><a href='/'>Volver al inicio</a>", 500
        
    return app