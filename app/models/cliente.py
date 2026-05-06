from app import db

class Cliente(db.Model):
    __tablename__ = 'cliente'
    cedula = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.String(40), nullable=False)
    apellido = db.Column(db.String(40), nullable=False)
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(80))
    direccion = db.Column(db.String(100))
    fechaNacimiento = db.Column(db.Date)
    
    reservas = db.relationship('Reserva', backref='cliente', lazy=True)
