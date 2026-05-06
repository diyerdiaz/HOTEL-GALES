from app import db
from datetime import datetime

class TareaLimpieza(db.Model):
    __tablename__ = 'tarea_limpieza'
    
    idTarea = db.Column(db.Integer, primary_key=True)
    idHabitacion = db.Column(db.Integer, db.ForeignKey('habitacion.idHabitacion'), nullable=False)
    idPersonal = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instrucciones = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, en curso, finalizado
    fechaAsignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fechaFinalizacion = db.Column(db.DateTime, nullable=True)

    # Relaciones
    habitacion = db.relationship('Habitacion', backref='tareas_limpieza')
    personal = db.relationship('User', backref='tareas_asignadas')
