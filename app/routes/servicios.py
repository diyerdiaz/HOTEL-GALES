from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.servicio import Servicio
from app.models.tiposervicio import TipoServicio
from app.utils.decorators import requiere_rol

bp = Blueprint('servicios', __name__, url_prefix='/servicios')

@bp.route('/')
@login_required
@requiere_rol('administrador', 'recepcionista')
def index():
    servicios = Servicio.query.all()
    return render_template('servicios/index.html', servicios=servicios)
