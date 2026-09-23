"""Pruebas de autenticación, registro y recuperación de contraseña."""

from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from app.models.cliente import Cliente
from app.models.password_reset import PasswordResetToken
from app.models.users import User
from app.test.base import HotelTestCase


class TestAutenticacion(HotelTestCase):
    def datos_registro_validos(self, **cambios):
        datos = {
            "cedula": "12345678",
            "nombre": "María",
            "apellido": "Gómez",
            "email": "maria.gomez@example.com",
            "telefono": "+573001234567",
            "usuario": "maria.gomez",
            "password": "ClaveSegura123",
            "confirm_password": "ClaveSegura123",
        }
        datos.update(cambios)
        return datos

    def test_01_login_muestra_formulario_de_credenciales(self):
        respuesta = self.client.get("/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'name="usuario"', respuesta.data)
        self.assertIn(b'name="password"', respuesta.data)

    def test_02_login_exitoso_inicia_sesion(self):
        self.crear_usuario("admin.prueba", rol="administrador")

        respuesta = self.iniciar_sesion("admin.prueba")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assertIsNotNone(self.obtener_id_de_usuario_autenticado())

    def test_03_login_cliente_llega_al_menu_protegido(self):
        self.crear_usuario("cliente.prueba", rol="cliente", cedula=10001)
        self.iniciar_sesion("cliente.prueba")

        respuesta = self.client.get("/menu")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("cliente.prueba", respuesta.get_data(as_text=True))

    def test_04_usuario_inexistente_no_inicia_sesion(self):
        respuesta = self.iniciar_sesion("no.existe")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())
        self.assertIn("Usuario o contraseña incorrectos", respuesta.get_data(as_text=True))

    def test_05_password_incorrecto_no_inicia_sesion(self):
        self.crear_usuario("usuario.clave", password="Password1234")
        respuesta = self.iniciar_sesion("usuario.clave", password="Incorrecta123")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())

    def test_06_login_sin_campos_muestra_error(self):
        respuesta = self.client.post("/", data={}, follow_redirects=False)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assert_contiene_flash("Por favor completa todos los campos")

    def test_07_usuario_autenticado_es_redirigido_desde_login(self):
        self.crear_usuario("ya.autenticado")
        self.iniciar_sesion("ya.autenticado")

        respuesta = self.client.get("/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")

    def test_08_logout_cierra_la_sesion(self):
        self.crear_usuario("salir.prueba")
        self.iniciar_sesion("salir.prueba")

        respuesta = self.client.get("/logout")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())

    def test_09_logout_requiere_autenticacion(self):
        respuesta = self.client.get("/logout")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/", respuesta.headers["Location"])
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())

    def test_10_registro_publico_muestra_formulario(self):
        respuesta = self.client.get("/register")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'id="register-form"', respuesta.data)
        self.assertIn(b'name="cedula"', respuesta.data)
        self.assertIn(b'name="confirm_password"', respuesta.data)

    def test_11_registro_exitoso_crea_cliente_usuario_y_hash(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        with self.app.app_context():
            cliente = Cliente.query.get(12345678)
            usuario = User.query.filter_by(usuario="maria.gomez").one()
            self.assertIsNotNone(cliente)
            self.assertEqual(usuario.rol, "cliente")
            self.assertNotEqual(usuario.password, "ClaveSegura123")
            self.assertTrue(check_password_hash(usuario.password, "ClaveSegura123"))

    def test_12_registro_normaliza_el_correo(self):
        datos = self.datos_registro_validos(email="  MARIA.GOMEZ@EXAMPLE.COM  ")
        self.client.post("/register", data=datos)

        with self.app.app_context():
            cliente = Cliente.query.get(12345678)
            self.assertEqual(cliente.email, "maria.gomez@example.com")

    def test_13_registro_rechaza_usuario_duplicado(self):
        self.crear_usuario("maria.gomez", cedula=None)
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/register")
        self.assert_contiene_flash("El nombre de usuario ya está en uso")

    def test_14_registro_rechaza_cedula_duplicada(self):
        self.crear_cliente(12345678, email="ocupada@example.com")
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/register")
        self.assert_contiene_flash("Esta cédula ya está registrada")

    def test_15_registro_rechaza_correo_duplicado(self):
        self.crear_cliente(87654321, email="maria.gomez@example.com")
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/register")
        self.assert_contiene_flash("El correo electrónico ya está registrado")

    def test_16_registro_exige_todos_los_campos(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(nombre=""), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Por favor completa todos los campos")

    def test_17_registro_rechaza_cedula_invalida(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(cedula="ABC123"), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("cédula o ID")

    def test_18_registro_rechaza_correo_invalido(self):
        respuesta = self.client.post(
            "/register",
            data=self.datos_registro_validos(email="correo-no-valido"),
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("correo electrónico válido")

    def test_19_registro_rechaza_nombre_con_numeros(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(nombre="Ana2"), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("nombre y apellido")

    def test_20_registro_rechaza_telefono_invalido(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(telefono="123"), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("teléfono")

    def test_21_registro_rechaza_usuario_invalido(self):
        respuesta = self.client.post(
            "/register", data=self.datos_registro_validos(usuario="a b"), follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("nombre de usuario")

    def test_22_registro_rechaza_password_muy_corta(self):
        respuesta = self.client.post(
            "/register",
            data=self.datos_registro_validos(password="A1b2", confirm_password="A1b2"),
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("8 y 30 caracteres")

    def test_23_registro_rechaza_password_sin_numero(self):
        respuesta = self.client.post(
            "/register",
            data=self.datos_registro_validos(password="PasswordOnly", confirm_password="PasswordOnly"),
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("al menos una letra y un número")

    def test_24_registro_rechaza_confirmacion_distinta(self):
        respuesta = self.client.post(
            "/register",
            data=self.datos_registro_validos(confirm_password="OtraClave123"),
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Las contraseñas no coinciden")

    def test_25_usuario_autenticado_no_puede_registrarse(self):
        self.crear_usuario("ya.registrado")
        self.iniciar_sesion("ya.registrado")

        respuesta = self.client.get("/register")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")

    def test_26_recuperacion_exige_correo(self):
        respuesta = self.client.post("/recuperar-contrasena", data={}, follow_redirects=False)

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/recuperar-contrasena")
        self.assert_contiene_flash("correo electrónico")

    def test_27_recuperacion_no_revela_si_el_correo_existe(self):
        respuesta = self.client.post(
            "/recuperar-contrasena",
            data={"email": "desconocido@example.com"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assert_contiene_flash(
            "Si el correo está registrado, recibirás instrucciones"
        )

    def test_28_recuperacion_valida_actualiza_password(self):
        self.crear_usuario("recuperar.clave", cedula=11001, email="recuperar@example.com")

        respuesta = self.client.post(
            "/recuperar-contrasena",
            data={"email": "recuperar@example.com"},
            follow_redirects=False,
        )
        token = respuesta.headers["Location"].rsplit("/", 1)[-1]

        with self.app.app_context():
            registro = PasswordResetToken.query.filter_by(token=token).one()
            self.assertFalse(registro.used)

        respuesta_reset = self.client.post(
            f"/restablecer-contrasena/{token}",
            data={"password": "NuevaClave123", "confirm_password": "NuevaClave123"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta_reset.status_code, 302)
        self.assertEqual(respuesta_reset.headers["Location"], "/")
        with self.app.app_context():
            registro = PasswordResetToken.query.filter_by(token=token).one()
            usuario = registro.user
            self.assertTrue(registro.used)
            self.assertTrue(check_password_hash(usuario.password, "NuevaClave123"))

    def test_29_token_recuperacion_solo_puede_usarse_una_vez(self):
        self.crear_usuario("un.uso", cedula=11002, email="un.uso@example.com")
        respuesta = self.client.post(
            "/recuperar-contrasena",
            data={"email": "un.uso@example.com"},
            follow_redirects=False,
        )
        token = respuesta.headers["Location"].rsplit("/", 1)[-1]
        self.client.post(
            f"/restablecer-contrasena/{token}",
            data={"password": "Cambiada123", "confirm_password": "Cambiada123"},
        )

        segundo_uso = self.client.get(f"/restablecer-contrasena/{token}")

        self.assertEqual(segundo_uso.status_code, 302)
        self.assertEqual(segundo_uso.headers["Location"], "/recuperar-contrasena")

    def test_30_token_expirado_es_rechazado(self):
        usuario_id = self.crear_usuario("expirado", cedula=11003)
        with self.app.app_context():
            token = PasswordResetToken(
                user_id=usuario_id,
                token="token-expirado-prueba",
                expires_at=datetime.utcnow() - timedelta(minutes=1),
                used=False,
            )
            from app import db

            db.session.add(token)
            db.session.commit()

        respuesta = self.client.get("/restablecer-contrasena/token-expirado-prueba")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/recuperar-contrasena")
        self.assert_contiene_flash("inválido o ha expirado")
