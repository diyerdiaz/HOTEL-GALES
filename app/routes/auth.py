from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.users import User
from app.utils.roles import ROLES
from app.utils.decorators import requiere_admin

bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    """Ruta para iniciar sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.menu'))
    
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        # Validar campos vacíos
        if not usuario or not password:
            flash('Por favor completa todos los campos', 'error')
            return redirect(url_for('auth.login'))
        
        # Buscar usuario
        user = User.query.filter_by(usuario=usuario).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Bienvenido {usuario}!', 'success')
            return redirect(url_for('auth.menu'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta para crear cuenta - Público para clientes"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.menu'))
    
    if request.method == 'POST':
        cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validar campos
        if not all([cedula, nombre, apellido, email, telefono, usuario, password, confirm_password]):
            flash('Por favor completa todos los campos', 'error')
            return redirect(url_for('auth.register'))
        
        if len(usuario) < 3:
            flash('El usuario debe tener al menos 3 caracteres', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.register'))
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(usuario=usuario).first():
            flash('El nombre de usuario ya está en uso', 'error')
            return redirect(url_for('auth.register'))
            
        from app.models.cliente import Cliente
        if Cliente.query.get(cedula):
            flash('Esta cédula ya está registrada', 'error')
            return redirect(url_for('auth.register'))
        
        try:
            # 1. Crear el perfil de Cliente
            nuevo_cliente = Cliente(
                cedula=cedula,
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono
            )
            db.session.add(nuevo_cliente)
            
            # 2. Crear el Usuario vinculado a esa cédula
            nuevo_usuario = User(
                usuario=usuario,
                password=generate_password_hash(password),
                rol='cliente',
                cedula=cedula
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('¡Bienvenido! Cuenta creada con éxito. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error técnico al crear la cuenta', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@bp.route('/menu')
@login_required
def menu():
    """Ruta del menú principal (después de autenticarse)"""
    from app.models.reserva import Reserva
    from app.models.habitacion import Habitacion
    
    # Datos para las gráficas (solo para staff)
    datos_graficas = {}
    if current_user.rol != 'cliente':
        # Estadísticas de Habitaciones
        habitaciones = Habitacion.query.all()
        datos_graficas['habitaciones'] = {
            'disponible': sum(1 for h in habitaciones if h.estadoHabitacion == 'disponible'),
            'ocupada': sum(1 for h in habitaciones if h.estadoHabitacion == 'ocupada'),
            'mantenimiento': sum(1 for h in habitaciones if h.estadoHabitacion == 'mantenimiento')
        }
        
        # Estadísticas de Reservas
        reservas = Reserva.query.all()
        datos_graficas['reservas'] = {
            'pendiente': sum(1 for r in reservas if r.estadoReserva == 'pendiente'),
            'en curso': sum(1 for r in reservas if r.estadoReserva == 'en curso'),
            'finalizada': sum(1 for r in reservas if r.estadoReserva == 'finalizada'),
            'cancelada': sum(1 for r in reservas if r.estadoReserva == 'cancelada')
        }

    return render_template('dashboard/menu.html', datos_graficas=datos_graficas)

@bp.route('/logout')
@login_required
def logout():
    """Ruta para cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Ruta para ver y actualizar el perfil del usuario"""
    from app.models.cliente import Cliente
    cliente = None
    if current_user.cedula:
        cliente = Cliente.query.get(current_user.cedula)

    if request.method == 'POST':
        # Actualizar datos de usuario
        nuevo_usuario = request.form.get('usuario')
        password = request.form.get('password')
        confirmar = request.form.get('confirm_password')

        # Si el usuario quiere cambiar de nombre de usuario
        if nuevo_usuario and nuevo_usuario != current_user.usuario:
            if User.query.filter_by(usuario=nuevo_usuario).first():
                flash('El nombre de usuario ya está en uso', 'error')
                return redirect(url_for('auth.perfil'))
            current_user.usuario = nuevo_usuario

        # Cambio de contraseña
        if password:
            if password != confirmar:
                flash('Las contraseñas no coinciden', 'error')
                return redirect(url_for('auth.perfil'))
            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return redirect(url_for('auth.perfil'))
            current_user.password = generate_password_hash(password)

        # Actualizar datos de cliente (si existen)
        if cliente:
            cliente.nombre = request.form.get('nombre', cliente.nombre)
            cliente.apellido = request.form.get('apellido', cliente.apellido)
            cliente.email = request.form.get('email', cliente.email)
            cliente.telefono = request.form.get('telefono', cliente.telefono)
            cliente.direccion = request.form.get('direccion', cliente.direccion)

        try:
            db.session.commit()
            flash('Perfil actualizado con éxito', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el perfil', 'error')
        
        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html', user=current_user, cliente=cliente)

@bp.route('/perfil/eliminar', methods=['POST'])
@login_required
def eliminar_cuenta():
    """Ruta para eliminar la cuenta propia"""
    user = User.query.get(current_user.id)
    try:
        logout_user() # Cerrar sesión antes de borrar
        db.session.delete(user)
        db.session.commit()
        flash('Tu cuenta ha sido eliminada. Lamentamos verte partir.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('No se pudo eliminar la cuenta', 'error')
        return redirect(url_for('auth.perfil'))
    
    return redirect(url_for('auth.login'))

@bp.route('/set_language/<lang>')
def set_language(lang):
    """Cambiar el idioma de la sesión"""
    from flask import session, current_app
    if lang in current_app.config['LANGUAGES']:
        session['language'] = lang
    return redirect(request.referrer or url_for('auth.menu'))
