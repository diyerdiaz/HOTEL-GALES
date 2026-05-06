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
    tipo.nombreTipo = request.form.get('nombreTipo')
    tipo.descripcionTipo = request.form.get('descripcionTipo')
    
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
