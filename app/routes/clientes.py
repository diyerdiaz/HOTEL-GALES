from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.cliente import Cliente
from app.utils.decorators import requiere_permiso

bp = Blueprint('clientes', __name__, url_prefix='/clientes')

@bp.route('/')
@login_required
@requiere_permiso('ver_huespedes')
def index():
    from app.models.users import User
    # 1. Obtener base de la consulta
    query = Cliente.query
    
    # 2. Sistema de búsqueda por nombre o apellido
    search_query = request.args.get('search', '')
    if search_query:
        query = query.filter(
            (Cliente.nombre.ilike(f'%{search_query}%')) | 
            (Cliente.apellido.ilike(f'%{search_query}%'))
        )
    
    clientes_bd = query.all()
    
    # 3. Obtener los IDs (cédulas) de usuarios que NO son rol 'cliente'
    usuarios_staff = User.query.filter(User.rol != 'cliente').all()
    cedulas_staff = [u.cedula for u in usuarios_staff if u.cedula]
    
    # 4. Filtrar la lista para mostrar solo clientes reales
    clientes_filtrados = [c for c in clientes_bd if c.cedula not in cedulas_staff]
    
    # 5. Calcular estadísticas y obtener información de quién atendió
    import json
    for c in clientes_filtrados:
        c.total_r = len(c.reservas)
        c.fin_r = sum(1 for r in c.reservas if r.estadoReserva == 'finalizada')
        c.can_r = sum(1 for r in c.reservas if r.estadoReserva == 'cancelada')
        c.ocu_r = sum(1 for r in c.reservas if r.estadoReserva == 'confirmada' or r.estadoReserva == 'pendiente')
        
        # Preparar JSON de todas las reservas para la tabla detallada del modal
        reservas_lista = []
        for r in c.reservas:
            total_r = float(r.facturas[0].totalFactura) if r.facturas else 0
            reservas_lista.append({
                'fecha': r.fechaEntrada.strftime('%d/%m/%Y'),
                'habitacion': r.habitacion.numeroHabitacion if r.habitacion else 'N/A',
                'estado': r.estadoReserva,
                'total': total_r
            })
        c.reservas_json = json.dumps(reservas_lista)

        # Obtener lista de recepcionistas que atendieron a este cliente
        c.recepcionistas_atendieron = []
        for r in c.reservas:
            # Mostramos todo (incluyendo canceladas) como solicitó el usuario
            if r.atendido_por:
                user_atendio = User.query.get(r.atendido_por)
                if user_atendio:
                    # Calcular el total de la reserva para mostrarlo en la tarjeta
                    total_reserva = 0
                    if r.facturas:
                        total_reserva = r.facturas[0].totalFactura
                    
                    c.recepcionistas_atendieron.append({
                        'usuario': user_atendio.usuario,
                        'nombre': user_atendio.usuario,
                        'rol': user_atendio.rol,
                        'fecha_reserva': r.fechaEntrada,
                        'estado': r.estadoReserva,
                        'total': total_reserva
                    })

    return render_template('clientes/index.html', clientes=clientes_filtrados)

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@requiere_permiso('crear_huespedes')
def nuevo():
    if request.method == 'POST':
        # Lógica para guardar cliente
        pass
    return render_template('clientes/form.html')
