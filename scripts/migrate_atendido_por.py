"""
Script de migración para agregar el campo 'atendido_por' a la tabla de reservas.
Este script es necesario para actualizar la base de datos existente con el nuevo campo.
"""

import os
import sys

# Agregar el directorio raíz al path para que las importaciones de 'app' funcionen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.reserva import Reserva

def migrate():
    app = create_app()
    
    with app.app_context():
        # Verificar si la columna ya existe
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('reserva')]
        
        if 'atendido_por' in columns:
            print("El campo 'atendido_por' ya existe en la tabla 'reserva'. No se requiere migración.")
            return
        
        # Agregar la nueva columna
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE reserva ADD COLUMN atendido_por INTEGER"))
                conn.execute(db.text("ALTER TABLE reserva ADD CONSTRAINT fk_reserva_atendido_por FOREIGN KEY (atendido_por) REFERENCES users(id)"))
                conn.commit()
            print("Migración exitosa: Campo 'atendido_por' agregado a la tabla 'reserva'.")
        except Exception as e:
            print(f"Error durante la migración: {e}")
            # Si falla la restricción, intentar sin ella
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE reserva ADD COLUMN atendido_por INTEGER"))
                    conn.commit()
                print("Migración parcial exitosa: Campo 'atendido_por' agregado sin restricción de clave foránea.")
            except Exception as e2:
                print(f"Error crítico: {e2}")

if __name__ == '__main__':
    migrate()
