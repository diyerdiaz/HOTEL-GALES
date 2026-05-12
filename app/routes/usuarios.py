"""
Rutas para gestionar usuarios - Solo administrador
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models.users import User
from app.utils.roles import ROLES
from app.utils.decorators import requiere_admin

bp = Blueprint('usuarios', __name__, url_prefix='/admin')

@bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def listar_usuarios():
    """Lista todos los usuarios y permite crear nuevos"""
    
    # Solo admin y recepcionista pueden acceder
    if current_user.rol not in ['administrador', 'recepcionista']:
        flash('No tienes permiso para acceder a esta sección', 'error')
        return redirect(url_for('auth.menu'))

    if request.method == 'POST':
        # Crear nuevo usuario
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        rol = request.form.get('rol', 'cliente')
        
        # Datos personales
        cedula = request.form.get('cedula')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        # Restricción: Recepcionista solo puede crear servicio_limpieza
        if current_user.rol == 'recepcionista' and rol != 'servicio_limpieza':
            flash('Como recepcionista solo puedes crear personal de limpieza.', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        # Validar campos
        if not usuario or not password or not confirm_password or not cedula or not nombre or not apellido:
            flash('Por favor completa todos los campos obligatorios (Usuario, Contraseña, Cédula, Nombre, Apellido)', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
        # Validaciones de longitud
        if len(str(cedula)) > 11:
            flash('La cédula no puede tener más de 11 dígitos', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        if len(nombre) > 40:
            flash('El nombre no puede tener más de 40 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        if len(apellido) > 40:
            flash('El apellido no puede tener más de 40 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        if email and len(email) > 60:
            flash('El email no puede tener más de 60 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        if telefono and len(telefono) > 11:
            flash('El teléfono no puede tener más de 11 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))

        if len(usuario) < 3 or len(usuario) > 40:
            flash('El usuario debe tener entre 3 y 40 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
        if len(password) < 6 or len(password) > 40:
            flash('La contraseña debe tener entre 6 y 40 caracteres', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
        # Validar que el rol sea válido
        if rol not in ROLES:
            flash('Rol inválido', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(usuario=usuario).first():
            flash('El usuario ya existe', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
        
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
            flash(f'Usuario {usuario} creado exitosamente como {rol}', 'success')
            return redirect(url_for('usuarios.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el usuario', 'error')
            return redirect(url_for('usuarios.listar_usuarios'))
    
    # GET: Mostrar lista de usuarios (Dependiendo del rol)
    if current_user.rol == 'administrador':
        # El admin ve TODOS los usuarios de cualquier rol
        usuarios = User.query.all()
    else:
        # Otros (ej. recepcionista) solo ven clientes
        usuarios = User.query.filter_by(rol='cliente').all()

    from app.models.cliente import Cliente
    clientes = {c.cedula: c for c in Cliente.query.all()}
    
    return render_template('dashboard/usuarios.html', usuarios=usuarios, roles=ROLES, clientes=clientes)

@bp.route('/editar-usuario/<int:id>', methods=['POST'])
@login_required
def editar_usuario(id):
    if current_user.rol != 'administrador':
        flash('Solo el administrador puede editar roles.', 'error')
        return redirect(url_for('usuarios.listar_usuarios'))
        
    usuario = User.query.get_or_404(id)
    nuevo_rol = request.form.get('rol')
    
    if nuevo_rol in ROLES:
        usuario.rol = nuevo_rol
        db.session.commit()
        flash(f'Rol de {usuario.usuario} actualizado a {nuevo_rol}.', 'success')
    else:
        flash('Rol inválido.', 'error')
        
    return redirect(url_for('usuarios.listar_usuarios'))

@bp.route('/eliminar-usuario/<int:id>', methods=['POST'])
@login_required
def eliminar_usuario(id):
    if current_user.rol != 'administrador':
        flash('Solo el administrador puede eliminar usuarios.', 'error')
        return redirect(url_for('usuarios.listar_usuarios'))
        
    usuario = User.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'error')
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuario {usuario.usuario} eliminado exitosamente.', 'success')
        
    return redirect(url_for('usuarios.listar_usuarios'))

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
            query = query.join(Reserva, User.id == Reserva.atendido_por).filter(Reserva.fechaEntrada == fecha_dt).distinct()
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
        flash('El usuario seleccionado no es un recepcionista.', 'error')
        return redirect(url_for('usuarios.historial_recepcionistas'))
    
    # Reservas atendidas por este recepcionista
    from app.models.reserva import Reserva
    historial = Reserva.query.filter_by(atendido_por=id).order_by(Reserva.fechaEntrada.desc()).all()
    
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
        flash('El usuario seleccionado no pertenece al personal de limpieza.', 'error')
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
