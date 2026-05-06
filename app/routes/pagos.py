from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.pago import Pago
from app.utils.decorators import requiere_permiso

bp = Blueprint('pagos', __name__, url_prefix='/pagos')

@bp.route('/')
@login_required
@requiere_permiso('crear_factura')
def index():
    pagos = Pago.query.all()
    return render_template('pagos/index.html', pagos=pagos)
