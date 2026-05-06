from flask_login import UserMixin
from datetime import datetime
from app import db 

class User(db.Model, UserMixin):
    """Modelo de Usuario para la aplicación Hotel"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), default='cliente', nullable=False)
    cedula = db.Column(db.BigInteger, db.ForeignKey('cliente.cedula'), nullable=True)
    estado_limpieza = db.Column(db.String(20), default='disponible')
    salario = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario,
            "password": self.password,
            "rol": self.rol,
            "created_at": self.created_at
        }
    
    def tiene_permisos(self, permiso):
        """Verifica si el usuario tiene un permiso específico"""
        from app.utils.roles import PERMISOS_ROL
        permisos = PERMISOS_ROL.get(self.rol, [])
        return permiso in permisos
    
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'administrador'

    def save(self):
        """Guarda el usuario en la base de datos"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Elimina el usuario de la base de datos"""
        db.session.delete(self)
        db.session.commit()
