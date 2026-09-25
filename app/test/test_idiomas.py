"""Pruebas de la Persona 3: cambio y persistencia de idioma."""

from app.test.base import HotelTestCase


class TestIdiomas(HotelTestCase):
    def test_01_idioma_por_defecto_es_espanol(self):
        self.crear_usuario("admin.idioma", rol="administrador")
        self.iniciar_sesion("admin.idioma")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn('<html lang="es">', contenido)
        self.assertIn("Gestión Hotelera", contenido)

    def test_02_cambia_interfaz_completa_a_ingles(self):
        self.crear_usuario("admin.ingles", rol="administrador")
        self.iniciar_sesion("admin.ingles")
        cambio = self.client.get("/set_language/en")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertEqual(cambio.status_code, 302)
        self.assertIn('<html lang="en">', contenido)
        self.assertIn("Hotel Management", contenido)
        self.assertIn("Operations", contenido)
        self.assertIn("Reception History", contenido)

    def test_03_puede_volver_de_ingles_a_espanol(self):
        self.crear_usuario("admin.vuelve_es", rol="administrador")
        self.iniciar_sesion("admin.vuelve_es")
        self.client.get("/set_language/en")

        self.client.get("/set_language/es")
        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn('<html lang="es">', contenido)
        self.assertIn("Gestión Hotelera", contenido)

    def test_04_rechaza_idioma_no_configurado(self):
        self.crear_usuario("admin.idioma_malo", rol="administrador")
        self.iniciar_sesion("admin.idioma_malo")
        self.client.get("/set_language/en")

        self.client.get("/set_language/fr")
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion.get("language"), "en")

    def test_05_idioma_se_persiste_entre_paginas(self):
        self.crear_usuario("admin.persistencia", rol="administrador")
        self.iniciar_sesion("admin.persistencia")
        self.client.get("/set_language/en")

        menu = self.client.get("/menu").get_data(as_text=True)
        perfil = self.client.get("/perfil").get_data(as_text=True)

        self.assertIn("Hotel Management", menu)
        self.assertIn("Save Changes", perfil)
