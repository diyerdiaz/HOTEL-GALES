from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models.reserva import Reserva
from app.models.habitacion import Habitacion
from app.models.pago import Pago
from app.models.factura import Factura
from app.models.users import User
from app.utils.decorators import requiere_permiso
from datetime import datetime

bp = Blueprint('reservas', __name__, url_prefix='/reservas')

@bp.route('/')
@login_required
def index():
    # Permitir que los clientes vean sus propias reservas sin permiso especial
    if current_user.rol == 'cliente':
        query = Reserva.query.filter_by(cedulaCliente=current_user.cedula)
    else:
        # Staff requiere permiso para ver todas las reservas
        if not current_user.tiene_permisos('ver_reservas'):
            flash(_('No tienes permiso para ver reservas'), 'error')
            return redirect(url_for('auth.menu'))
        query = Reserva.query
    
    fecha_filtro = request.args.get('fecha')
    
    # Aplicar filtro de fecha si existe
    if fecha_filtro:
        try:
            fecha_dt = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
            query = query.filter(Reserva.fechaEntrada == fecha_dt)
        except ValueError:
            pass

    # Ordenar por más reciente primero (ID descendente)
    reservas = query.order_by(Reserva.idReserva.desc()).all()
    
    return render_template('reservas/index.html', reservas=reservas, fecha_filtro=fecha_filtro)

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    # Permitir que los clientes creen sus propias reservas
    if current_user.rol == 'cliente':
        habitaciones_disponibles = Habitacion.query.filter_by(estadoHabitacion='disponible').all()
    else:
        # Staff requiere permiso para crear reservas
        from app.utils.decorators import requiere_permiso
        if not current_user.tiene_permisos('crear_reservas'):
            flash(_('No tienes permiso para crear reservas'), 'error')
            return redirect(url_for('auth.menu'))
        habitaciones_disponibles = Habitacion.query.filter_by(estadoHabitacion='disponible').all()
    
    from app.models.cliente import Cliente
    clientes = Cliente.query.all()
    
    # Para pre-seleccionar habitación y validar fechas
    habitacion_id_previa = request.args.get('habitacion_id', type=int)
    hoy = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        id_habitacion = request.form.get('id_habitacion')
        fecha_entrada_str = request.form.get('fecha_entrada')
        fecha_salida_str = request.form.get('fecha_salida')
        
        # Validar fechas básicas
        try:
            fecha_entrada = datetime.strptime(fecha_entrada_str, '%Y-%m-%d')
            fecha_salida = datetime.strptime(fecha_salida_str, '%Y-%m-%d')
            
            if fecha_entrada.date() < datetime.now().date():
                flash(_('No puedes reservar en una fecha pasada.'), 'error')
                return redirect(url_for('reservas.nueva', habitacion_id=id_habitacion))
            
            if fecha_salida <= fecha_entrada:
                flash(_('La fecha de salida debe ser posterior a la de entrada.'), 'error')
                return redirect(url_for('reservas.nueva', habitacion_id=id_habitacion))
                
        except ValueError:
            flash(_('Formato de fecha inválido.'), 'error')
            return redirect(url_for('reservas.nueva'))

        metodo_pago = request.form.get('metodo_pago')
        cantidad_personas = request.form.get('cantidad_personas', 1)
        
        # Determinar la cédula del cliente
        if current_user.rol == 'cliente':
            cedula_cliente = current_user.cedula
        else:
            cedula_cliente = request.form.get('cedula_cliente')
            
        if not cedula_cliente:
            flash(_('Error: No se proporcionó la cédula del cliente.'), 'error')
            return redirect(url_for('reservas.nueva'))

        # Verificar si el cliente ya tiene una reserva activa
        reserva_activa = Reserva.query.filter(
            Reserva.cedulaCliente == cedula_cliente,
            Reserva.estadoReserva.in_(['pendiente', 'confirmada'])
        ).first()

        if reserva_activa:
            flash(_('Este cliente ya tiene una reserva activa.'), 'warning')
            return redirect(url_for('reservas.index'))

        # Crear la reserva
        # FILTRO: Solo guardar 'recepcionista_id' si el usuario NO es un cliente
        recepcionista_id_val = current_user.id if current_user.rol != 'cliente' else None
        
        nueva_reserva = Reserva(
            cedulaCliente=cedula_cliente,
            idHabitacion=id_habitacion,
            fechaEntrada=fecha_entrada,
            fechaSalida=fecha_salida,
            cantidadPersonas=cantidad_personas,
            estadoReserva='pendiente',
            recepcionista_id=recepcionista_id_val  # Solo guarda si es recepcionista o admin
        )
        
        db.session.add(nueva_reserva)
        db.session.flush() 
        
        # Registrar el pago inicial
        habitacion = Habitacion.query.get(id_habitacion)
        nuevo_pago = Pago(
            idReserva=nueva_reserva.idReserva,
            metodoPago=metodo_pago,
            valorPago=habitacion.precioNoche
        )
        
        # Calcular total y crear Factura
        dias = (fecha_salida - fecha_entrada).days
        if dias <= 0: dias = 1
        total = habitacion.precioNoche * dias
        
        nueva_factura = Factura(
            idReserva=nueva_reserva.idReserva,
            totalFactura=total
        )
        db.session.add(nueva_factura)
        
        habitacion.estadoHabitacion = 'ocupada'
        db.session.add(nuevo_pago)
        db.session.commit()
        
        # Crear notificación para el cliente
        from app.models.notificacion import Notificacion
        # Si es el cliente quien crea la reserva, usar current_user.id, si es staff, buscar el usuario del cliente
        if current_user.rol == 'cliente':
            usuario_id = current_user.id
        else:
            usuario_id = User.query.filter_by(cedula=cedula_cliente).first().id
        
        Notificacion.crear_notificacion(
            usuario_id=usuario_id,
            tipo='reserva',
            titulo='¡Reserva Creada!',
            mensaje=f'Tu reserva para la habitación {habitacion.numeroHabitacion} ha sido creada exitosamente.',
            link=url_for('reservas.index')
        )
        
        flash(_('¡Reserva creada con éxito!'), 'success')
        return redirect(url_for('reservas.index'))

    return render_template('reservas/nueva.html', 
                           habitaciones=habitaciones_disponibles, 
                           clientes=clientes,
                           habitacion_id=habitacion_id_previa,
                           hoy=hoy)

@bp.route('/cambiar-estado/<int:id>', methods=['POST'])
@login_required
@requiere_permiso('editar_reservas')
def cambiar_estado(id):
    reserva = Reserva.query.get_or_404(id)
    nuevo_estado = request.form.get('estadoReserva')
    
    if nuevo_estado in ['pendiente', 'confirmada', 'finalizada', 'cancelada', 'limpieza']:
        if nuevo_estado == 'limpieza':
            reserva.estadoReserva = 'finalizada'
            reserva.habitacion.estadoHabitacion = 'limpieza'
            flash(_('Reserva finalizada y habitación enviada a limpieza.'), 'success')
        else:
            reserva.estadoReserva = nuevo_estado
            # Sincronizar el estado de la habitación para que todo cuadre
            if nuevo_estado == 'confirmada':
                reserva.habitacion.estadoHabitacion = 'ocupada'
            elif nuevo_estado in ['finalizada', 'cancelada']:
                reserva.habitacion.estadoHabitacion = 'disponible'
            flash(_('Estado actualizado a: %(estado)s') % {'estado': nuevo_estado}, 'success')
            
        # Registrar o actualizar el recepcionista que atendió la reserva
        if current_user.rol != 'cliente':
            reserva.recepcionista_id = current_user.id
            
        db.session.commit()
    else:
        flash(_('Estado inválido seleccionado.'), 'error')
        
    return redirect(url_for('reservas.index'))

@bp.route('/mantenimiento/<int:id>', methods=['POST'])
@login_required
@requiere_permiso('actualizar_habitaciones')
def mantenimiento(id):
    reserva = Reserva.query.get_or_404(id)
    reserva.habitacion.estadoHabitacion = 'mantenimiento'
    db.session.commit()
    flash(_('Habitación %(numero)s puesta en mantenimiento.') % {'numero': reserva.habitacion.numeroHabitacion}, 'warning')
    return redirect(url_for('reservas.index'))

@bp.route('/cancelar/<int:id>', methods=['POST'])
@login_required
def cancelar(id):
    reserva = Reserva.query.get_or_404(id)

    # Solo el cliente dueño de la reserva o el personal de recepción/administración puede cancelar
    es_duenio = current_user.rol == 'cliente' and reserva.cedulaCliente == current_user.cedula
    if not (es_duenio or current_user.rol in ('administrador', 'recepcionista')):
        flash(_('No tienes permiso para cancelar esta reserva'), 'error')
        return redirect(url_for('reservas.index'))
    
    if reserva.estadoReserva not in ['pendiente', 'confirmada']:
        flash(_('Esta reservación no se puede cancelar en su estado actual'), 'error')
        return redirect(url_for('reservas.index'))

    # Eliminar facturas y pagos asociados a la reserva
    Factura.query.filter_by(idReserva=reserva.idReserva).delete()
    Pago.query.filter_by(idReserva=reserva.idReserva).delete()

    reserva.estadoReserva = 'cancelada'
    reserva.habitacion.estadoHabitacion = 'disponible'
    db.session.commit()
    
    # Crear notificación para el cliente
    from app.models.notificacion import Notificacion
    # Si es el cliente quien cancela, usar current_user.id, si es staff, buscar el usuario del cliente
    if current_user.rol == 'cliente':
        usuario_id = current_user.id
    else:
        usuario_id = User.query.filter_by(cedula=reserva.cedulaCliente).first().id
    
    Notificacion.crear_notificacion(
        usuario_id=usuario_id,
        tipo='cancelacion',
        titulo='Reserva Cancelada',
        mensaje=f'Tu reserva #{id} ha sido cancelada.',
        link=url_for('reservas.index')
    )
    
    flash(_('Reserva #%(id)s cancelada correctamente.') % {'id': id}, 'info')
    return redirect(url_for('reservas.index'))
