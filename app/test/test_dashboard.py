"""Pruebas de la Persona 3: dashboard, indicadores y navegación por rol."""

import re
from datetime import date

from app.test.base import HotelTestCase


class TestDashboard(HotelTestCase):
    def test_01_dashboard_staff_muestra_indicadores_por_estado(self):
        self.crear_habitacion(numero=701, estado="disponible")
        self.crear_habitacion(numero=702, estado="ocupada")
        self.crear_habitacion(numero=703, estado="mantenimiento")
        self.crear_cliente(16701)
        self.crear_cliente(16702)
        self.crear_reserva(16701, 701, estado="pendiente")
        self.crear_reserva(16702, 702, estado="en curso")
        self.crear_usuario("admin.dashboard", rol="administrador")
        self.iniciar_sesion("admin.dashboard")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIsNotNone(
            re.search(
                r"Habitaciones Libres.*?<h2[^>]*>\s*1\s*</h2>",
                contenido,
                re.DOTALL,
            )
        )
        self.assertIsNotNone(
            re.search(
                r"Habitaciones Ocupadas.*?<h2[^>]*>\s*1\s*</h2>",
                contenido,
                re.DOTALL,
            )
        )
        self.assertIn("Reservas Pendientes", contenido)
        self.assertIn("Resumen Operativo", contenido)

    def test_02_dashboard_cliente_muestra_su_resumen(self):
        self.crear_cliente(16703)
        self.crear_usuario("cliente.dashboard", cedula=16703)
        activa = self.crear_habitacion(numero=704)
        finalizada = self.crear_habitacion(numero=705)
        cancelada = self.crear_habitacion(numero=706)
        self.crear_reserva(16703, activa, estado="confirmada")
        self.crear_reserva(16703, finalizada, estado="finalizada")
        self.crear_reserva(16703, cancelada, estado="cancelada")
        self.iniciar_sesion("cliente.dashboard")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertEqual(contenido.count("Total Reservas"), 1)
        self.assertIn("Su Reserva Actual", contenido)
        self.assertIn("Resumen de Estancias", contenido)
        self.assertIn("Confirmada", contenido)

    def test_03_cliente_no_ve_modulos_de_administracion(self):
        self.crear_usuario("cliente.sin_reportes", cedula=16704)
        self.iniciar_sesion("cliente.sin_reportes")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertNotIn("Reportes y Métricas", contenido)
        self.assertNotIn("Personal & Administración", contenido)

    def test_04_administrador_ve_enlaces_de_gestion(self):
        self.crear_usuario("admin.navegacion", rol="administrador")
        self.iniciar_sesion("admin.navegacion")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn("Reportes y Métricas", contenido)
        self.assertIn("Personal & Administración", contenido)
        self.assertIn("Empleados (Personal)", contenido)

    def test_05_recepcionista_no_ve_enlaces_de_administracion(self):
        self.crear_usuario("recepcion.navegacion", rol="recepcionista")
        self.iniciar_sesion("recepcion.navegacion")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn("Facturación & Finanzas", contenido)
        self.assertNotIn("Personal & Administración", contenido)
        self.assertNotIn("Empleados (Personal)", contenido)

    def test_06_limpieza_no_ve_enlaces_de_facturacion(self):
        self.crear_usuario("limpieza.navegacion", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.navegacion")

        contenido = self.client.get("/menu").get_data(as_text=True)

        self.assertIn("Limpieza & Mantenimiento", contenido)
        self.assertNotIn("Facturación & Finanzas", contenido)
        self.assertNotIn("Reportes y Métricas", contenido)
