from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.empleado import Empleado
from app.models.rolempleado import RolEmpleado
from app.utils.decorators import requiere_admin

bp = Blueprint('empleados', __name__, url_prefix='/admin/empleados')

@bp.route('/')
@login_required
@requiere_admin
def index():
    empleados = Empleado.query.all()
    return render_template('empleados/index.html', empleados=empleados)
