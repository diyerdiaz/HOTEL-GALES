from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.mantenimiento import MantenimientoHabitacion
from app.models.users import User
from app.utils.decorators import requiere_rol

bp = Blueprint('mantenimientos', __name__, url_prefix='/mantenimientos')

@bp.route('/')
@login_required
@requiere_rol('administrador', 'recepcionista')
def index():
    from app.models.tarea_limpieza import TareaLimpieza
    from datetime import datetime
    
    query = User.query.filter_by(rol='servicio_limpieza')
    
    search = request.args.get('search', '')
    if search:
        query = query.filter(User.usuario.ilike(f'%{search}%'))
        
    fecha = request.args.get('fecha', '')
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
            query = query.join(TareaLimpieza, User.id == TareaLimpieza.idPersonal)\
                         .filter(db.func.date(TareaLimpieza.fechaAsignacion) == fecha_dt).distinct()
        except ValueError:
            pass
            
    limpieza = query.all()
    mantenimientos = MantenimientoHabitacion.query.all()
    
    return render_template('mantenimientos/index.html', 
                           mantenimientos=mantenimientos, 
                           limpieza=limpieza,
                           search=search,
                           fecha=fecha)

@bp.route('/cambiar-estado/<int:id>/<string:estado>')
@login_required
@requiere_rol('administrador', 'recepcionista')
def cambiar_estado(id, estado):
    """Cambia el estado de disponibilidad del personal de limpieza"""
    staff = User.query.get_or_404(id)
    
    if staff.rol != 'servicio_limpieza':
        flash('Usuario no es personal de limpieza.', 'error')
        return redirect(url_for('mantenimientos.index'))
    
    estados_validos = ['disponible', 'ocupado']
    if estado not in estados_validos:
        flash('Estado inválido.', 'error')
        return redirect(url_for('mantenimientos.index'))
    
    staff.estado_limpieza = estado
    db.session.commit()
    flash(f'{staff.usuario} ahora está {estado}.', 'success')
    return redirect(url_for('mantenimientos.index'))
