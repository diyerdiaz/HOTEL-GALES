from app import db

class TipoServicio(db.Model):
    __tablename__ = 'tiposervicio'
    idTipoServicio = db.Column(db.Integer, primary_key=True)
    nombreTipoServicio = db.Column(db.String(40), nullable=False)
    
    servicios = db.relationship('Servicio', backref='tipo', lazy=True)
