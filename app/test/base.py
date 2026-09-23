"""Utilidades compartidas por las pruebas de la Persona 1.

La base de datos se crea en un directorio temporal para que las pruebas nunca
modifiquen la base de datos configurada para desarrollo o producción.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from config import Config


class HotelTestCase(unittest.TestCase):
    """Clase base con una aplicación Flask aislada para cada archivo de pruebas."""

    PASSWORD_PRUEBA = "Prueba123"

    @classmethod
    def setUpClass(cls):
        # Importar después de crear el parche evita que una configuración real
        # pueda ser utilizada accidentalmente por la aplicación de pruebas.
        from app import create_app

        cls._temporary_directory = TemporaryDirectory(prefix="hotel-gales-pruebas-")
        database_path = Path(cls._temporary_directory.name) / "pruebas.sqlite3"
        database_uri = f"sqlite:///{database_path}"

        cls._database_patch = patch.object(
            Config, "SQLALCHEMY_DATABASE_URI", database_uri
        )
        cls._secret_patch = patch.object(
            Config, "SECRET_KEY", "clave-exclusiva-para-pruebas"
        )
        cls._database_patch.start()
        cls._secret_patch.start()

        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
            SERVER_NAME="localhost",
            WTF_CSRF_ENABLED=False,
            BABEL_DEFAULT_LOCALE="es",
        )

    @classmethod
    def tearDownClass(cls):
        from app import db

        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

        cls._database_patch.stop()
        cls._secret_patch.stop()
        cls._temporary_directory.cleanup()

    def setUp(self):
        from app import db

        self.client = self.app.test_client()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    def tearDown(self):
        from app import db

        with self.app.app_context():
            db.session.remove()

    def iniciar_sesion(self, usuario, password=None):
        """Inicia sesión usando el formulario HTTP real del proyecto."""
        if password is None:
            password = self.PASSWORD_PRUEBA
        return self.client.post(
            "/",
            data={"usuario": usuario, "password": password},
            follow_redirects=False,
        )

    def obtener_id_de_usuario_autenticado(self):
        with self.client.session_transaction() as sesion:
            return sesion.get("_user_id")

    def mensajes_flash(self):
        """Devuelve mensajes flash que todavía no fueron consumidos por una vista."""
        with self.client.session_transaction() as sesion:
            return [mensaje for _, mensaje in sesion.get("_flashes", [])]

    def assert_contiene_flash(self, texto_esperado):
        self.assertTrue(
            any(texto_esperado in mensaje for mensaje in self.mensajes_flash()),
            f"No se encontró el mensaje flash esperado: {texto_esperado!r}",
        )

    def crear_cliente(
        self,
        cedula,
        nombre="Ana",
        apellido="Prueba",
        email=None,
        telefono="3001234567",
        direccion="Calle 1 #2-3",
    ):
        from app import db
        from app.models.cliente import Cliente

        cliente = Cliente(
            cedula=int(cedula),
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            direccion=direccion,
        )
        with self.app.app_context():
            db.session.add(cliente)
            db.session.commit()
        return int(cedula)

    def crear_usuario(
        self,
        usuario="usuario.prueba",
        rol="cliente",
        password=None,
        cedula=None,
        email=None,
        telefono="3001234567",
    ):
        """Crea un usuario y, cuando se proporciona cédula, su ficha de cliente."""
        from app import db
        from app.models.cliente import Cliente
        from app.models.users import User
        from werkzeug.security import generate_password_hash

        if password is None:
            password = self.PASSWORD_PRUEBA

        with self.app.app_context():
            if cedula is not None:
                cliente = Cliente.query.get(int(cedula))
                if cliente is None:
                    cliente = Cliente(
                        cedula=int(cedula),
                        nombre="Personal",
                        apellido="Prueba",
                        email=email,
                        telefono=telefono,
                    )
                    db.session.add(cliente)

            user = User(
                usuario=usuario,
                password=generate_password_hash(password),
                rol=rol,
                cedula=int(cedula) if cedula is not None else None,
            )
            db.session.add(user)
            db.session.commit()
            return user.id

    def crear_rol_empleado(self, nombre="Recepcionista", descripcion="Atención al huésped"):
        from app import db
        from app.models.rolempleado import RolEmpleado

        with self.app.app_context():
            rol = RolEmpleado(nombreRol=nombre, descripcionRol=descripcion)
            db.session.add(rol)
            db.session.commit()
            return rol.idRolEmpleado
