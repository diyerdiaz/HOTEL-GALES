from app import create_app, db
from app.models.users import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Asegurarse de que las tablas existan
    db.create_all()
    
    username = "admin"
    password = "admin123"
    
    user = User.query.filter_by(usuario=username).first()
    if user:
        print(f"El usuario '{username}' ya existe. Actualizando contraseña...")
        user.password = generate_password_hash(password)
        user.rol = 'administrador'
    else:
        print(f"Creando usuario '{username}'...")
        user = User(
            usuario=username,
            password=generate_password_hash(password),
            rol='administrador'
        )
        db.session.add(user)
    
    try:
        db.session.commit()
        print(f"Éxito: Usuario '{username}' configurado como administrador con contraseña '{password}'.")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
