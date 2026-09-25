"""Pruebas de la Persona 3: consumos asociados a reservas."""

from app.test.base import HotelTestCase


class TestConsumos(HotelTestCase):
    def preparar_consumo(self):
        self.crear_cliente(16201, nombre="Cliente", apellido="Consumo")
        habitacion_id = self.crear_habitacion(numero=301)
        reserva_id = self.crear_reserva(16201, habitacion_id)
        servicio_id = self.crear_servicio()
        return self.crear_consumo(
            reserva_id, servicio_id, cantidad=2, subtotal=70000
        ), reserva_id

    def test_01_consumos_requieren_autenticacion(self):
        respuesta = self.client.get("/consumos/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_administrador_consulta_consumos(self):
        self.preparar_consumo()
        self.crear_usuario("admin.consumos", rol="administrador")
        self.iniciar_sesion("admin.consumos")

        respuesta = self.client.get("/consumos/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Desayuno buffet", respuesta.get_data(as_text=True))

    def test_03_recepcionista_consulta_consumos(self):
        self.preparar_consumo()
        self.crear_usuario("recepcion.consumos", rol="recepcionista")
        self.iniciar_sesion("recepcion.consumos")

        respuesta = self.client.get("/consumos/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Desayuno buffet", respuesta.get_data(as_text=True))

    def test_04_cliente_no_consulta_consumos_de_huespedes(self):
        self.crear_usuario("cliente.consumos", cedula=16202)
        self.iniciar_sesion("cliente.consumos")

        respuesta = self.client.get("/consumos/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_05_personal_limpieza_no_consulta_consumos(self):
        self.crear_usuario("limpieza.consumos", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.consumos")

        respuesta = self.client.get("/consumos/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
