from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.rolempleado import RolEmpleado
from app.utils.decorators import requiere_admin

bp = Blueprint('rolempleados', __name__, url_prefix='/admin/roles-empleados')

@bp.route('/')
@login_required
@requiere_admin
def index():
    roles = RolEmpleado.query.all()
    return render_template('rolempleados/index.html', roles=roles)

@bp.route('/crear', methods=['POST'])
@login_required
@requiere_admin
def crear():
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    
    if not nombre:
        flash('El nombre del rol es obligatorio.', 'danger')
        return redirect(url_for('rolempleados.index'))
    
    nuevo_rol = RolEmpleado(nombreRol=nombre, descripcionRol=descripcion)
    db.session.add(nuevo_rol)
    db.session.commit()
    flash(f'Rol "{nombre}" creado exitosamente.', 'success')
    return redirect(url_for('rolempleados.index'))

@bp.route('/editar/<int:id>', methods=['POST'])
@login_required
@requiere_admin
def editar(id):
    rol = RolEmpleado.query.get_or_404(id)
    rol.nombreRol = request.form.get('nombre')
    rol.descripcionRol = request.form.get('descripcion')
    
    db.session.commit()
    flash(f'Rol "{rol.nombreRol}" actualizado.', 'success')
    return redirect(url_for('rolempleados.index'))

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@requiere_admin
def eliminar(id):
    rol = RolEmpleado.query.get_or_404(id)
    nombre = rol.nombreRol
    
    try:
        db.session.delete(rol)
        db.session.commit()
        flash(f'Rol "{nombre}" eliminado.', 'success')
    except Exception:
        db.session.rollback()
        flash(f'No se puede eliminar el rol "{nombre}" porque tiene empleados asociados.', 'danger')
        
    return redirect(url_for('rolempleados.index'))
