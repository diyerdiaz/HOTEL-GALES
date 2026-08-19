from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import re
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
        
        # Limpiar espacios en blanco al inicio y final
        cedula = cedula.strip() if cedula else ''
        nombre = nombre.strip() if nombre else ''
        apellido = apellido.strip() if apellido else ''
        email = email.strip().lower() if email else ''
        telefono = telefono.strip() if telefono else ''
        usuario = usuario.strip() if usuario else ''

        # Validar campos vacíos
        if not all([cedula, nombre, apellido, email, telefono, usuario, password, confirm_password]):
            flash('Por favor completa todos los campos', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar cédula / ID (solo números, de 5 a 15 dígitos)
        if not cedula.isdigit() or not (5 <= len(cedula) <= 15):
            flash('La cédula o ID debe contener únicamente dígitos numéricos y tener entre 5 y 15 dígitos.', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar email (cualquier dominio válido, no solo gmail.com)
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            flash('Por favor ingresa un correo electrónico válido.', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar nombre y apellido (solo letras, máx 30 caracteres)
        if not re.match(r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]{1,30}$", nombre) or not re.match(r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]{1,30}$", apellido):
            flash('El nombre y apellido deben contener solo letras y máximo 30 caracteres', 'error')
            return redirect(url_for('auth.register'))

        # Validar teléfono (entre 7 y 15 dígitos numéricos, opcionalmente con + inicial)
        if not re.match(r"^\+?\d{7,15}$", telefono):
            flash('El teléfono debe tener entre 7 y 15 dígitos numéricos (puede empezar con +)', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar usuario (entre 4 y 20 caracteres, letras, números, puntos, guiones y guiones bajos)
        if not re.match(r"^[a-zA-Z0-9._\-]{4,20}$", usuario):
            flash('El nombre de usuario debe tener entre 4 y 20 caracteres y solo contener letras, números, puntos, guiones o guiones bajos.', 'error')
            return redirect(url_for('auth.register'))
        
        # Validar contraseña (entre 8 y 30 caracteres, al menos una letra y un número)
        if len(password) < 8 or len(password) > 30:
            flash('La contraseña debe tener entre 8 y 30 caracteres', 'error')
            return redirect(url_for('auth.register'))
        
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash('La contraseña debe contener al menos una letra y un número', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.register'))
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(usuario=usuario).first():
            flash('El nombre de usuario ya está en uso', 'error')
            return redirect(url_for('auth.register'))
            
        from app.models.cliente import Cliente
        
        # Verificar si la cédula ya existe
        if Cliente.query.get(cedula):
            flash('Esta cédula ya está registrada', 'error')
            return redirect(url_for('auth.register'))

        # Verificar si el correo electrónico ya existe
        if Cliente.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado', 'error')
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
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning(f"Error de integridad al registrar usuario: {str(e)}")
            flash('La cédula, el correo o el nombre de usuario ya están registrados.', 'error')
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error técnico al registrar usuario: {str(e)}")
            flash('Ocurrió un error técnico al crear la cuenta. Por favor intente más tarde.', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@bp.route('/menu')
@login_required
def menu():
    """Ruta del menú principal (después de autenticarse)"""
    from app.models.reserva import Reserva
    from app.models.habitacion import Habitacion
    from app.models.comentario import Comentario
    
    # Datos para el dashboard de clientes
    datos_cliente = {}
    if current_user.rol == 'cliente':
        # Reserva actual del cliente
        reserva_actual = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula,
            Reserva.estadoReserva.in_(['pendiente', 'confirmada'])
        ).first()
        
        # Historial de reservas del cliente
        historial_reservas = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula
        ).order_by(Reserva.idReserva.desc()).limit(5).all()
        
        # Comentarios del cliente
        comentarios_cliente = Comentario.query.filter(
            Comentario.cedulaCliente == current_user.cedula
        ).order_by(Comentario.fechaComentario.desc()).limit(3).all()
        
        # Estadísticas del cliente
        total_reservas = Reserva.query.filter_by(cedulaCliente=current_user.cedula).count()
        reservas_finalizadas = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula,
            Reserva.estadoReserva == 'finalizada'
        ).count()
        reservas_canceladas = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula,
            Reserva.estadoReserva == 'cancelada'
        ).count()
        
        datos_cliente = {
            'reserva_actual': reserva_actual,
            'historial_reservas': historial_reservas,
            'comentarios': comentarios_cliente,
            'total_reservas': total_reservas,
            'reservas_finalizadas': reservas_finalizadas,
            'reservas_canceladas': reservas_canceladas
        }
    
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

    return render_template('dashboard/menu.html', datos_graficas=datos_graficas, datos_cliente=datos_cliente)

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
            if len(password) < 8 or len(password) > 30:
                flash('La contraseña debe tener entre 8 y 30 caracteres', 'error')
                return redirect(url_for('auth.perfil'))
            if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
                flash('La contraseña debe contener al menos una letra y un número', 'error')
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
    return redirect(request.referrer or url_for('auth.login'))

@bp.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    """Solicitar recuperación de contraseña"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.menu'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Por favor ingresa tu correo electrónico', 'error')
            return redirect(url_for('auth.recuperar_contrasena'))
        
        # Buscar usuario por email a través del cliente
        from app.models.cliente import Cliente
        cliente = Cliente.query.filter_by(email=email.lower()).first()
        
        if cliente:
            user = User.query.filter_by(cedula=cliente.cedula).first()
            if user:
                # Generar token de recuperación
                from app.models.password_reset import PasswordResetToken
                token = PasswordResetToken.generate_token(user.id)
                
                # En desarrollo, mostrar el token en pantalla
                # En producción, aquí se enviaría el email
                flash(f'Token de recuperación (desarrollo): {token}', 'info')
                flash('Se ha enviado un correo con instrucciones para recuperar tu contraseña', 'success')
                return redirect(url_for('auth.restablecer_contrasena', token=token))
        
        # Por seguridad, siempre mostrar el mismo mensaje incluso si el email no existe
        flash('Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_contrasena.html')

@bp.route('/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    """Restablecer contraseña con token"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.menu'))
    
    from app.models.password_reset import PasswordResetToken
    reset_token = PasswordResetToken.verify_token(token)
    
    if not reset_token:
        flash('El enlace de recuperación es inválido o ha expirado', 'error')
        return redirect(url_for('auth.recuperar_contrasena'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Por favor completa todos los campos', 'error')
            return redirect(url_for('auth.restablecer_contrasena', token=token))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.restablecer_contrasena', token=token))
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'error')
            return redirect(url_for('auth.restablecer_contrasena', token=token))
        
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash('La contraseña debe contener al menos una letra y un número', 'error')
            return redirect(url_for('auth.restablecer_contrasena', token=token))
        
        # Actualizar contraseña
        user = reset_token.user
        user.password = generate_password_hash(password)
        
        # Marcar token como usado
        reset_token.mark_as_used()
        
        db.session.commit()
        
        flash('¡Contraseña actualizada con éxito! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/restablecer_contrasena.html', token=token)

@bp.route('/simular_rol/<nuevo_role>')
@login_required
def simular_rol(nuevo_role):
    """Permite a un administrador simular el rol de otro tipo de usuario."""
    if not current_user.es_admin_real():
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('auth.menu'))
    
    from flask import session
    from app.utils.roles import ROLES
    
    if nuevo_role == 'restaurar' or nuevo_role == 'administrador':
        session.pop('simulated_role', None)
        flash('Rol original de Administrador restaurado', 'success')
    elif nuevo_role in ROLES:
        session['simulated_role'] = nuevo_role
        flash(f'Simulando rol de: {nuevo_role.title()}', 'success')
    else:
        flash('Rol no válido', 'error')
        
    return redirect(url_for('auth.menu'))

