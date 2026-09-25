"""Pruebas de la Persona 3: registro y consulta de pagos."""

from app.test.base import HotelTestCase


class TestPagos(HotelTestCase):
    def preparar_pago(self):
        self.crear_cliente(16101, nombre="Cliente", apellido="Pago")
        habitacion_id = self.crear_habitacion(numero=201)
        reserva_id = self.crear_reserva(16101, habitacion_id)
        return self.crear_pago(
            reserva_id, metodo="tarjeta", valor=185000
        ), reserva_id

    def test_01_pagos_requieren_autenticacion(self):
        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_administrador_consulta_pagos(self):
        self.preparar_pago()
        self.crear_usuario("admin.pagos", rol="administrador")
        self.iniciar_sesion("admin.pagos")

        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Registro de Pagos", respuesta.get_data(as_text=True))

    def test_03_recepcionista_consulta_pagos(self):
        self.preparar_pago()
        self.crear_usuario("recepcion.pagos", rol="recepcionista")
        self.iniciar_sesion("recepcion.pagos")

        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.status_code, 200)

    def test_04_cliente_no_consulta_pagos(self):
        self.crear_usuario("cliente.pagos", cedula=16102)
        self.iniciar_sesion("cliente.pagos")

        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_05_lista_muestra_metodo_y_valor(self):
        pago_id, reserva_id = self.preparar_pago()
        self.crear_usuario("admin.detalle_pago", rol="administrador")
        self.iniciar_sesion("admin.detalle_pago")

        contenido = self.client.get("/pagos/").get_data(as_text=True)

        self.assertIn(str(pago_id), contenido)
        self.assertIn(str(reserva_id), contenido)
        self.assertIn("tarjeta", contenido)
        self.assertIn("185000", contenido)

    def test_06_lista_sin_pagos_muestra_estado_vacio(self):
        self.crear_usuario("admin.sin_pagos", rol="administrador")
        self.iniciar_sesion("admin.sin_pagos")

        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Sin registros de pago", respuesta.get_data(as_text=True))
