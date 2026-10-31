import qrcode
import io
import base64
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from itsdangerous import URLSafeSerializer, BadSignature
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models.factura import Factura
from app.models.reserva import Reserva
from app.models.cliente import Cliente
from app.utils.decorators import requiere_permiso

bp = Blueprint('facturas', __name__, url_prefix='/facturas')


def _firmador():
    # Firma el id de la factura con la SECRET_KEY: el enlace del QR no se puede adivinar
    return URLSafeSerializer(current_app.config['SECRET_KEY'], salt='validar-factura')


def token_validacion(factura_id):
    return _firmador().dumps(factura_id)

@bp.route('/')
@login_required
@requiere_permiso('ver_facturacion')
def index():
    # 1. Unir tablas para poder filtrar por cliente
    query = Factura.query.join(Reserva).join(Cliente)
    
    # 2. Sistema de búsqueda por nombre de cliente
    search_query = request.args.get('search', '')
    if search_query:
        query = query.filter(
            (Cliente.nombre.ilike(f'%{search_query}%')) | 
            (Cliente.apellido.ilike(f'%{search_query}%'))
        )

    # 3. Filtrar por cliente si el usuario actual es un cliente
    if current_user.rol == 'cliente':
        query = query.filter(Reserva.cedulaCliente == current_user.cedula)
    
    # 4. Obtener resultados ordenados
    facturas = query.order_by(Factura.fechaFactura.desc()).all()
    
    return render_template('facturas/index.html', facturas=facturas)

@bp.route('/ver/<int:id>')
@login_required
@requiere_permiso('ver_facturacion')
def ver(id):
    factura = Factura.query.get_or_404(id)
    
    # Seguridad: Si es cliente, solo puede ver su propia factura
    if current_user.rol == 'cliente' and factura.reserva.cedulaCliente != current_user.cedula:
        flash(_('No tienes permiso para ver esta factura.'), 'error')
        return redirect(url_for('facturas.index'))
    
    # Calculamos días de estancia
    dias = (factura.reserva.fechaSalida - factura.reserva.fechaEntrada).days
    if dias <= 0: dias = 1

    # Generar URL de validación absoluta
    url_validacion = url_for('facturas.validar', token=token_validacion(factura.idFactura), _external=True)
    
    # Generar QR en memoria
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0c1433", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('facturas/ver.html', factura=factura, dias=dias, qr_base64=qr_base64)

@bp.route('/validar/<token>')
def validar(token):
    """Ruta pública para verificar la autenticidad de una factura vía código QR"""
    try:
        factura_id = _firmador().loads(token)
    except BadSignature:
        abort(404)
    factura = Factura.query.get_or_404(factura_id)
    return render_template('facturas/validar.html', factura=factura)
