from app import db

class Servicio(db.Model):
    __tablename__ = 'servicio'
    idServicio = db.Column(db.Integer, primary_key=True)
    nombreServicio = db.Column(db.String(50), nullable=False)
    idTipoServicio = db.Column(db.Integer, db.ForeignKey('tiposervicio.idTipoServicio'), nullable=False)
    precioServicio = db.Column(db.Numeric(10, 2), nullable=False)
    
    consumos = db.relationship('Consumo', backref='servicio', lazy=True)
