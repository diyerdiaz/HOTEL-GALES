"""
Decoradores para proteger rutas por rol y permiso
"""

from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user

def requiere_rol(*roles_permitidos):
    """
    Decorador para requerir un rol específico
    Uso: @requiere_rol('administrador', 'contador')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.rol not in roles_permitidos:
                flash('No tienes permiso para acceder a esta sección', 'error')
                return redirect(url_for('auth.menu'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requiere_permiso(permiso):
    """
    Decorador para requerir un permiso específico
    Uso: @requiere_permiso('ver_usuarios')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión', 'error')
                return redirect(url_for('auth.login'))
            
            if not current_user.tiene_permisos(permiso):
                flash('No tienes permiso para realizar esta acción', 'error')
                return redirect(url_for('auth.menu'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requiere_admin(f):
    """
    Decorador para requerir que el usuario sea administrador
    Uso: @requiere_admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.es_administrador():
            flash('Solo administradores pueden acceder aquí', 'error')
            return redirect(url_for('auth.menu'))
        
        return f(*args, **kwargs)
    return decorated_function
