from app import db
from datetime import datetime

class Pago(db.Model):
    __tablename__ = 'pago'
    idPago = db.Column(db.Integer, primary_key=True)
    idReserva = db.Column(db.Integer, db.ForeignKey('reserva.idReserva'), nullable=False)
    fechaPago = db.Column(db.DateTime, default=datetime.utcnow)
    metodoPago = db.Column(db.String(30))
    valorPago = db.Column(db.Numeric(10, 2), nullable=False)
