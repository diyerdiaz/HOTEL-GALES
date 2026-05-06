from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.consumo import Consumo
from app.utils.decorators import requiere_rol

bp = Blueprint('consumos', __name__, url_prefix='/consumos')

@bp.route('/')
@login_required
@requiere_rol('administrador', 'recepcionista')
def index():
    consumos = Consumo.query.all()
    return render_template('consumos/index.html', consumos=consumos)
