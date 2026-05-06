from app import db

class Reserva(db.Model):
    __tablename__ = 'reserva'
    idReserva = db.Column(db.Integer, primary_key=True)
    cedulaCliente = db.Column(db.BigInteger, db.ForeignKey('cliente.cedula'), nullable=False)
    idHabitacion = db.Column(db.Integer, db.ForeignKey('habitacion.idHabitacion'), nullable=False)
    fechaEntrada = db.Column(db.Date, nullable=False)
    fechaSalida = db.Column(db.Date, nullable=False)
    cantidadPersonas = db.Column(db.Integer)
    estadoReserva = db.Column(db.String(20), default='pendiente')
    atendido_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # ID del usuario que atendió
    
    pagos = db.relationship('Pago', backref='reserva', lazy=True)
    facturas = db.relationship('Factura', backref='reserva', lazy=True)
    consumos = db.relationship('Consumo', backref='reserva', lazy=True)
    
    # Relación con el usuario que atendió
    usuario_atendio = db.relationship('User', backref='reservas_atendidas', lazy=True)
