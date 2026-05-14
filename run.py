from app import create_app, db
from app.models.users import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_admin_user():
    """Crea un usuario administrador inicial si no existe ninguno."""
    admin_user = User.query.filter_by(rol='administrador').first()
    if not admin_user:
        username = app.config.get('ADMIN_USERNAME')
        password = app.config.get('ADMIN_PASSWORD')
        
        nuevo_admin = User(
            usuario=username,
            password=generate_password_hash(password),
            rol='administrador'
        )
        db.session.add(nuevo_admin)
        db.session.commit()
        print(f"[*] Usuario administrador '{username}' creado exitosamente.")

with app.app_context():
    try:
        db.create_all()
        create_admin_user()
    except Exception as e:
        print(f"[!] Error crítico al inicializar la base de datos: {e}")
        print("[!] La aplicación intentará continuar, pero algunas funciones pueden fallar.")

if __name__ == '__main__':
    #+++++++++++socketio.run(app, host="0.0.0.0", port=80, debug=True, allow_unsafe_werkzeug=True)
    app.run(host="127.0.0.1", port=5001, debug=True)