from app import db

class RolEmpleado(db.Model):
    __tablename__ = 'rolempleado'
    idRolEmpleado = db.Column(db.Integer, primary_key=True)
    nombreRol = db.Column(db.String(40), nullable=False)
    descripcionRol = db.Column(db.String(100))
    
    empleados = db.relationship('Empleado', backref='rol_info', lazy=True)
