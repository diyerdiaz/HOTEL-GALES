from app import db
from datetime import datetime

class MantenimientoHabitacion(db.Model):
    __tablename__ = 'mantenimientohabitacion'
    idMantenimiento = db.Column(db.Integer, primary_key=True)
    idHabitacion = db.Column(db.Integer, db.ForeignKey('habitacion.idHabitacion'), nullable=False)
    idEmpleado = db.Column(db.Integer, db.ForeignKey('empleado.idEmpleado'), nullable=False)
    fechaMantenimiento = db.Column(db.Date, default=datetime.utcnow)
    descripcionProblema = db.Column(db.String(150))
    costoMantenimiento = db.Column(db.Numeric(10, 2))
    estadoMantenimiento = db.Column(db.String(20))
