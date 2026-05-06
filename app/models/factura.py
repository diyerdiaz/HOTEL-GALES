from app import db
from datetime import datetime

class Factura(db.Model):
    __tablename__ = 'factura'
    idFactura = db.Column(db.Integer, primary_key=True)
    idReserva = db.Column(db.Integer, db.ForeignKey('reserva.idReserva'), nullable=False)
    fechaFactura = db.Column(db.DateTime, default=datetime.utcnow)
    totalFactura = db.Column(db.Numeric(12, 2), nullable=False)
