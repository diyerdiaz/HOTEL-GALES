"""Pruebas de la Persona 3: facturación y validación pública de facturas."""

from app.test.base import HotelTestCase


class TestFacturacion(HotelTestCase):
    def crear_escenario_factura(
        self,
        cedula=16001,
        nombre="Cliente",
        apellido="Facturación",
        total=450000,
    ):
        self.crear_cliente(cedula, nombre=nombre, apellido=apellido)
        habitacion_id = self.crear_habitacion(numero=int(cedula) - 15900)
        reserva_id = self.crear_reserva(cedula, habitacion_id)
        factura_id = self.crear_factura(reserva_id, total=total)
        return factura_id, cedula, nombre, apellido

    def test_01_facturacion_requiere_autenticacion(self):
        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_administrador_consulta_facturacion(self):
        self.crear_usuario("admin.facturacion", rol="administrador")
        self.iniciar_sesion("admin.facturacion")

        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Gestión de Facturación", respuesta.get_data(as_text=True))

    def test_03_recepcionista_consulta_facturacion(self):
        self.crear_usuario("recepcion.facturacion", rol="recepcionista")
        self.iniciar_sesion("recepcion.facturacion")

        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.status_code, 200)

    def test_04_personal_limpieza_no_consulta_facturacion(self):
        self.crear_usuario("limpieza.facturacion", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.facturacion")

        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_05_cliente_consulta_sus_propias_facturas(self):
        self.crear_cliente(16002, nombre="Ana", apellido="Dueña")
        self.crear_usuario("cliente.factura", cedula=16002)
        habitacion_id = self.crear_habitacion(numero=102)
        reserva_id = self.crear_reserva(16002, habitacion_id)
        self.crear_factura(reserva_id, total=300000)
        self.iniciar_sesion("cliente.factura")

        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("Mis Facturas", contenido)
        self.assertIn("Ana Dueña", contenido)

    def test_06_cliente_no_ve_facturas_de_otros(self):
        self.crear_cliente(16003, nombre="Ana", apellido="Dueña")
        self.crear_cliente(16004, nombre="Otro", apellido="Cliente")
        self.crear_usuario("cliente.aislado", cedula=16003)
        habitacion_ana = self.crear_habitacion(numero=103)
        habitacion_otro = self.crear_habitacion(numero=104)
        factura_ana = self.crear_factura(self.crear_reserva(16003, habitacion_ana))
        self.crear_factura(self.crear_reserva(16004, habitacion_otro))
        self.iniciar_sesion("cliente.aislado")

        contenido = self.client.get("/facturas/").get_data(as_text=True)

        self.assertIn(f"#{factura_ana:05d}", contenido)
        self.assertNotIn("Otro Cliente", contenido)

    def test_07_busqueda_de_facturas_por_cliente(self):
        self.crear_escenario_factura(
            cedula=16005, nombre="Busqueda", apellido="Factura", total=510000
        )
        self.crear_usuario("admin.busqueda_factura", rol="administrador")
        self.iniciar_sesion("admin.busqueda_factura")

        respuesta = self.client.get("/facturas/?search=Busqueda")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Busqueda Factura", respuesta.get_data(as_text=True))

    def test_08_lista_sin_facturas_muestra_mensaje(self):
        self.crear_usuario("cliente.sin_facturas", cedula=16006)
        self.iniciar_sesion("cliente.sin_facturas")

        respuesta = self.client.get("/facturas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "Cuando realices una reserva, tu factura aparecerá aquí",
            respuesta.get_data(as_text=True),
        )

    def test_09_detalle_genera_qr_y_muestra_total(self):
        factura_id, _, _, _ = self.crear_escenario_factura(
            cedula=16007, total=475000
        )
        self.crear_usuario("admin.detalle_factura", rol="administrador")
        self.iniciar_sesion("admin.detalle_factura")

        respuesta = self.client.get(f"/facturas/ver/{factura_id}")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("data:image/png;base64,", contenido)
        self.assertIn("$ 475.000 COP", contenido)

    def test_10_cliente_no_abre_factura_de_otro(self):
        self.crear_cliente(16008, nombre="Intruso", apellido="Cliente")
        self.crear_usuario("cliente.intruso", cedula=16008)
        factura_id, _, _, _ = self.crear_escenario_factura(
            cedula=16009, nombre="Titular", apellido="Factura"
        )
        self.iniciar_sesion("cliente.intruso")

        respuesta = self.client.get(f"/facturas/ver/{factura_id}")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/facturas/")
        self.assert_contiene_flash("No tienes permiso para ver esta factura")

    def test_11_validacion_publica_no_requiere_sesion(self):
        factura_id, cedula, nombre, apellido = self.crear_escenario_factura(
            cedula=16010, nombre="Pública", apellido="Validación", total=620000
        )

        respuesta = self.client.get(f"/facturas/validar/{factura_id}")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Documento Auténtico", contenido)
        self.assertIn("Pública Validación", contenido)
        self.assertIn(f"****{str(cedula)[-4:]}", contenido)
        self.assertNotIn(f"C.C: {cedula}", contenido)
