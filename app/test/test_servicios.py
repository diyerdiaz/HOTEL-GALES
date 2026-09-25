"""Pruebas de la Persona 3: catálogo de servicios y categorías."""

from app.test.base import HotelTestCase


class TestServicios(HotelTestCase):
    def test_01_servicios_requieren_autenticacion(self):
        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_administrador_consulta_servicios(self):
        self.crear_servicio()
        self.crear_usuario("admin.servicios", rol="administrador")
        self.iniciar_sesion("admin.servicios")

        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Catálogo de Servicios", respuesta.get_data(as_text=True))

    def test_03_recepcionista_consulta_servicios(self):
        self.crear_servicio(nombre="Room service", precio=42000)
        self.crear_usuario("recepcion.servicios", rol="recepcionista")
        self.iniciar_sesion("recepcion.servicios")

        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Room service", respuesta.get_data(as_text=True))

    def test_04_cliente_no_gestiona_servicios(self):
        self.crear_usuario("cliente.servicios", cedula=16301)
        self.iniciar_sesion("cliente.servicios")

        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_05_personal_limpieza_no_gestiona_servicios(self):
        self.crear_usuario("limpieza.servicios", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.servicios")

        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")

    def test_06_muestra_nombre_tipo_y_precio_formateado(self):
        self.crear_servicio(
            nombre="Spa relaxante", precio=95000, tipo_nombre="Bienestar"
        )
        self.crear_usuario("admin.detalle_servicio", rol="administrador")
        self.iniciar_sesion("admin.detalle_servicio")

        contenido = self.client.get("/servicios/").get_data(as_text=True)

        self.assertIn("Spa relaxante", contenido)
        self.assertIn("Bienestar", contenido)
        self.assertIn("$ 95.000 COP", contenido)

    def test_07_catalogo_vacio_muestra_mensaje(self):
        self.crear_usuario("admin.sin_servicios", rol="administrador")
        self.iniciar_sesion("admin.sin_servicios")

        respuesta = self.client.get("/servicios/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("No hay servicios registrados", respuesta.get_data(as_text=True))

    def test_08_administrador_consulta_categorias_con_conteo(self):
        self.crear_servicio(
            nombre="Bebida caliente", tipo_nombre="Bebidas"
        )
        self.crear_usuario("admin.tipos_servicio", rol="administrador")
        self.iniciar_sesion("admin.tipos_servicio")

        contenido = self.client.get("/admin/tipo-servicios/").get_data(as_text=True)

        self.assertIn("Bebidas", contenido)
        self.assertIn("1", contenido)
        self.assertIn("servicios", contenido)

    def test_09_recepcionista_no_gestiona_categorias(self):
        self.crear_usuario("recepcion.tipos", rol="recepcionista")
        self.iniciar_sesion("recepcion.tipos")

        respuesta = self.client.get("/admin/tipo-servicios/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("Solo administradores")
