"""
Rutas para gestionar usuarios - Solo administrador
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_babel import gettext as _
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import re
from app import db
from app.models.users import User
from app.utils.roles import ROLES, rol_label
from app.utils.decorators import requiere_admin

bp = Blueprint('usuarios', __name__, url_prefix='/admin')

@bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def listar_usuarios():
    """Lista todos los usuarios y permite crear nuevos"""
    
    # Solo admin y recepcionista pueden acceder
    if current_user.rol not in ['administrador', 'recepcionista']:
        flash(_('No tienes permiso para acceder a esta sección'), 'error')
        return redirect(url_for('auth.menu'))

    if request.method == 'POST':
        # Crear nuevo usuario
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        rol = request.form.get('rol', 'cliente')
        origen = request.form.get('origen', 'usuarios')
        
        # Datos personales
        cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        # Redirigir de vuelta a la página desde la que se envió el formulario
        redir_target = url_for('empleados.index') if origen == 'empleados' else url_for('usuarios.listar_usuarios')

        # La página de usuarios solo permite crear clientes
        if rol != 'cliente' and origen == 'usuarios':
            flash(_('En esta sección solo se pueden crear clientes.'), 'error')
            return redirect(redir_target)
        # Solo el administrador puede crear personal (no clientes)
        if rol != 'cliente' and current_user.rol != 'administrador':
            flash(_('No tienes permiso para crear personal.'), 'error')
            return redirect(redir_target)

        # Validar campos
        if not usuario or not password or not confirm_password or not cedula or not nombre or not apellido:
            flash(_('Por favor completa todos los campos obligatorios (Usuario, Contraseña, Cédula, Nombre, Apellido)'), 'error')
            return redirect(redir_target)
        
        # Limpiar espacios en blanco
        cedula = cedula.strip() if cedula else ''
        nombre = nombre.strip() if nombre else ''
        apellido = apellido.strip() if apellido else ''
        email = email.strip().lower() if email else ''
        telefono = telefono.strip() if telefono else ''
        usuario = usuario.strip() if usuario else ''

        # Validar cédula / ID (solo números, de 5 a 15 dígitos)
        if not cedula.isdigit() or not (5 <= len(cedula) <= 15):
            flash(_('La cédula o ID debe contener únicamente dígitos numéricos y tener entre 5 y 15 dígitos.'), 'error')
            return redirect(redir_target)

        # Validar email si se proporciona
        if email:
            if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
                flash(_('Por favor ingresa un correo electrónico válido.'), 'error')
                return redirect(redir_target)
            
            # Verificar si el correo ya está registrado en Cliente
            from app.models.cliente import Cliente
            if Cliente.query.filter_by(email=email).first():
                flash(_('El correo electrónico ya está registrado'), 'error')
                return redirect(redir_target)

        # Validar teléfono si se proporciona
        if telefono:
            if not re.match(r"^\+?\d{7,15}$", telefono):
                flash(_('El teléfono debe tener entre 7 y 15 dígitos numéricos (puede empezar con +)'), 'error')
                return redirect(redir_target)
        
        # Validar usuario (entre 4 y 20 caracteres)
        if not re.match(r"^[a-zA-Z0-9._\-]{4,20}$", usuario):
            flash(_('El nombre de usuario debe tener entre 4 y 20 caracteres y solo contener letras, números, puntos, guiones o guiones bajos.'), 'error')
            return redirect(redir_target)
        
        # Validar contraseña (entre 8 y 30 caracteres, al menos una letra y un número)
        if len(password) < 8 or len(password) > 30:
            flash(_('La contraseña debe tener entre 8 y 30 caracteres'), 'error')
            return redirect(redir_target)
        
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash(_('La contraseña debe contener al menos una letra y un número'), 'error')
            return redirect(redir_target)
        
        if password != confirm_password:
            flash(_('Las contraseñas no coinciden'), 'error')
            return redirect(redir_target)
        
        # Validar que el rol sea válido
        if rol not in ROLES:
            flash(_('Rol inválido'), 'error')
            return redirect(redir_target)
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(usuario=usuario).first():
            flash(_('El usuario ya existe'), 'error')
            return redirect(redir_target)
        
        # Gestionar datos personales (Cliente/Staff)
        from app.models.cliente import Cliente
        cliente = Cliente.query.get(cedula)
        if not cliente:
            cliente = Cliente(
                cedula=cedula,
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                direccion=direccion
            )
            db.session.add(cliente)
        
        # Crear nuevo usuario con rol y cedula
        nuevo_usuario = User(
            usuario=usuario,
            password=generate_password_hash(password),
            rol=rol,
            cedula=cedula
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(_('Usuario %(usuario)s creado exitosamente como %(rol)s') % {'usuario': usuario, 'rol': rol_label(rol)}, 'success')
            return redirect(redir_target)
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.warning(f"Error de integridad al crear usuario admin: {str(e)}")
            flash(_('La cédula, el correo o el nombre de usuario ya están registrados.'), 'error')
            return redirect(redir_target)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error técnico al crear usuario admin: {str(e)}")
            flash(_('Error al crear el usuario'), 'error')
            return redirect(redir_target)
    
    # GET: Mostrar solo clientes (los empleados se gestionan en la sección Empleados)
    usuarios = User.query.filter_by(rol='cliente').all()

    from app.models.cliente import Cliente
    clientes = {c.cedula: c for c in Cliente.query.all()}
    
    return render_template('dashboard/usuarios.html', usuarios=usuarios, roles=ROLES, clientes=clientes)

@bp.route('/editar-usuario/<int:id>', methods=['POST'])
@login_required
def editar_usuario(id):
    redir_target = url_for('empleados.index') if request.form.get('origen') == 'empleados' else url_for('usuarios.listar_usuarios')
    if current_user.rol != 'administrador':
        flash(_('Solo el administrador puede editar roles.'), 'error')
        return redirect(redir_target)
        
    usuario = User.query.get_or_404(id)
    nuevo_rol = request.form.get('rol')
    
    if nuevo_rol in ROLES:
        usuario.rol = nuevo_rol
        db.session.commit()
        flash(_('Rol de %(usuario)s actualizado a %(rol)s.') % {'usuario': usuario.usuario, 'rol': rol_label(nuevo_rol)}, 'success')
    else:
        flash(_('Rol inválido.'), 'error')
        
    return redirect(redir_target)

@bp.route('/eliminar-usuario/<int:id>', methods=['POST'])
@login_required
def eliminar_usuario(id):
    redir_target = url_for('empleados.index') if request.form.get('origen') == 'empleados' else url_for('usuarios.listar_usuarios')
    if current_user.rol != 'administrador':
        flash(_('Solo el administrador puede eliminar usuarios.'), 'error')
        return redirect(redir_target)
        
    usuario = User.query.get_or_404(id)

    if usuario.id == current_user.id:
        flash(_('No puedes eliminarte a ti mismo.'), 'error')
    else:
        cedula = usuario.cedula
        nombre_usuario = usuario.usuario
        db.session.delete(usuario)
        db.session.commit()

        # Si el cliente asociado no tiene reservas ni otras cuentas vinculadas,
        # se elimina también su ficha para que no quede huérfana en Gestión de Clientes.
        if cedula:
            from app.models.cliente import Cliente
            from app.models.reserva import Reserva
            tiene_reservas = Reserva.query.filter_by(cedulaCliente=cedula).first() is not None
            otra_cuenta_vinculada = User.query.filter_by(cedula=cedula).first() is not None
            if not tiene_reservas and not otra_cuenta_vinculada:
                cliente = Cliente.query.get(cedula)
                if cliente:
                    db.session.delete(cliente)
                    db.session.commit()

        flash(_('Usuario %(usuario)s eliminado exitosamente.') % {'usuario': nombre_usuario}, 'success')

    return redirect(redir_target)

@bp.route('/recepcionistas')
@login_required
@requiere_admin
def historial_recepcionistas():
    """Muestra una lista de recepcionistas y un resumen de su actividad"""
    from flask import request
    from app.models.reserva import Reserva
    from datetime import datetime
    
    query = User.query.filter_by(rol='recepcionista')
    
    search = request.args.get('search', '')
    if search:
        query = query.filter(User.usuario.ilike(f'%{search}%'))
        
    fecha = request.args.get('fecha', '')
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            query = query.join(Reserva, User.id == Reserva.recepcionista_id).filter(Reserva.fechaEntrada == fecha_dt).distinct()
        except ValueError:
            pass
            
    recepcionistas = query.all()
    
    # Obtener información de cliente vinculada para cada uno
    from app.models.cliente import Cliente
    info_personal = {c.cedula: c for c in Cliente.query.all()}
    
    return render_template('dashboard/recepcionistas.html', 
                         recepcionistas=recepcionistas, 
                         info_personal=info_personal,
                         search=search,
                         fecha=fecha)

@bp.route('/recepcionista/<int:id>/historial')
@login_required
@requiere_admin
def ver_historial_recepcionista(id):
    """Muestra el historial detallado de un recepcionista específico"""
    recepcionista = User.query.get_or_404(id)
    if recepcionista.rol != 'recepcionista':
        flash(_('El usuario seleccionado no es un recepcionista.'), 'error')
        return redirect(url_for('usuarios.historial_recepcionistas'))
    
    # Reservas atendidas por este recepcionista
    from app.models.reserva import Reserva
    historial = Reserva.query.filter_by(recepcionista_id=id).order_by(Reserva.fechaEntrada.desc()).all()
    
    from app.models.cliente import Cliente
    cliente_info = Cliente.query.get(recepcionista.cedula) if recepcionista.cedula else None
    
    return render_template('dashboard/historial_recepcionista.html', 
                         recepcionista=recepcionista, 
                         historial=historial,
                         cliente_info=cliente_info)
@bp.route('/personal-limpieza')
@login_required
@requiere_admin
def historial_limpieza():
    """Muestra una lista del personal de limpieza y su actividad"""
    from flask import request
    from app.models.tarea_limpieza import TareaLimpieza
    from datetime import datetime
    
    query = User.query.filter_by(rol='servicio_limpieza')
    
    search = request.args.get('search', '')
    if search:
        query = query.filter(User.usuario.ilike(f'%{search}%'))
        
    fecha = request.args.get('fecha', '')
    if fecha:
        try:
            # En tareas de limpieza usamos fechaAsignacion
            # fechaAsignacion es DateTime, filtramos por el día
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            query = query.join(TareaLimpieza, User.id == TareaLimpieza.idPersonal)\
                         .filter(db.func.date(TareaLimpieza.fechaAsignacion) == fecha_dt).distinct()
        except ValueError:
            pass
            
    personal = query.all()
    
    # Obtener información de cliente vinculada
    from app.models.cliente import Cliente
    info_personal = {c.cedula: c for c in Cliente.query.all()}
    
    return render_template('dashboard/personal_limpieza.html', 
                         personal=personal, 
                         info_personal=info_personal,
                         search=search,
                         fecha=fecha)

@bp.route('/personal-limpieza/<int:id>/historial')
@login_required
@requiere_admin
def ver_historial_limpieza(id):
    """Muestra el historial detallado de un empleado de limpieza"""
    empleado = User.query.get_or_404(id)
    if empleado.rol != 'servicio_limpieza':
        flash(_('El usuario seleccionado no pertenece al personal de limpieza.'), 'error')
        return redirect(url_for('usuarios.historial_limpieza'))
    
    # Tareas realizadas por este empleado
    from app.models.tarea_limpieza import TareaLimpieza
    historial = TareaLimpieza.query.filter_by(idPersonal=id).order_by(TareaLimpieza.fechaAsignacion.desc()).all()
    
    from app.models.cliente import Cliente
    cliente_info = Cliente.query.get(empleado.cedula) if empleado.cedula else None
    
    return render_template('dashboard/historial_limpieza_detalle.html', 
                         empleado=empleado, 
                         historial=historial,
                         cliente_info=cliente_info)
