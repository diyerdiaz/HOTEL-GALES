"""Pruebas de la Persona 3: elementos comunes de la interfaz web."""

from app.test.base import HotelTestCase


class TestInterfaz(HotelTestCase):
    def test_01_login_incluye_configuracion_responsive(self):
        respuesta = self.client.get("/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            b'<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            respuesta.data,
        )

    def test_02_dashboard_incluye_configuracion_responsive(self):
        self.crear_usuario("admin.interfaz", rol="administrador")
        self.iniciar_sesion("admin.interfaz")

        respuesta = self.client.get("/menu")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            b'<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            respuesta.data,
        )

    def test_03_sidebar_muestra_usuario_y_rol_actuales(self):
        self.crear_usuario("admin.sidebar", rol="administrador")
        self.iniciar_sesion("admin.sidebar")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn("admin.sidebar", contenido)
        self.assertIn("Administrador", contenido)
        self.assertIn('class="sidebar"', contenido)

    def test_04_pagina_inexistente_muestra_error_404(self):
        respuesta = self.client.get("/ruta-que-no-existe")

        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("404", respuesta.get_data(as_text=True))
        self.assertIn("Página no encontrada", respuesta.get_data(as_text=True))
