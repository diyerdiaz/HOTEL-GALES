from app import db

class Empleado(db.Model):
    __tablename__ = 'empleado'
    idEmpleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(40), nullable=False)
    apellido = db.Column(db.String(40), nullable=False)
    idRolEmpleado = db.Column(db.Integer, db.ForeignKey('rolempleado.idRolEmpleado'), nullable=False)
    cargo = db.Column(db.String(40))
    salario = db.Column(db.Numeric(10, 2))
    fechaIngreso = db.Column(db.Date)
    
    mantenimientos = db.relationship('MantenimientoHabitacion', backref='empleado', lazy=True)
