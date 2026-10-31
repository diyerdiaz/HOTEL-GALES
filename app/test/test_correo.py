"""Pruebas del envío de correos de recuperación de contraseña (SMTP simulado)."""

from unittest.mock import patch

from app.models.password_reset import PasswordResetToken
from app.test.base import HotelTestCase


CONFIG_CORREO = {
    "MAIL_SERVER": "smtp.prueba.local",
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": "hotel@prueba.local",
    "MAIL_PASSWORD": "clave-smtp-prueba",
    "MAIL_SENDER": "hotel@prueba.local",
    "MAIL_SENDER_NAME": "Hotel Gales",
    "MAIL_ASYNC": False,
    "URL_PUBLICA": "",
}


class TestCorreo(HotelTestCase):
    def setUp(self):
        super().setUp()
        self._config_original = {k: self.app.config.get(k) for k in CONFIG_CORREO}
        self.app.config.update(CONFIG_CORREO)
        self.crear_usuario("correo.cliente", cedula=18001, email="cliente@example.com")
        with self.app.app_context():
            from app.models.cliente import Cliente
            Cliente.query.get(18001).nombre = "Laura"
            from app import db
            db.session.commit()

    def tearDown(self):
        self.app.config.update(self._config_original)
        super().tearDown()

    def solicitar(self, email="cliente@example.com", **kwargs):
        return self.client.post("/recuperar-contrasena", data={"email": email}, **kwargs)

    def ultimo_token(self):
        with self.app.app_context():
            registro = PasswordResetToken.query.order_by(PasswordResetToken.id.desc()).first()
            return registro.token if registro else None

    def mensaje_enviado(self, smtp):
        servidor = smtp.return_value
        servidor.send_message.assert_called_once()
        return servidor, servidor.send_message.call_args[0][0]

    @patch("app.utils.correo.smtplib.SMTP")
    def test_01_envia_el_enlace_al_correo_del_cliente(self, smtp):
        respuesta = self.solicitar()

        servidor, mensaje = self.mensaje_enviado(smtp)
        token = self.ultimo_token()
        texto = mensaje.get_body(("plain",)).get_content()
        html = mensaje.get_body(("html",)).get_content()

        smtp.assert_called_once_with("smtp.prueba.local", 587, timeout=self.app.config["MAIL_TIMEOUT"])
        servidor.starttls.assert_called_once()
        servidor.login.assert_called_once_with("hotel@prueba.local", "clave-smtp-prueba")
        self.assertEqual(mensaje["To"], "cliente@example.com")
        self.assertIn("Hotel Gales", mensaje["From"])
        self.assertIn(f"/restablecer-contrasena/{token}", texto)
        self.assertIn(f"/restablecer-contrasena/{token}", html)
        self.assertIn("Laura", texto)
        self.assertIn("correo.cliente", texto)
        # La respuesta es la misma de siempre: el token nunca aparece en la página
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assertFalse(any(token in m for m in self.mensajes_flash()))

    @patch("app.utils.correo.smtplib.SMTP")
    def test_02_el_enlace_del_correo_permite_cambiar_la_contrasena(self, smtp):
        self.solicitar()
        _, mensaje = self.mensaje_enviado(smtp)
        texto = mensaje.get_body(("plain",)).get_content()
        ruta = texto[texto.index("/restablecer-contrasena/"):].split()[0]

        respuesta = self.client.post(
            ruta, data={"password": "DesdeCorreo123", "confirm_password": "DesdeCorreo123"}
        )
        self.assertEqual(respuesta.headers["Location"], "/")

        login = self.iniciar_sesion("correo.cliente", "DesdeCorreo123")
        self.assertEqual(login.status_code, 302)
        self.assertIsNotNone(self.obtener_id_de_usuario_autenticado())

    @patch("app.utils.correo.smtplib.SMTP")
    def test_03_correo_no_registrado_no_envia_nada(self, smtp):
        respuesta = self.solicitar("nadie@example.com")

        smtp.assert_not_called()
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assert_contiene_flash("Si el correo está registrado")

    @patch("app.utils.correo.smtplib.SMTP")
    def test_04_correo_se_busca_sin_importar_mayusculas_ni_espacios(self, smtp):
        self.solicitar("  Cliente@Example.COM ")

        self.mensaje_enviado(smtp)

    @patch("app.utils.correo.smtplib.SMTP")
    def test_05_enlace_usa_url_publica_aunque_falsifiquen_el_host(self, smtp):
        self.app.config["URL_PUBLICA"] = "https://hotelgales.com"

        self.solicitar(headers={"Host": "sitio-atacante.example"})

        _, mensaje = self.mensaje_enviado(smtp)
        texto = mensaje.get_body(("plain",)).get_content()
        self.assertIn("https://hotelgales.com/restablecer-contrasena/", texto)
        self.assertNotIn("sitio-atacante", texto)

    @patch("app.utils.correo.smtplib.SMTP")
    def test_06_falla_del_servidor_de_correo_no_rompe_la_pagina(self, smtp):
        smtp.return_value.send_message.side_effect = OSError("SMTP caído")

        respuesta = self.solicitar()

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assert_contiene_flash("Si el correo está registrado")

    @patch("app.utils.correo.smtplib.SMTP_SSL")
    @patch("app.utils.correo.smtplib.SMTP")
    def test_07_soporta_conexion_ssl_directa(self, smtp, smtp_ssl):
        self.app.config.update(MAIL_USE_SSL=True, MAIL_PORT=465)

        self.solicitar()

        smtp.assert_not_called()
        servidor = smtp_ssl.return_value
        servidor.starttls.assert_not_called()
        servidor.send_message.assert_called_once()

    @patch("app.utils.correo.smtplib.SMTP")
    def test_08_sin_servidor_configurado_no_intenta_enviar(self, smtp):
        self.app.config["MAIL_SERVER"] = ""

        respuesta = self.solicitar()

        smtp.assert_not_called()
        self.assertEqual(respuesta.headers["Location"], "/")
        self.assertIsNotNone(self.ultimo_token())

    @patch("app.utils.correo.threading.Thread")
    def test_09_por_defecto_se_envia_en_segundo_plano(self, hilo):
        self.app.config["MAIL_ASYNC"] = True

        self.solicitar()

        hilo.assert_called_once()
        hilo.return_value.start.assert_called_once()
