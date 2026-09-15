from app import db
from datetime import datetime

class Notificacion(db.Model):
    __tablename__ = 'notificacion'
    idNotificacion = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'reserva', 'cancelacion', 'checkin', 'checkout', etc.
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(500))  # Enlace opcional a la reserva relacionada
    
    usuario = db.relationship('User', backref=db.backref('notificaciones', cascade='all, delete-orphan'), lazy=True)
    
    def __repr__(self):
        return f'<Notificacion {self.idNotificacion} - {self.tipo} - {self.titulo}>'
    
    @staticmethod
    def crear_notificacion(usuario_id, tipo, titulo, mensaje, link=None):
        """Crea una nueva notificación para un usuario"""
        notificacion = Notificacion(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            link=link
        )
        db.session.add(notificacion)
        db.session.commit()
        return notificacion
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        db.session.commit()
