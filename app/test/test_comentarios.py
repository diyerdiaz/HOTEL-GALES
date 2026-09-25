"""Pruebas de la Persona 3: comentarios, calificaciones y permisos."""

from app.models.comentario import Comentario
from app.test.base import HotelTestCase


class TestComentarios(HotelTestCase):
    def preparar_cliente_hospedado(self, cedula=16501, usuario="cliente.comentario"):
        self.crear_cliente(
            cedula, nombre="Cliente", apellido="Comentario"
        )
        self.crear_usuario(usuario, cedula=cedula)
        habitacion_id = self.crear_habitacion(numero=501)
        reserva_id = self.crear_reserva(
            cedula, habitacion_id, estado="finalizada"
        )
        return habitacion_id, reserva_id

    def test_01_comentarios_requieren_autenticacion(self):
        habitacion_id = self.crear_habitacion(numero=502)

        respuesta = self.client.get(
            f"/comentarios/habitacion/{habitacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_muestra_promedio_de_calificaciones(self):
        habitacion_id = self.crear_habitacion(numero=503)
        self.crear_cliente(16502)
        self.crear_cliente(16503)
        self.crear_comentario(habitacion_id, 16502, calificacion=5)
        self.crear_comentario(habitacion_id, 16503, calificacion=4)
        self.crear_usuario("cliente.lee_comentarios", cedula=16504)
        self.iniciar_sesion("cliente.lee_comentarios")

        contenido = self.client.get(
            f"/comentarios/habitacion/{habitacion_id}"
        ).get_data(as_text=True)

        self.assertIn("4.5", contenido)
        self.assertIn("2 comentarios", contenido)

    def test_03_habitacion_sin_comentarios_muestra_estado_vacio(self):
        habitacion_id = self.crear_habitacion(numero=504)
        self.crear_usuario("cliente.sin_comentarios", cedula=16505)
        self.iniciar_sesion("cliente.sin_comentarios")

        respuesta = self.client.get(
            f"/comentarios/habitacion/{habitacion_id}"
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "Esta habitación aún no tiene comentarios",
            respuesta.get_data(as_text=True),
        )

    def test_04_personal_no_puede_crear_comentarios(self):
        self.crear_usuario("admin.comentarios", rol="administrador")
        habitacion_id = self.crear_habitacion(numero=505)
        self.iniciar_sesion("admin.comentarios")

        respuesta = self.client.get(
            f"/comentarios/nuevo/{habitacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/habitaciones/")
        self.assert_contiene_flash("Solo los clientes pueden dejar comentarios")

    def test_05_cliente_sin_reserva_finalizada_no_comenta(self):
        self.crear_cliente(16506)
        self.crear_usuario("cliente.sin_estancia", cedula=16506)
        habitacion_id = self.crear_habitacion(numero=506)
        self.crear_reserva(16506, habitacion_id, estado="confirmada")
        self.iniciar_sesion("cliente.sin_estancia")

        respuesta = self.client.get(
            f"/comentarios/nuevo/{habitacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            respuesta.headers["Location"],
            f"/habitaciones/detalle/{habitacion_id}",
        )
        self.assert_contiene_flash("donde te has hospedado")

    def test_06_cliente_puede_publicar_comentario(self):
        habitacion_id, _ = self.preparar_cliente_hospedado()
        self.iniciar_sesion("cliente.comentario")

        respuesta = self.client.post(
            f"/comentarios/nuevo/{habitacion_id}",
            data={
                "calificacion": "5",
                "comentario": "Habitación limpia y muy cómoda.",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            comentario = Comentario.query.one()
            self.assertEqual(comentario.calificacion, 5)
            self.assertEqual(comentario.cedulaCliente, 16501)

    def test_07_rechaza_comentario_sin_campos(self):
        habitacion_id, _ = self.preparar_cliente_hospedado(
            cedula=16507, usuario="cliente.campos"
        )
        self.iniciar_sesion("cliente.campos")

        respuesta = self.client.post(
            f"/comentarios/nuevo/{habitacion_id}", data={}
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Por favor completa todos los campos")

    def test_08_rechaza_calificaciones_fuera_del_rango(self):
        habitacion_id, _ = self.preparar_cliente_hospedado(
            cedula=16508, usuario="cliente.rango"
        )
        self.iniciar_sesion("cliente.rango")

        for calificacion in ("0", "6", "abc"):
            with self.subTest(calificacion=calificacion):
                respuesta = self.client.post(
                    f"/comentarios/nuevo/{habitacion_id}",
                    data={
                        "calificacion": calificacion,
                        "comentario": "Texto suficientemente largo para probar.",
                    },
                )
                self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertEqual(Comentario.query.count(), 0)

    def test_09_rechaza_comentario_muy_corto(self):
        habitacion_id, _ = self.preparar_cliente_hospedado(
            cedula=16509, usuario="cliente.corto"
        )
        self.iniciar_sesion("cliente.corto")

        respuesta = self.client.post(
            f"/comentarios/nuevo/{habitacion_id}",
            data={"calificacion": "4", "comentario": "Corto"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("al menos 10 caracteres")

    def test_10_rechaza_comentario_demasiado_largo(self):
        habitacion_id, _ = self.preparar_cliente_hospedado(
            cedula=16510, usuario="cliente.largo"
        )
        self.iniciar_sesion("cliente.largo")

        respuesta = self.client.post(
            f"/comentarios/nuevo/{habitacion_id}",
            data={
                "calificacion": "4",
                "comentario": "A" * 501,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("no puede exceder 500")

    def test_11_no_permite_dos_comentarios_en_la_misma_habitacion(self):
        habitacion_id, _ = self.preparar_cliente_hospedado(
            cedula=16511, usuario="cliente.duplicado"
        )
        self.crear_comentario(habitacion_id, 16511)
        self.iniciar_sesion("cliente.duplicado")

        respuesta = self.client.get(f"/comentarios/nuevo/{habitacion_id}")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            respuesta.headers["Location"],
            f"/comentarios/habitacion/{habitacion_id}",
        )
        self.assert_contiene_flash("Ya has dejado un comentario")

    def test_12_mis_comentarios_solo_muestra_los_propios(self):
        habitacion_id = self.crear_habitacion(numero=507)
        self.crear_cliente(16512)
        self.crear_cliente(16513)
        self.crear_comentario(
            habitacion_id, 16512, texto="Comentario propio visible"
        )
        self.crear_comentario(
            habitacion_id, 16513, texto="Comentario ajeno oculto"
        )
        self.crear_usuario("cliente.mis_comentarios", cedula=16512)
        self.iniciar_sesion("cliente.mis_comentarios")

        contenido = self.client.get("/comentarios/mis-comentarios").get_data(
            as_text=True
        )

        self.assertIn("Comentario propio visible", contenido)
        self.assertNotIn("Comentario ajeno oculto", contenido)

    def test_13_personal_no_accede_a_mis_comentarios(self):
        self.crear_usuario("recepcion.mis_comentarios", rol="recepcionista")
        self.iniciar_sesion("recepcion.mis_comentarios")

        respuesta = self.client.get("/comentarios/mis-comentarios")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("solo para clientes")

    def test_14_cliente_elimina_su_comentario(self):
        habitacion_id = self.crear_habitacion(numero=508)
        self.crear_cliente(16514)
        comentario_id = self.crear_comentario(habitacion_id, 16514)
        self.crear_usuario("cliente.elimina_comentario", cedula=16514)
        self.iniciar_sesion("cliente.elimina_comentario")

        respuesta = self.client.post(
            f"/comentarios/eliminar/{comentario_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            respuesta.headers["Location"], "/comentarios/mis-comentarios"
        )
        with self.app.app_context():
            self.assertIsNone(Comentario.query.get(comentario_id))

    def test_15_no_elimina_comentario_de_otro_cliente(self):
        habitacion_id = self.crear_habitacion(numero=509)
        self.crear_cliente(16515)
        self.crear_cliente(16516)
        comentario_id = self.crear_comentario(habitacion_id, 16516)
        self.crear_usuario("cliente.protegido", cedula=16515)
        self.iniciar_sesion("cliente.protegido")

        respuesta = self.client.post(
            f"/comentarios/eliminar/{comentario_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("No tienes permiso")
        with self.app.app_context():
            self.assertIsNotNone(Comentario.query.get(comentario_id))

    def test_16_comentario_inexistente_devuelve_404(self):
        self.crear_usuario("cliente.404_comentario", cedula=16517)
        self.iniciar_sesion("cliente.404_comentario")

        respuesta = self.client.post("/comentarios/eliminar/999999")

        self.assertEqual(respuesta.status_code, 404)

    def test_17_escapa_html_en_comentarios(self):
        habitacion_id = self.crear_habitacion(numero=510)
        self.crear_cliente(16518)
        texto_malicioso = "<script>alert(1)</script>Comentario de seguridad"
        self.crear_comentario(habitacion_id, 16518, texto=texto_malicioso)
        self.crear_usuario("cliente.xss", cedula=16518)
        self.iniciar_sesion("cliente.xss")

        contenido = self.client.get(
            f"/comentarios/habitacion/{habitacion_id}"
        ).get_data(as_text=True)

        self.assertIn("&lt;script&gt;", contenido)
        self.assertNotIn(texto_malicioso, contenido)
