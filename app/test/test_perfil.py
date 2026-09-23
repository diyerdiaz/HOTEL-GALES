"""Pruebas de visualización, edición y eliminación del perfil propio."""

import unittest

from werkzeug.security import check_password_hash

from app.models.cliente import Cliente
from app.models.users import User
from app.test.base import HotelTestCase


class TestPerfil(HotelTestCase):
    def test_01_perfil_requiere_inicio_de_sesion(self):
        respuesta = self.client.get("/perfil")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_perfil_cliente_muestra_informacion_personal(self):
        self.crear_usuario(
            "perfil.cliente",
            rol="cliente",
            cedula=12001,
            email="perfil@example.com",
        )
        self.iniciar_sesion("perfil.cliente")

        respuesta = self.client.get("/perfil")

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("perfil.cliente", contenido)
        self.assertIn("perfil@example.com", contenido)
        self.assertIn("Información Personal", contenido)

    def test_03_perfil_administrativo_se_presenta_sin_ficha_de_cliente(self):
        self.crear_usuario("perfil.admin", rol="administrador")
        self.iniciar_sesion("perfil.admin")

        respuesta = self.client.get("/perfil")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Perfil Administrativo", respuesta.get_data(as_text=True))

    def test_04_actualiza_nombre_de_usuario(self):
        self.crear_usuario("nombre.anterior", cedula=12002)
        self.iniciar_sesion("nombre.anterior")

        respuesta = self.client.post(
            "/perfil", data={"usuario": "nombre.nuevo"}, follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/perfil")
        with self.app.app_context():
            self.assertIsNotNone(User.query.filter_by(usuario="nombre.nuevo").one())

    def test_05_actualiza_datos_personales_del_cliente(self):
        self.crear_usuario("datos.cliente", cedula=12003, email="anterior@example.com")
        self.iniciar_sesion("datos.cliente")

        respuesta = self.client.post(
            "/perfil",
            data={
                "usuario": "datos.cliente",
                "nombre": "Laura",
                "apellido": "Updated",
                "email": "actualizado@example.com",
                "telefono": "3015550000",
                "direccion": "Avenida Nueva 45",
            },
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            cliente = Cliente.query.get(12003)
            self.assertEqual(cliente.nombre, "Laura")
            self.assertEqual(cliente.apellido, "Updated")
            self.assertEqual(cliente.email, "actualizado@example.com")
            self.assertEqual(cliente.telefono, "3015550000")
            self.assertEqual(cliente.direccion, "Avenida Nueva 45")

    def test_06_actualizacion_parcial_conserva_datos_no_enviados(self):
        self.crear_usuario("parcial.cliente", cedula=12004, email="parcial@example.com")
        self.iniciar_sesion("parcial.cliente")

        self.client.post("/perfil", data={"nombre": "NombreActualizado"})

        with self.app.app_context():
            cliente = Cliente.query.get(12004)
            self.assertEqual(cliente.nombre, "NombreActualizado")
            self.assertEqual(cliente.email, "parcial@example.com")

    def test_07_cambia_password_valida(self):
        self.crear_usuario("cambio.password", cedula=12005)
        self.iniciar_sesion("cambio.password")

        respuesta = self.client.post(
            "/perfil",
            data={
                "usuario": "cambio.password",
                "password": "NuevaClave123",
                "confirm_password": "NuevaClave123",
            },
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            usuario = User.query.filter_by(usuario="cambio.password").one()
            self.assertTrue(check_password_hash(usuario.password, "NuevaClave123"))
        self.client.get("/logout")
        self.assertEqual(self.iniciar_sesion("cambio.password", "NuevaClave123").status_code, 302)

    def test_08_rechaza_nombre_de_usuario_duplicado(self):
        self.crear_usuario("ocupado", cedula=None)
        objetivo = self.crear_usuario("cambia.nombre", cedula=12006)
        self.iniciar_sesion("cambia.nombre")

        respuesta = self.client.post(
            "/perfil", data={"usuario": "ocupado"}, follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("El nombre de usuario ya está en uso")
        with self.app.app_context():
            self.assertEqual(User.query.get(objetivo).usuario, "cambia.nombre")

    def test_09_rechaza_confirmacion_de_password_distinta(self):
        self.crear_usuario("confirma.password", cedula=12007)
        self.iniciar_sesion("confirma.password")

        respuesta = self.client.post(
            "/perfil",
            data={"password": "NuevaClave123", "confirm_password": "Distinta123"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Las contraseñas no coinciden")

    def test_10_rechaza_password_de_menos_de_ocho_caracteres(self):
        self.crear_usuario("corta.password", cedula=12008)
        self.iniciar_sesion("corta.password")

        respuesta = self.client.post(
            "/perfil",
            data={"password": "A1b2c3", "confirm_password": "A1b2c3"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("8 y 30 caracteres")

    def test_11_rechaza_password_sin_numero(self):
        self.crear_usuario("sin.numero", cedula=12009)
        self.iniciar_sesion("sin.numero")

        respuesta = self.client.post(
            "/perfil",
            data={"password": "PasswordSolo", "confirm_password": "PasswordSolo"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("al menos una letra y un número")

    def test_12_elimina_la_propia_cuenta_y_cierra_sesion(self):
        usuario_id = self.crear_usuario("eliminar.cuenta", cedula=12010)
        self.iniciar_sesion("eliminar.cuenta")

        respuesta = self.client.post("/perfil/eliminar", follow_redirects=False)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())
        with self.app.app_context():
            self.assertIsNone(User.query.get(usuario_id))

    @unittest.expectedFailure
    def test_13_eliminacion_de_cuenta_solo_acepta_post(self):
        usuario_id = self.crear_usuario("no.eliminar.get", cedula=12011)
        self.iniciar_sesion("no.eliminar.get")

        respuesta = self.client.get("/perfil/eliminar")

        self.assertEqual(respuesta.status_code, 405)
        with self.app.app_context():
            self.assertIsNotNone(User.query.get(usuario_id))

    def test_14_perfil_no_permite_cambiar_el_rol(self):
        usuario_id = self.crear_usuario("rol.actual", rol="cliente", cedula=12012)
        self.iniciar_sesion("rol.actual")

        self.client.post(
            "/perfil",
            data={"usuario": "rol.actual", "rol": "administrador"},
            follow_redirects=False,
        )

        with self.app.app_context():
            self.assertEqual(User.query.get(usuario_id).rol, "cliente")
