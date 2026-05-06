import os
import sys

# Agregar el directorio raíz al path para que las importaciones de 'app' funcionen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.users import User
from app.models.rolempleado import RolEmpleado
from app.models.cliente import Cliente
from app.models.empleado import Empleado
from werkzeug.security import generate_password_hash

def initialize_database():
    app = create_app()
    with app.app_context():
        print("Iniciando creación de tablas...")
        # Crear todas las tablas definidas en los modelos
        db.create_all()
        print("Tablas creadas correctamente.")

        # 1. Crear roles básicos en RolEmpleado si no existen
        roles_basicos = [
            ('Administrador', 'Control total del sistema'),
            ('Recepcionista', 'Gestión de huéspedes y reservas'),
            ('Servicio de Limpieza', 'Mantenimiento y aseo')
        ]

        for nombre, descripcion in roles_basicos:
            rol = RolEmpleado.query.filter_by(nombreRol=nombre).first()
            if not rol:
                nuevo_rol = RolEmpleado(nombreRol=nombre, descripcionRol=descripcion)
                db.session.add(nuevo_rol)
                print(f"Rol '{nombre}' creado.")
        
        db.session.commit()

        # 2. Crear usuario administrador "Juan"
        admin_usuario = 'Juan'
        admin_password = 'Juan1234'
        
        user = User.query.filter_by(usuario=admin_usuario).first()
        if not user:
            print(f"Creando usuario administrador {admin_usuario}...")
            nuevo_admin = User(
                usuario=admin_usuario,
                password=generate_password_hash(admin_password),
                rol='administrador'
            )
            db.session.add(nuevo_admin)
            db.session.commit()
            print(f"Usuario {admin_usuario} creado exitosamente.")
        else:
            print(f"El usuario {admin_usuario} ya existe.")

        print("Finalización de la configuración de la base de datos.")

if __name__ == "__main__":
    initialize_database()
