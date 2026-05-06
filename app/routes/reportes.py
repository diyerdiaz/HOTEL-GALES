from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.reserva import Reserva
from app.models.factura import Factura
from app.models.cliente import Cliente
from app.models.empleado import Empleado
from app.models.users import User
from app.utils.decorators import requiere_admin
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

bp = Blueprint('reportes', __name__, url_prefix='/admin/reportes')

@bp.route('/')
@login_required
@requiere_admin
def index():
    # 1. Obtener el mes a filtrar (formato YYYY-MM)
    mes_seleccionado = request.args.get('mes')
    if not mes_seleccionado:
        mes_seleccionado = datetime.now().strftime('%Y-%m')

    # 2. Calcular rango de fechas para el mes seleccionado
    try:
        año, mes = map(int, mes_seleccionado.split('-'))
        _, ultimo_dia = calendar.monthrange(año, mes)
        # Convertir a objetos date para comparación correcta en SQLAlchemy
        fecha_inicio = datetime(año, mes, 1).date()
        fecha_fin = datetime(año, mes, ultimo_dia).date()
    except Exception as e:
        print(f"Error parsing date: {e}")
        hoy = datetime.now()
        fecha_inicio = hoy.replace(day=1).date()
        _, ultimo_dia = calendar.monthrange(hoy.year, hoy.month)
        fecha_fin = hoy.replace(day=ultimo_dia).date()

    # 3. Listado de Reservas del Mes
    reservas_mes = Reserva.query.filter(
        Reserva.fechaEntrada >= fecha_inicio,
        Reserva.fechaEntrada <= fecha_fin
    ).order_by(Reserva.fechaEntrada.desc()).all()

    # 4. Ganancias por Cliente Filtrado (Mes)
    ganancias_clientes = db.session.query(
        Cliente.nombre,
        Cliente.apellido,
        func.sum(Factura.totalFactura).label('total')
    ).join(Reserva, Cliente.cedula == Reserva.cedulaCliente)\
     .join(Factura, Reserva.idReserva == Factura.idReserva)\
     .filter(
         Factura.fechaFactura >= fecha_inicio, 
         Factura.fechaFactura <= fecha_fin,
         Reserva.estadoReserva.in_(['confirmada', 'finalizada'])
     )\
     .group_by(Cliente.cedula, Cliente.nombre, Cliente.apellido)\
     .order_by(func.sum(Factura.totalFactura).desc())\
     .limit(5).all()

    # 5. Total ganancias mes
    total_ganancias_mes = db.session.query(func.sum(Factura.totalFactura))\
        .join(Reserva)\
        .filter(
            Factura.fechaFactura >= fecha_inicio, 
            Factura.fechaFactura <= fecha_fin,
            Reserva.estadoReserva.in_(['confirmada', 'finalizada'])
        ).scalar() or 0
        
    # 5.1 Total ganancias histórico
    total_ganancias_historico = db.session.query(func.sum(Factura.totalFactura))\
        .join(Reserva)\
        .filter(Reserva.estadoReserva.in_(['confirmada', 'finalizada'])).scalar() or 0

    # 6. Listado de Empleados (Basado en usuarios con roles operativos)
    roles_empleados = ['recepcionista', 'servicio_limpieza']
    usuarios_staff = User.query.filter(User.rol.in_(roles_empleados)).all()
    
    empleados = []
    for u in usuarios_staff:
        # Obtener datos personales del cliente asociado si existe
        cliente = Cliente.query.get(u.cedula) if u.cedula else None
        
        # Mapear rol a nombre legible
        cargo_nombres = {
            'administrador': 'Administrador',
            'recepcionista': 'Recepcionista',
            'servicio_limpieza': 'Serv. Limpieza'
        }
        
        empleados.append({
            'id': u.id,
            'nombre': cliente.nombre if cliente else u.usuario,
            'apellido': cliente.apellido if cliente else '',
            'cargo': cargo_nombres.get(u.rol, u.rol),
            'fechaIngreso': u.created_at,
            'salario': float(u.salario) if u.salario else 0
        })
        
    total_nomina = sum([e['salario'] for e in empleados])
    
    # Margen de Ganancia (Porcentaje)
    margen_ganancia = 0
    if total_ganancias_mes > 0:
        beneficio_neto = float(total_ganancias_mes) - float(total_nomina)
        margen_ganancia = (beneficio_neto / float(total_ganancias_mes)) * 100

    return render_template('dashboard/reportes.html', 
                           reservas_mes=reservas_mes,
                           ganancias_clientes=ganancias_clientes,
                           empleados=empleados,
                           total_nomina=total_nomina,
                           total_ganancias_mes=total_ganancias_mes,
                           total_ganancias_historico=total_ganancias_historico,
                           margen_ganancia=margen_ganancia,
                           mes_seleccionado=mes_seleccionado,
                           hoy=datetime.now().strftime('%d/%m/%Y'))

@bp.route('/actualizar-salario/<int:id>', methods=['POST'])
@login_required
@requiere_admin
def actualizar_salario(id):
    usuario = User.query.get_or_404(id)
    nuevo_salario = request.form.get('salario')
    
    if nuevo_salario:
        try:
            usuario.salario = float(nuevo_salario)
            db.session.commit()
            flash(f'Salario actualizado correctamente', 'success')
        except ValueError:
            flash('Valor de salario inválido', 'error')
            
    return redirect(url_for('reportes.index'))
