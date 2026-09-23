"""Pruebas de seguridad para acceso, sesión, roles y datos sensibles."""

import unittest

from werkzeug.security import check_password_hash

from app.models.cliente import Cliente
from app.models.users import User
from app.test.base import HotelTestCase


class TestSeguridad(HotelTestCase):
    def test_01_password_se_guarda_como_hash(self):
        usuario_id = self.crear_usuario("hash.password", password="Secreto123")

        with self.app.app_context():
            usuario = User.query.get(usuario_id)
            self.assertNotEqual(usuario.password, "Secreto123")
            self.assertTrue(check_password_hash(usuario.password, "Secreto123"))

    def test_02_login_no_distingue_usuario_inexistente_de_password_incorrecto(self):
        self.crear_usuario("usuario.real", password="Correcta123")

        respuesta_existente = self.iniciar_sesion("usuario.real", "Incorrecta123")
        respuesta_inexistente = self.iniciar_sesion("usuario.inexistente", "Incorrecta123")
        mensaje = "Usuario o contraseña incorrectos"

        self.assertEqual(respuesta_existente.status_code, 200)
        self.assertEqual(respuesta_inexistente.status_code, 200)
        self.assertIn(mensaje, respuesta_existente.get_data(as_text=True))
        self.assertIn(mensaje, respuesta_inexistente.get_data(as_text=True))

    def test_03_rutas_administrativas_requieren_autenticacion(self):
        rutas = [
            "/admin/usuarios",
            "/admin/roles-empleados/",
            "/admin/personal-limpieza",
            "/clientes/",
        ]

        for ruta in rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("next=", respuesta.headers["Location"])

    def test_04_cliente_no_puede_simular_otro_rol(self):
        self.crear_usuario("cliente.simulador", cedula=15001)
        self.iniciar_sesion("cliente.simulador")

        respuesta = self.client.get("/simular_rol/recepcionista")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        with self.client.session_transaction() as sesion:
            self.assertNotIn("simulated_role", sesion)

    def test_05_administrador_simula_y_restaura_rol(self):
        usuario_id = self.crear_usuario("admin.simulador", rol="administrador")
        self.iniciar_sesion("admin.simulador")

        simular = self.client.get("/simular_rol/recepcionista")
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion.get("simulated_role"), "recepcionista")
        with self.app.app_context():
            self.assertEqual(User.query.get(usuario_id).real_rol, "administrador")

        restaurar = self.client.get("/simular_rol/restaurar")
        with self.client.session_transaction() as sesion:
            self.assertNotIn("simulated_role", sesion)

        self.assertEqual(simular.status_code, 302)
        self.assertEqual(restaurar.status_code, 302)

    def test_06_simulador_rechaza_rol_desconocido(self):
        self.crear_usuario("admin.rol_desconocido", rol="administrador")
        self.iniciar_sesion("admin.rol_desconocido")

        respuesta = self.client.get("/simular_rol/superusuario")

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Rol no válido")
        with self.client.session_transaction() as sesion:
            self.assertNotIn("simulated_role", sesion)

    def test_07_rol_simulado_no_conserva_permisos_de_administrador(self):
        self.crear_usuario("admin.simula_cliente", rol="administrador")
        self.iniciar_sesion("admin.simula_cliente")
        self.client.get("/simular_rol/cliente")

        respuesta = self.client.get("/admin/usuarios")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_08_recepcionista_no_puede_editar_ni_eliminar_usuarios(self):
        objetivo = self.crear_usuario("objetivo.protegido", cedula=15002)
        self.crear_usuario("recepcion.protegido", rol="recepcionista")
        self.iniciar_sesion("recepcion.protegido")

        editar = self.client.post(
            f"/admin/editar-usuario/{objetivo}", data={"rol": "administrador"}
        )
        eliminar = self.client.post(f"/admin/eliminar-usuario/{objetivo}")

        self.assertEqual(editar.status_code, 302)
        self.assertEqual(eliminar.status_code, 302)
        with self.app.app_context():
            usuario = User.query.get(objetivo)
            self.assertIsNotNone(usuario)
            self.assertEqual(usuario.rol, "cliente")

    @unittest.expectedFailure
    def test_09_perfil_rechaza_nombre_de_usuario_invalido(self):
        usuario_id = self.crear_usuario("perfil.invalido", cedula=15003)
        self.iniciar_sesion("perfil.invalido")

        respuesta = self.client.post(
            "/perfil", data={"usuario": "nombre inválido"}, follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("nombre de usuario")
        with self.app.app_context():
            self.assertEqual(User.query.get(usuario_id).usuario, "perfil.invalido")

    @unittest.expectedFailure
    def test_10_perfil_rechaza_correo_ya_registrado(self):
        self.crear_cliente(15004, email="ocupado@example.com")
        usuario_id = self.crear_usuario(
            "perfil.correo", cedula=15005, email="propio@example.com"
        )
        self.iniciar_sesion("perfil.correo")

        respuesta = self.client.post(
            "/perfil",
            data={"usuario": "perfil.correo", "email": "ocupado@example.com"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("correo electrónico ya está registrado")
        with self.app.app_context():
            self.assertEqual(Cliente.query.get(15005).email, "propio@example.com")

    @unittest.expectedFailure
    def test_11_perfil_rechaza_telefono_invalido(self):
        usuario_id = self.crear_usuario(
            "perfil.telefono", cedula=15006, telefono="3001234567"
        )
        self.iniciar_sesion("perfil.telefono")

        respuesta = self.client.post(
            "/perfil",
            data={"usuario": "perfil.telefono", "telefono": "12"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("teléfono")
        with self.app.app_context():
            cliente = Cliente.query.get(15006)
            self.assertEqual(cliente.telefono, "3001234567")

    def test_12_idioma_solo_acepta_valores_configurados(self):
        self.client.get("/set_language/en")
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion.get("language"), "en")

        self.client.get("/set_language/fr")
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion.get("language"), "en")

    def test_13_hash_de_password_no_se_renderiza_en_pantallas(self):
        objetivo_id = self.crear_usuario("visible.cliente", cedula=15007)
        self.crear_usuario("admin.visible", rol="administrador")
        self.iniciar_sesion("admin.visible")
        with self.app.app_context():
            hash_password = User.query.get(objetivo_id).password

        lista = self.client.get("/admin/usuarios")

        self.assertEqual(lista.status_code, 200)
        self.assertNotIn(hash_password.encode(), lista.data)
