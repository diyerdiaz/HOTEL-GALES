from app import db

class Consumo(db.Model):
    __tablename__ = 'consumo'
    idConsumo = db.Column(db.Integer, primary_key=True)
    idReserva = db.Column(db.Integer, db.ForeignKey('reserva.idReserva'), nullable=False)
    idServicio = db.Column(db.Integer, db.ForeignKey('servicio.idServicio'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Numeric(10, 2))
