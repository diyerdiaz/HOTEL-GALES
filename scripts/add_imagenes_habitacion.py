import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, text
from app import create_app, db

# Agrega las columnas imagen1, imagen2 e imagen3 a la tabla habitacion
# Funciona tanto con SQLite (local) como con PostgreSQL (producción)
app = create_app()

with app.app_context():
    columnas = [c['name'] for c in inspect(db.engine).get_columns('habitacion')]
    with db.engine.begin() as conn:
        for col in ('imagen1', 'imagen2', 'imagen3'):
            if col in columnas:
                print(f"Column '{col}' already exists in 'habitacion' table")
            else:
                conn.execute(text(f'ALTER TABLE habitacion ADD COLUMN "{col}" VARCHAR(255)'))
                print(f"Column '{col}' added successfully to 'habitacion' table")
