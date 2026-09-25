"""Pruebas de la Persona 3: reportes financieros y nómina."""

from datetime import date

from app.models.users import User
from app.test.base import HotelTestCase


class TestReportes(HotelTestCase):
    def crear_ingreso_mensual(
        self,
        cedula,
        nombre,
        total,
        fecha_entrada=None,
        fecha_factura=None,
    ):
        if fecha_entrada is None:
            fecha_entrada = date.today()
        self.crear_cliente(cedula, nombre=nombre, apellido="Reporte")
        habitacion_id = self.crear_habitacion(numero=600 + cedula % 100)
        reserva_id = self.crear_reserva(
            cedula, habitacion_id, estado="confirmada",
            fecha_entrada=fecha_entrada
        )
        return self.crear_factura(
            reserva_id, total=total, fecha_emision=fecha_factura
        )

    def test_01_reportes_requieren_autenticacion(self):
        respuesta = self.client.get("/admin/reportes/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_recepcionista_no_consulta_reportes(self):
        self.crear_usuario("recepcion.reportes", rol="recepcionista")
        self.iniciar_sesion("recepcion.reportes")

        respuesta = self.client.get("/admin/reportes/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("Solo administradores")

    def test_03_administrador_consulta_reportes(self):
        self.crear_usuario("admin.reportes", rol="administrador")
        self.iniciar_sesion("admin.reportes")

        respuesta = self.client.get("/admin/reportes/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "Reportes & Métricas Financieras",
            respuesta.get_data(as_text=True),
        )

    def test_04_muestra_ganancias_y_clientes_del_mes(self):
        self.crear_ingreso_mensual(16601, "Cliente", 725000)
        self.crear_usuario("admin.ganancias", rol="administrador")
        self.iniciar_sesion("admin.ganancias")
        mes = date.today().strftime("%Y-%m")

        respuesta = self.client.get(f"/admin/reportes/?mes={mes}")
        contenido = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Cliente Reporte", contenido)
        self.assertIn("$ 725.000 COP", contenido)

    def test_05_filtra_por_mes_seleccionado(self):
        self.crear_ingreso_mensual(
            16602,
            "Informehistórico",
            900000,
            fecha_entrada=date(2020, 1, 15),
            fecha_factura=date(2020, 1, 15),
        )
        self.crear_usuario("admin.meses", rol="administrador")
        self.iniciar_sesion("admin.meses")
        mes = date.today().strftime("%Y-%m")

        contenido = self.client.get(
            f"/admin/reportes/?mes={mes}"
        ).get_data(as_text=True)

        self.assertNotIn("Informehistórico Reporte", contenido)

    def test_06_mes_invalido_revierte_al_mes_actual(self):
        self.crear_ingreso_mensual(16603, "Actual", 310000)
        self.crear_usuario("admin.mes_invalido", rol="administrador")
        self.iniciar_sesion("admin.mes_invalido")

        respuesta = self.client.get("/admin/reportes/?mes=mes-invalido")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Actual Reporte", respuesta.get_data(as_text=True))

    def test_07_nomina_solo_incluye_personal_operativo(self):
        self.crear_cliente(16604, nombre="Recepción", apellido="Prueba")
        self.crear_usuario(
            "recepcion.nomina",
            rol="recepcionista",
            cedula=16604,
            salario=2000000,
        )
        self.crear_cliente(16605, nombre="Limpieza", apellido="Prueba")
        self.crear_usuario(
            "limpieza.nomina",
            rol="servicio_limpieza",
            cedula=16605,
            salario=1500000,
        )
        self.crear_cliente(16606, nombre="Cliente", apellido="FueraNómina")
        self.crear_usuario("cliente.fuera_nomina", cedula=16606)
        self.crear_usuario("admin.nomina", rol="administrador")
        self.iniciar_sesion("admin.nomina")

        contenido = self.client.get("/admin/reportes/").get_data(as_text=True)

        self.assertIn("Recepción Prueba", contenido)
        self.assertIn("Limpieza Prueba", contenido)
        self.assertNotIn("FueraNómina", contenido)
        self.assertIn("$ 3.500.000 COP", contenido)

    def test_08_administrador_actualiza_salario(self):
        usuario_id = self.crear_usuario(
            "recepcion.salario", rol="recepcionista", salario=1000000
        )
        self.crear_usuario("admin.actualiza_salario", rol="administrador")
        self.iniciar_sesion("admin.actualiza_salario")

        respuesta = self.client.post(
            f"/admin/reportes/actualizar-salario/{usuario_id}",
            data={"salario": "2500000"},
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertEqual(float(User.query.get(usuario_id).salario), 2500000.0)

    def test_09_salario_invalido_no_modifica_datos(self):
        usuario_id = self.crear_usuario(
            "recepcion.salario_malo", rol="recepcionista", salario=1200000
        )
        self.crear_usuario("admin.salario_malo", rol="administrador")
        self.iniciar_sesion("admin.salario_malo")

        respuesta = self.client.post(
            f"/admin/reportes/actualizar-salario/{usuario_id}",
            data={"salario": "no-es-numero"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Valor de salario inválido")
        with self.app.app_context():
            self.assertEqual(float(User.query.get(usuario_id).salario), 1200000.0)

    def test_10_salario_de_usuario_inexistente_devuelve_404(self):
        self.crear_usuario("admin.salario_404", rol="administrador")
        self.iniciar_sesion("admin.salario_404")

        respuesta = self.client.post(
            "/admin/reportes/actualizar-salario/999999",
            data={"salario": "1000"},
        )

        self.assertEqual(respuesta.status_code, 404)
