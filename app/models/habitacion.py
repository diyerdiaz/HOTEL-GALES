from app import db

class Habitacion(db.Model):
    __tablename__ = 'habitacion'
    idHabitacion = db.Column(db.Integer, primary_key=True)
    numeroHabitacion = db.Column(db.Integer, nullable=False)
    idTipoHabitacion = db.Column(db.Integer, db.ForeignKey('tipohabitacion.idTipoHabitacion'), nullable=False)
    precioNoche = db.Column(db.Numeric(10, 2), nullable=False)
    estadoHabitacion = db.Column(db.String(20), default='disponible')
    imagen1 = db.Column(db.String(255), nullable=True)
    imagen2 = db.Column(db.String(255), nullable=True)
    imagen3 = db.Column(db.String(255), nullable=True)
    
    reservas = db.relationship('Reserva', backref='habitacion', lazy=True)
    mantenimientos = db.relationship('MantenimientoHabitacion', backref='habitacion_info', lazy=True)

    @property
    def imagenes(self):
        """Lista de imágenes cargadas (sin espacios vacíos)"""
        return [img for img in (self.imagen1, self.imagen2, self.imagen3) if img]
