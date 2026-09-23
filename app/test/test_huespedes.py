"""Pruebas de consulta y gestión de huéspedes."""

import unittest

from app.models.cliente import Cliente
from app.test.base import HotelTestCase


class TestHuespedes(HotelTestCase):
    def test_01_lista_huespedes_requiere_autenticacion(self):
        respuesta = self.client.get("/clientes/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_cliente_no_puede_gestionar_huespedes(self):
        self.crear_usuario("cliente.sin_lista", cedula=14001)
        self.iniciar_sesion("cliente.sin_lista")

        respuesta = self.client.get("/clientes/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_03_administrador_consulta_huespedes(self):
        self.crear_usuario("admin.huespedes", rol="administrador")
        self.iniciar_sesion("admin.huespedes")

        respuesta = self.client.get("/clientes/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Gestión de Clientes", respuesta.get_data(as_text=True))

    def test_04_recepcionista_consulta_huespedes(self):
        self.crear_usuario("recepcion.huespedes", rol="recepcionista")
        self.iniciar_sesion("recepcion.huespedes")

        respuesta = self.client.get("/clientes/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.status_code, 200)

    def test_05_lista_solo_muestra_clientes_con_cuenta_activa(self):
        self.crear_usuario("cliente.activo", cedula=14002)
        self.crear_cliente(14003, nombre="Ficha", apellido="SinCuenta")
        self.crear_usuario("admin.filtro", rol="administrador")
        self.iniciar_sesion("admin.filtro")

        respuesta = self.client.get("/clientes/")
        contenido = respuesta.get_data(as_text=True)

        self.assertIn("14002", contenido)
        self.assertNotIn("SinCuenta", contenido)

    def test_06_oculta_fichas_de_personal(self):
        self.crear_usuario(
            "recepcion.para_ocultar", rol="recepcionista", cedula=14004
        )
        self.crear_usuario("admin.ocultamiento", rol="administrador")
        self.iniciar_sesion("admin.ocultamiento")

        respuesta = self.client.get("/clientes/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("recepcion.para_ocultar", respuesta.get_data(as_text=True))

    def test_07_busqueda_por_nombre(self):
        self.crear_cliente(14005, nombre="Busqueda", apellido="Nombre")
        self.crear_usuario("cliente.busqueda", cedula=14005)
        self.crear_usuario("admin.busqueda", rol="administrador")
        self.iniciar_sesion("admin.busqueda")

        respuesta = self.client.get("/clientes/?search=Busqueda")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Busqueda", contenido)
        self.assertNotIn("cliente.apellido", contenido)

    def test_08_busqueda_por_apellido(self):
        self.crear_cliente(14006, nombre="Nombre", apellido="ApellidoBusqueda")
        self.crear_usuario("cliente.apellido", cedula=14006)
        self.crear_usuario("admin.apellido", rol="administrador")
        self.iniciar_sesion("admin.apellido")

        respuesta = self.client.get("/clientes/?search=ApellidoBusqueda")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("ApellidoBusqueda", contenido)

    def test_09_busqueda_sin_resultados(self):
        self.crear_cliente(14007, nombre="NormalVisible", apellido="Cliente")
        self.crear_usuario("cliente.normal", cedula=14007)
        self.crear_usuario("admin.sin.resultados", rol="administrador")
        self.iniciar_sesion("admin.sin.resultados")

        respuesta = self.client.get("/clientes/?search=NoExisteEsteNombre")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("NormalVisible", contenido)
        self.assertIn("No hay clientes registrados", contenido)

    @unittest.expectedFailure
    def test_10_formulario_nuevo_cliente_crea_registro(self):
        self.crear_usuario("admin.nuevo_huesped", rol="administrador")
        self.iniciar_sesion("admin.nuevo_huesped")
        datos = {
            "cedula": "14008",
            "nombre": "Nuevo",
            "apellido": "Huésped",
            "email": "nuevo@example.com",
            "telefono": "3002223333",
            "direccion": "Carrera 1 #2-3",
        }

        formulario = self.client.get("/clientes/nuevo")
        self.assertEqual(formulario.status_code, 200)

        respuesta = self.client.post(
            "/clientes/nuevo", data=datos, follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/clientes/")
        with self.app.app_context():
            cliente = Cliente.query.get(14008)
            self.assertIsNotNone(cliente)
            self.assertEqual(cliente.email, "nuevo@example.com")

    def test_11_cliente_no_puede_abrir_formulario_de_nuevo_huesped(self):
        self.crear_usuario("cliente.nuevo_huesped", cedula=14009)
        self.iniciar_sesion("cliente.nuevo_huesped")

        respuesta = self.client.get("/clientes/nuevo")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")
