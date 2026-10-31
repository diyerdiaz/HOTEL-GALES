"""Pruebas de regresión para las vulnerabilidades corregidas en la auditoría de seguridad."""

import re

from config import Config
from app.models.habitacion import Habitacion
from app.models.reserva import Reserva
from app.test.base import HotelTestCase


class TestVulnerabilidades(HotelTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Ruta que falla a propósito para revisar qué ve el usuario ante un error interno
        def ruta_que_falla():
            raise ValueError("detalle-interno-secreto <script>alert(1)</script>")

        cls.app.add_url_rule("/_prueba_error", "prueba_error", ruta_que_falla)

    # ------------------------------------------------------------------
    # Errores y cabeceras
    # ------------------------------------------------------------------
    def test_01_error_interno_no_muestra_detalles_tecnicos(self):
        respuesta = self.client.get("/_prueba_error")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 500)
        self.assertNotIn("detalle-interno-secreto", contenido)
        self.assertNotIn("<script>", contenido)

    def test_02_errores_http_conservan_su_codigo(self):
        self.assertEqual(self.client.get("/no-existe-esta-ruta").status_code, 404)
        self.crear_usuario("metodo.incorrecto", cedula=17001)
        self.iniciar_sesion("metodo.incorrecto")
        self.assertEqual(self.client.get("/perfil/eliminar").status_code, 405)

    def test_03_respuestas_incluyen_cabeceras_de_seguridad(self):
        respuesta = self.client.get("/")

        self.assertEqual(respuesta.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(respuesta.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn("Referrer-Policy", respuesta.headers)

    def test_04_cookie_de_sesion_es_httponly_y_samesite(self):
        self.crear_usuario("cookie.segura", cedula=17002)
        respuesta = self.iniciar_sesion("cookie.segura")
        cookie = respuesta.headers.get("Set-Cookie", "")

        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_05_no_existe_clave_secreta_fija_por_defecto(self):
        self.assertNotEqual(Config.SECRET_KEY, "clave-por-defecto-insegura")
        self.assertNotEqual(self.app.config["SECRET_KEY"], "clave-por-defecto-insegura")

    # ------------------------------------------------------------------
    # CSRF
    # ------------------------------------------------------------------
    def test_06_formulario_sin_token_csrf_es_rechazado(self):
        self.crear_usuario("csrf.usuario", cedula=17003)
        self.app.config["WTF_CSRF_ENABLED"] = True
        try:
            respuesta = self.iniciar_sesion("csrf.usuario")
        finally:
            self.app.config["WTF_CSRF_ENABLED"] = False

        self.assertEqual(respuesta.status_code, 400)
        self.assertIsNone(self.obtener_id_de_usuario_autenticado())

    def test_07_formulario_con_token_csrf_es_aceptado(self):
        self.crear_usuario("csrf.valido", cedula=17004)
        self.app.config["WTF_CSRF_ENABLED"] = True
        try:
            pagina = self.client.get("/").get_data(as_text=True)
            token = re.search(r'name="csrf_token" value="([^"]+)"', pagina).group(1)
            respuesta = self.client.post(
                "/",
                data={"usuario": "csrf.valido", "password": self.PASSWORD_PRUEBA, "csrf_token": token},
            )
        finally:
            self.app.config["WTF_CSRF_ENABLED"] = False

        self.assertEqual(respuesta.status_code, 302)
        self.assertIsNotNone(self.obtener_id_de_usuario_autenticado())

    def test_08_paginas_internas_publican_el_token_csrf(self):
        self.crear_usuario("admin.csrf", rol="administrador")
        self.iniciar_sesion("admin.csrf")

        contenido = self.client.get("/habitaciones/nueva").get_data(as_text=True)

        self.assertIn('<meta name="csrf-token"', contenido)

    # ------------------------------------------------------------------
    # Acciones que modifican datos ya no aceptan GET (un enlace no basta)
    # ------------------------------------------------------------------
    def test_09_acciones_que_modifican_datos_rechazan_get(self):
        self.crear_usuario("admin.get", rol="administrador")
        self.iniciar_sesion("admin.get")
        hab_id = self.crear_habitacion(numero=701)

        rutas = [
            f"/habitaciones/eliminar/{hab_id}",
            f"/habitaciones/estado/{hab_id}/mantenimiento",
            "/reservas/cancelar/1",
            "/reservas/mantenimiento/1",
            "/limpieza/iniciar/1",
            "/limpieza/completar/1",
            "/mantenimientos/cambiar-estado/1/disponible",
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 405)

        with self.app.app_context():
            self.assertIsNotNone(Habitacion.query.get(hab_id))

    # ------------------------------------------------------------------
    # Control de acceso
    # ------------------------------------------------------------------
    def test_10_estado_de_habitacion_invalido_es_rechazado(self):
        self.crear_usuario("admin.estado", rol="administrador")
        self.iniciar_sesion("admin.estado")
        hab_id = self.crear_habitacion(numero=702)

        self.client.post(f"/habitaciones/estado/{hab_id}/<script>hackeado")

        with self.app.app_context():
            self.assertEqual(Habitacion.query.get(hab_id).estadoHabitacion, "disponible")
        self.assert_contiene_flash("Estado inválido")

    def test_11_limpieza_no_puede_marcar_habitacion_ocupada(self):
        self.crear_usuario("limpieza.estado", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.estado")
        hab_id = self.crear_habitacion(numero=703, estado="disponible")

        self.client.post(f"/habitaciones/estado/{hab_id}/ocupada")

        with self.app.app_context():
            self.assertEqual(Habitacion.query.get(hab_id).estadoHabitacion, "disponible")

    def test_12_limpieza_si_puede_marcar_limpia_una_habitacion_en_limpieza(self):
        self.crear_usuario("limpieza.ok", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.ok")
        hab_id = self.crear_habitacion(numero=704, estado="limpieza")

        self.client.post(f"/habitaciones/estado/{hab_id}/disponible")

        with self.app.app_context():
            self.assertEqual(Habitacion.query.get(hab_id).estadoHabitacion, "disponible")

    def test_13_limpieza_no_puede_cancelar_reservas(self):
        self.crear_cliente(17005)
        self.crear_usuario("dueno.reserva", cedula=17005)
        hab_id = self.crear_habitacion(numero=705, estado="ocupada")
        reserva_id = self.crear_reserva(17005, hab_id, estado="confirmada")
        self.crear_usuario("limpieza.cancelar", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.cancelar")

        self.client.post(f"/reservas/cancelar/{reserva_id}")

        with self.app.app_context():
            self.assertEqual(Reserva.query.get(reserva_id).estadoReserva, "confirmada")
        self.assert_contiene_flash("No tienes permiso")

    def test_14_cliente_no_puede_cancelar_reserva_ajena(self):
        self.crear_cliente(17006)
        hab_id = self.crear_habitacion(numero=706, estado="ocupada")
        reserva_id = self.crear_reserva(17006, hab_id, estado="confirmada")
        self.crear_usuario("otro.cliente", cedula=17007)
        self.iniciar_sesion("otro.cliente")

        self.client.post(f"/reservas/cancelar/{reserva_id}")

        with self.app.app_context():
            self.assertEqual(Reserva.query.get(reserva_id).estadoReserva, "confirmada")

    # ------------------------------------------------------------------
    # Redirecciones
    # ------------------------------------------------------------------
    def test_15_cambio_de_idioma_no_redirige_a_sitios_externos(self):
        respuesta = self.client.get(
            "/set_language/en", headers={"Referer": "https://sitio-malicioso.example/robar"}
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn("sitio-malicioso", respuesta.headers["Location"])

    def test_16_cambio_de_idioma_regresa_a_la_pagina_interna(self):
        respuesta = self.client.get(
            "/set_language/en", headers={"Referer": "http://localhost/habitaciones/publica"}
        )

        self.assertEqual(respuesta.headers["Location"], "http://localhost/habitaciones/publica")
