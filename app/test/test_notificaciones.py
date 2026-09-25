"""Pruebas de la Persona 3: notificaciones y contador AJAX."""

from datetime import date, timedelta

from app.models.notificacion import Notificacion
from app.test.base import HotelTestCase


class TestNotificaciones(HotelTestCase):
    def test_01_notificaciones_requieren_autenticacion(self):
        respuesta = self.client.get("/notificaciones/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_usuario_sin_notificaciones_ve_estado_vacio(self):
        self.crear_usuario("cliente.sin_avisos", cedula=16401)
        self.iniciar_sesion("cliente.sin_avisos")

        respuesta = self.client.get("/notificaciones/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("No tienes notificaciones", respuesta.get_data(as_text=True))

    def test_03_lista_solo_muestra_notificaciones_del_usuario(self):
        usuario_id = self.crear_usuario("cliente.avisos", cedula=16402)
        otro_id = self.crear_usuario("otro.avisos", cedula=16403)
        self.crear_notificacion(usuario_id, titulo="Aviso propio")
        self.crear_notificacion(otro_id, titulo="Aviso ajeno")
        self.iniciar_sesion("cliente.avisos")

        contenido = self.client.get("/notificaciones/").get_data(as_text=True)

        self.assertIn("Aviso propio", contenido)
        self.assertNotIn("Aviso ajeno", contenido)

    def test_04_muestra_cantidad_de_no_leidas(self):
        usuario_id = self.crear_usuario("cliente.nuevas", cedula=16404)
        self.crear_notificacion(usuario_id, titulo="Nueva 1")
        self.crear_notificacion(usuario_id, titulo="Nueva 2")
        self.crear_notificacion(
            usuario_id, titulo="Leída", leida=True
        )
        self.iniciar_sesion("cliente.nuevas")

        respuesta = self.client.get("/notificaciones/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("2", respuesta.get_data(as_text=True))
        self.assertIn("nuevas", respuesta.get_data(as_text=True))

    def test_05_marca_una_notificacion_como_leida(self):
        usuario_id = self.crear_usuario("cliente.marcar", cedula=16405)
        notificacion_id = self.crear_notificacion(usuario_id)
        self.iniciar_sesion("cliente.marcar")

        respuesta = self.client.post(
            f"/notificaciones/marcar-leida/{notificacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertTrue(Notificacion.query.get(notificacion_id).leida)

    def test_06_responde_json_al_marcar_notificacion(self):
        usuario_id = self.crear_usuario("cliente.json", cedula=16406)
        notificacion_id = self.crear_notificacion(usuario_id)
        self.iniciar_sesion("cliente.json")

        respuesta = self.client.post(
            f"/notificaciones/marcar-leida/{notificacion_id}",
            content_type="application/json",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json(), {"success": True})

    def test_07_no_puede_marcar_notificacion_de_otro(self):
        self.crear_usuario("cliente.otro_marca", cedula=16407)
        otro_id = self.crear_usuario("dueño.marca", cedula=16408)
        notificacion_id = self.crear_notificacion(otro_id)
        self.iniciar_sesion("cliente.otro_marca")

        respuesta = self.client.post(
            f"/notificaciones/marcar-leida/{notificacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("No tienes permiso")
        with self.app.app_context():
            self.assertFalse(Notificacion.query.get(notificacion_id).leida)

    def test_08_marca_todas_como_leidas(self):
        usuario_id = self.crear_usuario("cliente.todas", cedula=16409)
        primera = self.crear_notificacion(usuario_id, titulo="Primera")
        segunda = self.crear_notificacion(usuario_id, titulo="Segunda")
        self.iniciar_sesion("cliente.todas")

        respuesta = self.client.post("/notificaciones/marcar-todas-leidas")

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertTrue(Notificacion.query.get(primera).leida)
            self.assertTrue(Notificacion.query.get(segunda).leida)

    def test_09_elimina_propia_notificacion(self):
        usuario_id = self.crear_usuario("cliente.elimina", cedula=16410)
        notificacion_id = self.crear_notificacion(usuario_id)
        self.iniciar_sesion("cliente.elimina")

        respuesta = self.client.post(
            f"/notificaciones/eliminar/{notificacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(Notificacion.query.get(notificacion_id))

    def test_10_no_puede_eliminar_notificacion_ajena(self):
        self.crear_usuario("cliente.elimina_otro", cedula=16411)
        otro_id = self.crear_usuario("dueño.elimina", cedula=16412)
        notificacion_id = self.crear_notificacion(otro_id)
        self.iniciar_sesion("cliente.elimina_otro")

        respuesta = self.client.post(
            f"/notificaciones/eliminar/{notificacion_id}"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("No tienes permiso")
        with self.app.app_context():
            self.assertIsNotNone(Notificacion.query.get(notificacion_id))

    def test_11_contador_ajax_solo_devuelve_no_leidas(self):
        usuario_id = self.crear_usuario("cliente.contador", cedula=16413)
        self.crear_notificacion(usuario_id, titulo="Sin leer 1")
        self.crear_notificacion(usuario_id, titulo="Sin leer 2")
        self.crear_notificacion(
            usuario_id, titulo="Leída", leida=True
        )
        self.iniciar_sesion("cliente.contador")

        respuesta = self.client.get("/notificaciones/contador-no-leidas")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json(), {"no_leidas": 2})

    def test_12_reserva_creada_genera_notificacion_automatica(self):
        self.crear_cliente(16414, nombre="Notificado", apellido="Cliente")
        usuario_id = self.crear_usuario("cliente.autonotificado", cedula=16414)
        habitacion_id = self.crear_habitacion(numero=401)
        self.iniciar_sesion("cliente.autonotificado")
        entrada = date.today() + timedelta(days=1)
        salida = entrada + timedelta(days=2)

        respuesta = self.client.post(
            "/reservas/nueva",
            data={
                "id_habitacion": str(habitacion_id),
                "fecha_entrada": entrada.isoformat(),
                "fecha_salida": salida.isoformat(),
                "cantidad_personas": "2",
                "metodo_pago": "tarjeta",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            notificacion = Notificacion.query.filter_by(usuario_id=usuario_id).one()
            self.assertEqual(notificacion.titulo, "¡Reserva Creada!")
            self.assertIn("ha sido creada exitosamente", notificacion.mensaje)
