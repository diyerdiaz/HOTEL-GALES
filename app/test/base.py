"""Utilidades compartidas por las pruebas de software.

La base de datos se crea en un directorio temporal para que las pruebas nunca
modifiquen la base de datos configurada para desarrollo o producción.
"""

from datetime import date, timedelta
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
        salario=0,
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
                salario=salario,
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

    def crear_habitacion(
        self,
        numero=101,
        precio=200000,
        estado="disponible",
        tipo_nombre="Estándar",
    ):
        from app import db
        from app.models.habitacion import Habitacion
        from app.models.tipohabitacion import TipoHabitacion

        with self.app.app_context():
            tipo = TipoHabitacion.query.filter_by(nombreTipo=tipo_nombre).first()
            if tipo is None:
                tipo = TipoHabitacion(
                    nombreTipo=tipo_nombre, descripcionTipo="Tipo de prueba"
                )
                db.session.add(tipo)
                db.session.flush()
            habitacion = Habitacion(
                numeroHabitacion=numero,
                idTipoHabitacion=tipo.idTipoHabitacion,
                precioNoche=precio,
                estadoHabitacion=estado,
            )
            db.session.add(habitacion)
            db.session.commit()
            return habitacion.idHabitacion

    def crear_reserva(
        self,
        cedula,
        habitacion_id,
        estado="confirmada",
        fecha_entrada=None,
        fecha_salida=None,
        cantidad_personas=1,
    ):
        from app import db
        from app.models.reserva import Reserva

        if fecha_entrada is None:
            fecha_entrada = date.today()
        if fecha_salida is None:
            fecha_salida = fecha_entrada + timedelta(days=2)

        with self.app.app_context():
            reserva = Reserva(
                cedulaCliente=int(cedula),
                idHabitacion=habitacion_id,
                fechaEntrada=fecha_entrada,
                fechaSalida=fecha_salida,
                cantidadPersonas=cantidad_personas,
                estadoReserva=estado,
            )
            db.session.add(reserva)
            db.session.commit()
            return reserva.idReserva

    def crear_factura(self, reserva_id, total=400000, fecha_emision=None):
        from app import db
        from app.models.factura import Factura

        with self.app.app_context():
            factura = Factura(
                idReserva=reserva_id,
                totalFactura=total,
                fechaFactura=fecha_emision,
            )
            db.session.add(factura)
            db.session.commit()
            return factura.idFactura

    def crear_pago(
        self,
        reserva_id,
        metodo="tarjeta",
        valor=200000,
    ):
        from app import db
        from app.models.pago import Pago

        with self.app.app_context():
            pago = Pago(
                idReserva=reserva_id,
                metodoPago=metodo,
                valorPago=valor,
            )
            db.session.add(pago)
            db.session.commit()
            return pago.idPago

    def crear_servicio(
        self,
        nombre="Desayuno buffet",
        precio=35000,
        tipo_nombre="Alimentación",
    ):
        from app import db
        from app.models.servicio import Servicio
        from app.models.tiposervicio import TipoServicio

        with self.app.app_context():
            tipo = TipoServicio.query.filter_by(
                nombreTipoServicio=tipo_nombre
            ).first()
            if tipo is None:
                tipo = TipoServicio(nombreTipoServicio=tipo_nombre)
                db.session.add(tipo)
                db.session.flush()
            servicio = Servicio(
                nombreServicio=nombre,
                idTipoServicio=tipo.idTipoServicio,
                precioServicio=precio,
            )
            db.session.add(servicio)
            db.session.commit()
            return servicio.idServicio

    def crear_consumo(
        self,
        reserva_id,
        servicio_id,
        cantidad=2,
        subtotal=70000,
    ):
        from app import db
        from app.models.consumo import Consumo

        with self.app.app_context():
            consumo = Consumo(
                idReserva=reserva_id,
                idServicio=servicio_id,
                cantidad=cantidad,
                subtotal=subtotal,
            )
            db.session.add(consumo)
            db.session.commit()
            return consumo.idConsumo

    def crear_notificacion(
        self,
        usuario_id,
        titulo="Reserva creada",
        mensaje="La reserva fue creada correctamente.",
        leida=False,
        link=None,
    ):
        from app import db
        from app.models.notificacion import Notificacion

        with self.app.app_context():
            notificacion = Notificacion(
                usuario_id=usuario_id,
                tipo="prueba",
                titulo=titulo,
                mensaje=mensaje,
                leida=leida,
                link=link,
            )
            db.session.add(notificacion)
            db.session.commit()
            return notificacion.idNotificacion

    def crear_comentario(
        self,
        habitacion_id,
        cedula,
        calificacion=5,
        texto="La habitación fue muy cómoda y limpia.",
    ):
        from app import db
        from app.models.comentario import Comentario

        with self.app.app_context():
            comentario = Comentario(
                idHabitacion=habitacion_id,
                cedulaCliente=int(cedula),
                calificacion=calificacion,
                comentario=texto,
            )
            db.session.add(comentario)
            db.session.commit()
            return comentario.idComentario
