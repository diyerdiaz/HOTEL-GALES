from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.tiposervicio import TipoServicio
from app.utils.decorators import requiere_admin

bp = Blueprint('tiposervicios', __name__, url_prefix='/admin/tipo-servicios')

@bp.route('/')
@login_required
@requiere_admin
def index():
    tipos = TipoServicio.query.all()
    return render_template('tiposervicios/index.html', tipos=tipos)
