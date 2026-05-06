from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.tarea_limpieza import TareaLimpieza
from app.models.habitacion import Habitacion
from app.models.users import User
from app.utils.decorators import requiere_permiso
from datetime import datetime

bp = Blueprint('limpieza', __name__, url_prefix='/limpieza')

@bp.route('/tareas')
@login_required
@requiere_permiso('ver_tareas_limpieza')
def mis_tareas():
    filtro = request.args.get('filtro', 'todas')
    query = TareaLimpieza.query

    # Si es personal de limpieza, solo ve las suyas
    if current_user.rol == 'servicio_limpieza':
        query = query.filter_by(idPersonal=current_user.id)
    
    # Filtros por estado
    if filtro == 'pendientes':
        query = query.filter(TareaLimpieza.estado.in_(['pendiente', 'en curso']))
    elif filtro == 'completadas':
        query = query.filter_by(estado='finalizado')

    tareas = query.order_by(TareaLimpieza.fechaAsignacion.desc()).all()
        
    return render_template('limpieza/tareas.html', tareas=tareas, filtro=filtro)

@bp.route('/asignar', methods=['GET', 'POST'])
@login_required
@requiere_permiso('gestionar_tareas_limpieza')
def asignar_tarea():
    if request.method == 'POST':
        id_habitacion = request.form.get('id_habitacion')
        id_personal = request.form.get('id_personal')
        instrucciones = request.form.get('instrucciones')
        
        nueva_tarea = TareaLimpieza(
            idHabitacion=id_habitacion,
            idPersonal=id_personal,
            instrucciones=instrucciones,
            estado='pendiente'
        )
        
        db.session.add(nueva_tarea)
        db.session.commit()
        flash('Tarea de limpieza asignada correctamente.', 'success')
        return redirect(url_for('limpieza.mis_tareas'))
        
    habitaciones = Habitacion.query.all()
    personal = User.query.filter_by(rol='servicio_limpieza').all()
    return render_template('limpieza/asignar.html', habitaciones=habitaciones, personal=personal)

@bp.route('/completar/<int:id>')
@login_required
@requiere_permiso('ver_tareas_limpieza')
def completar_tarea(id):
    tarea = TareaLimpieza.query.get_or_404(id)
    
    # Verificar que el personal solo complete sus tareas
    if current_user.rol == 'servicio_limpieza' and tarea.idPersonal != current_user.id:
        flash('No puedes completar una tarea que no tienes asignada.', 'error')
        return redirect(url_for('limpieza.mis_tareas'))
        
    tarea.estado = 'finalizado'
    tarea.fechaFinalizacion = datetime.utcnow()
    db.session.commit()
    flash(f'Tarea de la habitación {tarea.habitacion.numeroHabitacion} marcada como completada.', 'success')
    return redirect(url_for('limpieza.mis_tareas'))

@bp.route('/iniciar/<int:id>')
@login_required
@requiere_permiso('ver_tareas_limpieza')
def iniciar_tarea(id):
    tarea = TareaLimpieza.query.get_or_404(id)
    if current_user.rol == 'servicio_limpieza' and tarea.idPersonal != current_user.id:
        flash('No puedes iniciar una tarea que no tienes asignada.', 'error')
        return redirect(url_for('limpieza.mis_tareas'))
        
    tarea.estado = 'en curso'
    db.session.commit()
    flash(f'Has iniciado la limpieza de la habitación {tarea.habitacion.numeroHabitacion}.', 'info')
    return redirect(url_for('limpieza.mis_tareas'))
