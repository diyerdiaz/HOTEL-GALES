"""Pruebas de administración y gestión de usuarios."""

from datetime import date

from app.models.cliente import Cliente
from app.models.habitacion import Habitacion
from app.models.reserva import Reserva
from app.models.tipohabitacion import TipoHabitacion
from app.models.users import User
from app.test.base import HotelTestCase


class TestUsuarios(HotelTestCase):
    def datos_usuario_validos(self, **cambios):
        datos = {
            "cedula": "13001",
            "nombre": "Carlos",
            "apellido": "Pérez",
            "email": "carlos@example.com",
            "telefono": "3001112223",
            "direccion": "Calle 10 #20-30",
            "usuario": "carlos.perez",
            "password": "Temporal123",
            "confirm_password": "Temporal123",
            "rol": "cliente",
            "origen": "usuarios",
        }
        datos.update(cambios)
        return datos

    def crear_reserva_para_cliente(self, cedula):
        from app import db

        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo="Estándar", descripcionTipo="Prueba")
            db.session.add(tipo)
            db.session.flush()
            habitacion = Habitacion(
                numeroHabitacion=901,
                idTipoHabitacion=tipo.idTipoHabitacion,
                precioNoche=150000,
                estadoHabitacion="ocupada",
            )
            db.session.add(habitacion)
            db.session.flush()
            reserva = Reserva(
                cedulaCliente=cedula,
                idHabitacion=habitacion.idHabitacion,
                fechaEntrada=date.today(),
                fechaSalida=date.today(),
                cantidadPersonas=1,
                estadoReserva="confirmada",
            )
            db.session.add(reserva)
            db.session.commit()

    def test_01_lista_usuarios_requiere_autenticacion(self):
        respuesta = self.client.get("/admin/usuarios")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_cliente_no_puede_gestionar_usuarios(self):
        self.crear_usuario("cliente.restringido", cedula=13002)
        self.iniciar_sesion("cliente.restringido")

        respuesta = self.client.get("/admin/usuarios")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_03_recepcionista_puede_consultar_lista_de_clientes(self):
        self.crear_usuario("recepcion.consulta", rol="recepcionista")
        self.iniciar_sesion("recepcion.consulta")

        respuesta = self.client.get("/admin/usuarios")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Historial de Clientes", respuesta.get_data(as_text=True))

    def test_04_administrador_puede_consultar_lista_de_clientes(self):
        self.crear_usuario("admin.lista", rol="administrador")
        self.iniciar_sesion("admin.lista")

        respuesta = self.client.get("/admin/usuarios")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Historial de Clientes", respuesta.get_data(as_text=True))

    def test_05_lista_muestra_solo_usuarios_rol_cliente(self):
        self.crear_usuario("cliente.visible", cedula=13003)
        self.crear_usuario("recepcion.oculto", rol="recepcionista", cedula=13004)
        self.crear_usuario("admin.actual", rol="administrador")
        self.iniciar_sesion("admin.actual")

        respuesta = self.client.get("/admin/usuarios")
        contenido = respuesta.get_data(as_text=True)

        self.assertIn("cliente.visible", contenido)
        self.assertNotIn("recepcion.oculto", contenido)

    def test_06_administrador_crea_cliente(self):
        self.crear_usuario("admin.crea", rol="administrador")
        self.iniciar_sesion("admin.crea")

        respuesta = self.client.post(
            "/admin/usuarios", data=self.datos_usuario_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/admin/usuarios")
        with self.app.app_context():
            cliente = Cliente.query.get(13001)
            usuario = User.query.filter_by(usuario="carlos.perez").one()
            self.assertIsNotNone(cliente)
            self.assertEqual(usuario.rol, "cliente")

    def test_07_creacion_normaliza_el_correo(self):
        self.crear_usuario("admin.correo", rol="administrador")
        self.iniciar_sesion("admin.correo")
        datos = self.datos_usuario_validos(email="  CARLOS@EXAMPLE.COM  ")

        self.client.post("/admin/usuarios", data=datos)

        with self.app.app_context():
            self.assertEqual(Cliente.query.get(13001).email, "carlos@example.com")

    def test_08_recepcionista_puede_crear_cliente(self):
        self.crear_usuario("recepcion.crea", rol="recepcionista")
        self.iniciar_sesion("recepcion.crea")

        respuesta = self.client.post(
            "/admin/usuarios", data=self.datos_usuario_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertIsNotNone(User.query.filter_by(usuario="carlos.perez").one())

    def test_09_recepcionista_no_puede_crear_personal(self):
        self.crear_usuario("recepcion.sin_personal", rol="recepcionista")
        self.iniciar_sesion("recepcion.sin_personal")
        datos = self.datos_usuario_validos(
            rol="recepcionista", origen="empleados", usuario="recepcion.nuevo"
        )

        respuesta = self.client.post("/admin/usuarios", data=datos, follow_redirects=False)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/admin/empleados/")
        self.assert_contiene_flash("No tienes permiso para crear personal")
        with self.app.app_context():
            self.assertIsNone(User.query.filter_by(usuario="recepcion.nuevo").first())

    def test_10_administrador_crea_personal_desde_empleados(self):
        self.crear_usuario("admin.personal", rol="administrador")
        self.iniciar_sesion("admin.personal")
        datos = self.datos_usuario_validos(
            rol="recepcionista", origen="empleados", usuario="recepcion.nuevo"
        )

        respuesta = self.client.post("/admin/usuarios", data=datos, follow_redirects=False)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/admin/empleados/")
        with self.app.app_context():
            usuario = User.query.filter_by(usuario="recepcion.nuevo").one()
            self.assertEqual(usuario.rol, "recepcionista")

    def test_11_rechaza_datos_invalidos_al_crear_usuario(self):
        self.crear_usuario("admin.validacion", rol="administrador")
        self.iniciar_sesion("admin.validacion")
        casos = {
            "campos_requeridos": {"nombre": ""},
            "cedula": {"cedula": "ABC"},
            "correo": {"email": "correo-malo"},
            "telefono": {"telefono": "12"},
            "usuario": {"usuario": "a b"},
            "password_corta": {"password": "A1b", "confirm_password": "A1b"},
            "password_sin_numero": {
                "password": "PasswordOnly",
                "confirm_password": "PasswordOnly",
            },
            "confirmacion": {"confirm_password": "OtraClave123"},
            "rol": {"rol": "superusuario"},
        }

        for indice, (nombre_caso, cambios) in enumerate(casos.items(), start=1):
            with self.subTest(caso=nombre_caso):
                datos = self.datos_usuario_validos(
                    cedula=str(13100 + indice),
                    usuario=f"invalido.{indice}",
                    email=f"invalido{indice}@example.com",
                )
                datos.update(cambios)
                respuesta = self.client.post(
                    "/admin/usuarios", data=datos, follow_redirects=False
                )
                self.assertEqual(respuesta.status_code, 302)
                with self.app.app_context():
                    self.assertIsNone(
                        User.query.filter_by(usuario=datos["usuario"]).first()
                    )

    def test_12_rechaza_usuario_duplicado(self):
        self.crear_usuario("carlos.perez", cedula=13200)
        self.crear_usuario("admin.duplicado", rol="administrador")
        self.iniciar_sesion("admin.duplicado")

        respuesta = self.client.post(
            "/admin/usuarios", data=self.datos_usuario_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("El usuario ya existe")

    def test_13_rechaza_correo_de_cliente_duplicado(self):
        self.crear_usuario("ocupado.correo", cedula=13201, email="carlos@example.com")
        self.crear_usuario("admin.email", rol="administrador")
        self.iniciar_sesion("admin.email")

        respuesta = self.client.post(
            "/admin/usuarios", data=self.datos_usuario_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("El correo electrónico ya está registrado")

    def test_14_administrador_actualiza_rol(self):
        objetivo = self.crear_usuario("cambio.rol", cedula=13202)
        self.crear_usuario("admin.edita", rol="administrador")
        self.iniciar_sesion("admin.edita")

        respuesta = self.client.post(
            f"/admin/editar-usuario/{objetivo}",
            data={"rol": "recepcionista", "origen": "usuarios"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertEqual(User.query.get(objetivo).rol, "recepcionista")

    def test_15_rechaza_rol_invalido_al_editar(self):
        objetivo = self.crear_usuario("rol.invalido", rol="cliente", cedula=13203)
        self.crear_usuario("admin.rol_invalido", rol="administrador")
        self.iniciar_sesion("admin.rol_invalido")

        respuesta = self.client.post(
            f"/admin/editar-usuario/{objetivo}",
            data={"rol": "superusuario"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Rol inválido")
        with self.app.app_context():
            self.assertEqual(User.query.get(objetivo).rol, "cliente")

    def test_16_recepcionista_no_puede_editar_rol(self):
        objetivo = self.crear_usuario("rol.protegido", rol="cliente", cedula=13204)
        self.crear_usuario("recepcion.edita", rol="recepcionista")
        self.iniciar_sesion("recepcion.edita")

        respuesta = self.client.post(
            f"/admin/editar-usuario/{objetivo}",
            data={"rol": "administrador"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Solo el administrador")
        with self.app.app_context():
            self.assertEqual(User.query.get(objetivo).rol, "cliente")

    def test_17_administrador_elimina_usuario_y_cliente_sin_relaciones(self):
        objetivo = self.crear_usuario("eliminar.objetivo", cedula=13205)
        self.crear_usuario("admin.elimina", rol="administrador")
        self.iniciar_sesion("admin.elimina")

        respuesta = self.client.post(
            f"/admin/eliminar-usuario/{objetivo}",
            data={"origen": "usuarios"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(User.query.get(objetivo))
            self.assertIsNone(Cliente.query.get(13205))

    def test_18_administrador_no_puede_eliminar_su_propia_cuenta(self):
        admin_id = self.crear_usuario("admin.protegido", rol="administrador")
        self.iniciar_sesion("admin.protegido")

        respuesta = self.client.post(
            f"/admin/eliminar-usuario/{admin_id}",
            data={"origen": "usuarios"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("No puedes eliminarte a ti mismo")
        with self.app.app_context():
            self.assertIsNotNone(User.query.get(admin_id))

    def test_19_eliminar_usuario_conserva_cliente_con_reservas(self):
        objetivo = self.crear_usuario("cliente.reservas", cedula=13206)
        self.crear_reserva_para_cliente(13206)
        self.crear_usuario("admin.historial", rol="administrador")
        self.iniciar_sesion("admin.historial")

        self.client.post(
            f"/admin/eliminar-usuario/{objetivo}",
            data={"origen": "usuarios"},
            follow_redirects=False,
        )

        with self.app.app_context():
            self.assertIsNone(User.query.get(objetivo))
            self.assertIsNotNone(Cliente.query.get(13206))

    def test_20_usuario_inexistente_devuelve_404(self):
        self.crear_usuario("admin.inexistente", rol="administrador")
        self.iniciar_sesion("admin.inexistente")

        respuesta = self.client.post(
            "/admin/editar-usuario/999999", data={"rol": "cliente"}
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_21_administrador_consulta_historial_de_recepcionistas(self):
        self.crear_usuario("recep.historial", rol="recepcionista", cedula=13207)
        self.crear_usuario("admin.recep", rol="administrador")
        self.iniciar_sesion("admin.recep")

        respuesta = self.client.get("/admin/recepcionistas?search=recep")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("recep.historial", respuesta.get_data(as_text=True))

    def test_22_historial_rechaza_usuario_que_no_es_recepcionista(self):
        cliente_id = self.crear_usuario("cliente.no_recep", cedula=13208)
        self.crear_usuario("admin.historial_rol", rol="administrador")
        self.iniciar_sesion("admin.historial_rol")

        respuesta = self.client.get(f"/admin/recepcionista/{cliente_id}/historial")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/admin/recepcionistas")
        self.assert_contiene_flash("no es un recepcionista")

    def test_23_administrador_consulta_historial_de_limpieza(self):
        self.crear_usuario(
            "limpieza.historial", rol="servicio_limpieza", cedula=13209
        )
        self.crear_usuario("admin.limpieza", rol="administrador")
        self.iniciar_sesion("admin.limpieza")

        respuesta = self.client.get("/admin/personal-limpieza?search=limpieza")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("limpieza.historial", respuesta.get_data(as_text=True))
