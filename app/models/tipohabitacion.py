from app import db

class TipoHabitacion(db.Model):
    __tablename__ = 'tipohabitacion'
    idTipoHabitacion = db.Column(db.Integer, primary_key=True)
    nombreTipo = db.Column(db.String(30), nullable=False)
    descripcionTipo = db.Column(db.String(100))
    
    habitaciones = db.relationship('Habitacion', backref='tipo', lazy=True)
