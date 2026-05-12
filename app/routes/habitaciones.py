from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.habitacion import Habitacion
from app.models.tipohabitacion import TipoHabitacion
from app.utils.decorators import requiere_permiso

bp = Blueprint('habitaciones', __name__, url_prefix='/habitaciones')

@bp.route('/')
@login_required
@requiere_permiso('ver_habitaciones')
def index():
    habitaciones_todas = Habitacion.query.all()
    
    # Filtrar habitaciones para el equipo de limpieza
    if current_user.rol == 'servicio_limpieza':
        habitaciones = [h for h in habitaciones_todas if h.estadoHabitacion == 'limpieza']
    else:
        from app.models.reserva import Reserva
        for h in habitaciones_todas:
            h.cliente_actual = None
            if h.estadoHabitacion == 'ocupada':
                reserva = Reserva.query.filter_by(idHabitacion=h.idHabitacion, estadoReserva='confirmada').first()
                if reserva and reserva.cliente:
                    h.cliente_actual = f"{reserva.cliente.nombre} {reserva.cliente.apellido}"
        habitaciones = habitaciones_todas
    
    # Verificar si el cliente actual ya tiene una reserva activa
    tiene_reserva_activa = False
    if current_user.rol == 'cliente':
        from app.models.reserva import Reserva
        reserva = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula,
            Reserva.estadoReserva.in_(['pendiente', 'confirmada'])
        ).first()
        tiene_reserva_activa = reserva is not None

    return render_template('habitaciones/index.html', 
                           habitaciones=habitaciones, 
                           tiene_reserva_activa=tiene_reserva_activa)

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@requiere_permiso('crear_habitacion')
def nueva():
    if request.method == 'POST':
        numero = request.form.get('numeroHabitacion')
        id_tipo = request.form.get('idTipoHabitacion')
        precio = request.form.get('precioNoche')
        estado = request.form.get('estadoHabitacion', 'disponible')
        
        # Validaciones de longitud
        if len(str(numero)) > 4:
            flash('El número de habitación no puede tener más de 4 dígitos', 'error')
            return redirect(url_for('habitaciones.nueva'))
            
        if len(str(precio)) > 7:
            flash('El precio no puede tener más de 7 dígitos', 'error')
            return redirect(url_for('habitaciones.nueva'))
        
        nueva_hab = Habitacion(
            numeroHabitacion=numero,
            idTipoHabitacion=id_tipo,
            precioNoche=precio,
            estadoHabitacion=estado
        )
        db.session.add(nueva_hab)
        db.session.commit()
        flash('Habitación registrada con éxito', 'success')
        return redirect(url_for('habitaciones.index'))
        
    tipos = TipoHabitacion.query.all()
    return render_template('habitaciones/nueva.html', tipos=tipos)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@requiere_permiso('editar_habitacion')
def editar(id):
    hab = Habitacion.query.get_or_404(id)
    if request.method == 'POST':
        hab.numeroHabitacion = request.form.get('numeroHabitacion')
        hab.idTipoHabitacion = request.form.get('idTipoHabitacion')
        hab.precioNoche = request.form.get('precioNoche')
        hab.estadoHabitacion = request.form.get('estadoHabitacion')
        
        # Validaciones de longitud
        if len(str(hab.numeroHabitacion)) > 4:
            flash('El número de habitación no puede tener más de 4 dígitos', 'error')
            return redirect(url_for('habitaciones.editar', id=id))
            
        if len(str(hab.precioNoche)) > 7:
            flash('El precio no puede tener más de 7 dígitos', 'error')
            return redirect(url_for('habitaciones.editar', id=id))
        
        db.session.commit()
        flash('Habitación actualizada con éxito', 'success')
        return redirect(url_for('habitaciones.index'))
    
    tipos = TipoHabitacion.query.all()
    return render_template('habitaciones/editar.html', hab=hab, tipos=tipos)

@bp.route('/eliminar/<int:id>')
@login_required
@requiere_permiso('eliminar_habitacion')
def eliminar(id):
    hab = Habitacion.query.get_or_404(id)
    db.session.delete(hab)
    db.session.commit()
    flash('Habitación eliminada correctamente', 'info')
    return redirect(url_for('habitaciones.index'))

@bp.route('/estado/<int:id>/<string:nuevo_estado>')
@login_required
@requiere_permiso('actualizar_habitaciones')
def cambiar_estado(id, nuevo_estado):
    hab = Habitacion.query.get_or_404(id)
    
    if current_user.rol == 'servicio_limpieza' and nuevo_estado == 'disponible' and hab.estadoHabitacion == 'limpieza':
        # Registrar automáticamente en el historial de limpieza sin requerir asignación manual
        from app.models.tarea_limpieza import TareaLimpieza
        from datetime import datetime
        nueva_tarea = TareaLimpieza(
            idHabitacion=hab.idHabitacion,
            idPersonal=current_user.id,
            instrucciones='Limpieza general post estadía',
            estado='finalizado',
            fechaFinalizacion=datetime.utcnow()
        )
        db.session.add(nueva_tarea)
        
    hab.estadoHabitacion = nuevo_estado
    db.session.commit()
    flash(f'Habitación {hab.numeroHabitacion} actualizada a {nuevo_estado}', 'success')
    return redirect(url_for('habitaciones.index'))
