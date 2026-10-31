import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models.habitacion import Habitacion
from app.models.tipohabitacion import TipoHabitacion
from app.utils.decorators import requiere_permiso

bp = Blueprint('habitaciones', __name__, url_prefix='/habitaciones')

EXTENSIONES_IMAGEN = {'jpg', 'jpeg', 'png', 'webp'}
CAMPOS_IMAGEN = ('imagen1', 'imagen2', 'imagen3')


def _carpeta_imagenes():
    carpeta = os.path.join(current_app.static_folder, 'uploads', 'habitaciones')
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def _imagenes_enviadas():
    return [f for f in request.files.getlist('imagenes') if f and f.filename]


def _validar_imagenes(hab=None):
    """Devuelve un mensaje de error si algún archivo no es válido o se superan las 3 imágenes"""
    for archivo in _imagenes_enviadas():
        ext = archivo.filename.rsplit('.', 1)[-1].lower() if '.' in archivo.filename else ''
        if ext not in EXTENSIONES_IMAGEN:
            return _('Solo se permiten imágenes JPG, PNG o WEBP')
        archivo.stream.seek(0, os.SEEK_END)
        vacia = archivo.stream.tell() == 0
        archivo.stream.seek(0)
        if vacia:
            return _('La imagen %(nombre)s está vacía o dañada', nombre=archivo.filename)

    conservadas = 0
    if hab:
        conservadas = sum(1 for campo in CAMPOS_IMAGEN
                          if getattr(hab, campo) and not request.form.get(f'eliminar_{campo}'))
    if conservadas + len(_imagenes_enviadas()) > len(CAMPOS_IMAGEN):
        return _('Solo puedes agregar máximo 3 imágenes por habitación')
    return None


def _borrar_imagen(nombre):
    if nombre:
        ruta = os.path.join(_carpeta_imagenes(), nombre)
        if os.path.exists(ruta):
            os.remove(ruta)


def _guardar_imagenes(hab):
    """Elimina las imágenes marcadas y ubica las nuevas en los espacios libres"""
    for campo in CAMPOS_IMAGEN:
        if request.form.get(f'eliminar_{campo}'):
            _borrar_imagen(getattr(hab, campo))
            setattr(hab, campo, None)

    libres = [campo for campo in CAMPOS_IMAGEN if not getattr(hab, campo)]
    for campo, archivo in zip(libres, _imagenes_enviadas()):
        ext = archivo.filename.rsplit('.', 1)[-1].lower()
        nombre = f"{uuid.uuid4().hex}.{ext}"
        archivo.save(os.path.join(_carpeta_imagenes(), nombre))
        setattr(hab, campo, nombre)

@bp.route('/publica')
def publica():
    """Vista pública de habitaciones para usuarios no autenticados"""
    habitaciones_todas = Habitacion.query.all()
    
    # Obtener parámetros de búsqueda y filtros
    busqueda = request.args.get('busqueda', '')
    tipo_habitacion = request.args.get('tipo', '')
    precio_min = request.args.get('precio_min', '')
    precio_max = request.args.get('precio_max', '')
    estado = request.args.get('estado', 'disponible')  # Por defecto mostrar solo disponibles
    
    # Aplicar filtros
    query = Habitacion.query
    
    # Búsqueda por número de habitación
    if busqueda:
        try:
            num_hab = int(busqueda)
            query = query.filter(Habitacion.numeroHabitacion == num_hab)
        except ValueError:
            pass
    
    # Filtro por tipo de habitación
    if tipo_habitacion:
        query = query.filter(Habitacion.idTipoHabitacion == tipo_habitacion)
    
    # Filtro por precio mínimo
    if precio_min:
        try:
            query = query.filter(Habitacion.precioNoche >= float(precio_min))
        except ValueError:
            pass
    
    # Filtro por precio máximo
    if precio_max:
        try:
            query = query.filter(Habitacion.precioNoche <= float(precio_max))
        except ValueError:
            pass
    
    # Filtro por estado (por defecto solo disponibles para vista pública)
    if estado:
        query = query.filter(Habitacion.estadoHabitacion == estado)
    
    habitaciones_todas = query.all()
    
    # Obtener tipos de habitación para el filtro
    tipos = TipoHabitacion.query.all()
    
    # Calcular promedio de calificaciones para cada habitación
    from app.models.comentario import Comentario
    for hab in habitaciones_todas:
        comentarios = Comentario.query.filter_by(idHabitacion=hab.idHabitacion).all()
        if comentarios:
            hab.promedio = sum(c.calificacion for c in comentarios) / len(comentarios)
            hab.num_comentarios = len(comentarios)
        else:
            hab.promedio = 0
            hab.num_comentarios = 0

    return render_template('habitaciones/publica.html', 
                           habitaciones=habitaciones_todas,
                           tipos=tipos,
                           busqueda=busqueda,
                           tipo_habitacion=tipo_habitacion,
                           precio_min=precio_min,
                           precio_max=precio_max,
                           estado=estado)

@bp.route('/')
@login_required
@requiere_permiso('ver_habitaciones')
def index():
    habitaciones_todas = Habitacion.query.all()
    
    # Obtener parámetros de búsqueda y filtros
    busqueda = request.args.get('busqueda', '')
    tipo_habitacion = request.args.get('tipo', '')
    precio_min = request.args.get('precio_min', '')
    precio_max = request.args.get('precio_max', '')
    estado = request.args.get('estado', '')
    
    # Aplicar filtros
    query = Habitacion.query
    
    # Búsqueda por número de habitación
    if busqueda:
        try:
            num_hab = int(busqueda)
            query = query.filter(Habitacion.numeroHabitacion == num_hab)
        except ValueError:
            pass
    
    # Filtro por tipo de habitación
    if tipo_habitacion:
        query = query.filter(Habitacion.idTipoHabitacion == tipo_habitacion)
    
    # Filtro por precio mínimo
    if precio_min:
        try:
            query = query.filter(Habitacion.precioNoche >= float(precio_min))
        except ValueError:
            pass
    
    # Filtro por precio máximo
    if precio_max:
        try:
            query = query.filter(Habitacion.precioNoche <= float(precio_max))
        except ValueError:
            pass
    
    # Filtro por estado
    if estado:
        query = query.filter(Habitacion.estadoHabitacion == estado)
    
    habitaciones_todas = query.all()
    
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
    
    # Obtener tipos de habitación para el filtro
    tipos = TipoHabitacion.query.all()

    return render_template('habitaciones/index.html', 
                           habitaciones=habitaciones, 
                           tiene_reserva_activa=tiene_reserva_activa,
                           tipos=tipos,
                           busqueda=busqueda,
                           tipo_habitacion=tipo_habitacion,
                           precio_min=precio_min,
                           precio_max=precio_max,
                           estado=estado)

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
            flash(_('El número de habitación no puede tener más de 4 dígitos'), 'error')
            return redirect(url_for('habitaciones.nueva'))
            
        if len(str(precio)) > 7:
            flash(_('El precio no puede tener más de 7 dígitos'), 'error')
            return redirect(url_for('habitaciones.nueva'))

        error_imagen = _validar_imagenes()
        if error_imagen:
            flash(error_imagen, 'error')
            return redirect(url_for('habitaciones.nueva'))
        
        nueva_hab = Habitacion(
            numeroHabitacion=numero,
            idTipoHabitacion=id_tipo,
            precioNoche=precio,
            estadoHabitacion=estado
        )
        _guardar_imagenes(nueva_hab)
        db.session.add(nueva_hab)
        db.session.commit()
        flash(_('Habitación registrada con éxito'), 'success')
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
            flash(_('El número de habitación no puede tener más de 4 dígitos'), 'error')
            return redirect(url_for('habitaciones.editar', id=id))
            
        if len(str(hab.precioNoche)) > 7:
            flash(_('El precio no puede tener más de 7 dígitos'), 'error')
            return redirect(url_for('habitaciones.editar', id=id))

        error_imagen = _validar_imagenes(hab)
        if error_imagen:
            flash(error_imagen, 'error')
            return redirect(url_for('habitaciones.editar', id=id))

        _guardar_imagenes(hab)
        db.session.commit()
        flash(_('Habitación actualizada con éxito'), 'success')
        return redirect(url_for('habitaciones.index'))
    
    tipos = TipoHabitacion.query.all()
    return render_template('habitaciones/editar.html', hab=hab, tipos=tipos)

@bp.route('/eliminar/<int:id>')
@login_required
@requiere_permiso('eliminar_habitacion')
def eliminar(id):
    hab = Habitacion.query.get_or_404(id)
    imagenes = hab.imagenes
    db.session.delete(hab)
    db.session.commit()
    for img in imagenes:
        _borrar_imagen(img)
    flash(_('Habitación eliminada correctamente'), 'info')
    return redirect(url_for('habitaciones.index'))

@bp.route('/detalle/<int:id>')
@login_required
def detalle(id):
    """Ver detalles de una habitación específica"""
    hab = Habitacion.query.get_or_404(id)
    from app.models.comentario import Comentario
    
    # Obtener comentarios de la habitación
    comentarios = Comentario.query.filter_by(idHabitacion=id).order_by(Comentario.fechaComentario.desc()).limit(10).all()
    
    # Calcular promedio de calificaciones
    if comentarios:
        promedio = sum(c.calificacion for c in comentarios) / len(comentarios)
    else:
        promedio = 0
    
    # Verificar si el cliente actual ya comentó esta habitación
    ya_comento = False
    if current_user.rol == 'cliente':
        ya_comento = Comentario.query.filter_by(
            idHabitacion=id,
            cedulaCliente=current_user.cedula
        ).first() is not None
    
    # Verificar si el cliente actual tiene una reserva activa
    tiene_reserva_activa = False
    if current_user.rol == 'cliente':
        from app.models.reserva import Reserva
        reserva = Reserva.query.filter(
            Reserva.cedulaCliente == current_user.cedula,
            Reserva.estadoReserva.in_(['pendiente', 'confirmada'])
        ).first()
        tiene_reserva_activa = reserva is not None
    
    return render_template('habitaciones/detalle.html', 
                          hab=hab, 
                          comentarios=comentarios,
                          promedio=promedio,
                          ya_comento=ya_comento,
                          tiene_reserva_activa=tiene_reserva_activa)

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
    flash(_('Habitación %(numero)s actualizada a %(estado)s') % {'numero': hab.numeroHabitacion, 'estado': nuevo_estado}, 'success')
    return redirect(url_for('habitaciones.index'))
