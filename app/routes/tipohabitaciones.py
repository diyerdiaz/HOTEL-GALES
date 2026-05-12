from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.tipohabitacion import TipoHabitacion
from app.utils.decorators import requiere_admin

bp = Blueprint('tipohabitaciones', __name__, url_prefix='/admin/tipo-habitaciones')

@bp.route('/', methods=['GET', 'POST'])
@login_required
@requiere_admin
def index():
    if request.method == 'POST':
        nombre = request.form.get('nombreTipo')
        descripcion = request.form.get('descripcionTipo')
        
        if not nombre:
            flash('El nombre es obligatorio', 'error')
        elif len(nombre) > 15:
            flash('El nombre no puede tener más de 15 caracteres', 'error')
        elif descripcion and len(descripcion) > 80:
            flash('La descripción no puede tener más de 80 caracteres', 'error')
        else:
            nuevo_tipo = TipoHabitacion(nombreTipo=nombre, descripcionTipo=descripcion)
            db.session.add(nuevo_tipo)
            db.session.commit()
            flash('Tipo de habitación creado exitosamente', 'success')
            return redirect(url_for('tipohabitaciones.index'))
            
    tipos = TipoHabitacion.query.all()
    return render_template('tipohabitaciones/index.html', tipos=tipos)

@bp.route('/editar/<int:id>', methods=['POST'])
@login_required
@requiere_admin
def editar(id):
    tipo = TipoHabitacion.query.get_or_404(id)
    nombre = request.form.get('nombreTipo')
    descripcion = request.form.get('descripcionTipo')
    
    if not nombre:
        flash('El nombre es obligatorio', 'error')
    elif len(nombre) > 15:
        flash('El nombre no puede tener más de 15 caracteres', 'error')
    elif descripcion and len(descripcion) > 80:
        flash('La descripción no puede tener más de 80 caracteres', 'error')
    else:
        tipo.nombreTipo = nombre
        tipo.descripcionTipo = descripcion
        db.session.commit()
        flash('Tipo de habitación actualizado', 'success')

    return redirect(url_for('tipohabitaciones.index'))

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@requiere_admin
def eliminar(id):
    tipo = TipoHabitacion.query.get_or_404(id)
    try:
        db.session.delete(tipo)
        db.session.commit()
        flash('Tipo de habitación eliminado', 'success')
    except:
        db.session.rollback()
        flash('No se puede eliminar este tipo porque tiene habitaciones asociadas', 'error')
        
    return redirect(url_for('tipohabitaciones.index'))
