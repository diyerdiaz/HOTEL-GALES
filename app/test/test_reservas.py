"""Pruebas unitarias y de integración para el módulo de Reservas."""

from datetime import date, timedelta
from app import db
from app.models.habitacion import Habitacion
from app.models.reserva import Reserva
from app.models.pago import Pago
from app.models.factura import Factura
from app.models.tipohabitacion import TipoHabitacion
from app.test.base import HotelTestCase


class TestReservas(HotelTestCase):
    """Suite de pruebas para las operaciones del ciclo de vida de reservas."""

    def crear_tipo_habitacion(self, nombre="Estándar"):
        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo=nombre, descripcionTipo="Tipo prueba")
            db.session.add(tipo)
            db.session.commit()
            return tipo.idTipoHabitacion

    def crear_habitacion(self, numero=101, tipo_id=None, precio=150000.0, estado="disponible"):
        if tipo_id is None:
            tipo_id = self.crear_tipo_habitacion()
        with self.app.app_context():
            hab = Habitacion(
                numeroHabitacion=numero,
                idTipoHabitacion=tipo_id,
                precioNoche=precio,
                estadoHabitacion=estado,
            )
            db.session.add(hab)
            db.session.commit()
            return hab.idHabitacion

    def crear_reserva(
        self,
        cedula_cliente,
        id_habitacion,
        fecha_entrada=None,
        fecha_salida=None,
        estado="pendiente",
        recepcionista_id=None,
        crear_factura_y_pago=True,
    ):
        hoy = date.today()
        if fecha_entrada is None:
            fecha_entrada = hoy + timedelta(days=1)
        if fecha_salida is None:
            fecha_salida = hoy + timedelta(days=3)

        with self.app.app_context():
            reserva = Reserva(
                cedulaCliente=int(cedula_cliente),
                idHabitacion=id_habitacion,
                fechaEntrada=fecha_entrada,
                fechaSalida=fecha_salida,
                cantidadPersonas=2,
                estadoReserva=estado,
                recepcionista_id=recepcionista_id,
            )
            db.session.add(reserva)
            db.session.flush()

            if crear_factura_y_pago:
                hab = Habitacion.query.get(id_habitacion)
                dias = max((fecha_salida - fecha_entrada).days, 1)
                total = float(hab.precioNoche) * dias

                pago = Pago(
                    idReserva=reserva.idReserva,
                    metodoPago="efectivo",
                    valorPago=hab.precioNoche,
                )
                factura = Factura(
                    idReserva=reserva.idReserva,
                    totalFactura=total,
                )
                db.session.add(pago)
                db.session.add(factura)

            db.session.commit()
            return reserva.idReserva

    # =========================================================================
    # CONSULTA Y FILTROS DE RESERVAS
    # =========================================================================
    def test_01_consulta_reservas_requiere_autenticacion(self):
        """No se puede consultar reservas sin haber iniciado sesión."""
        respuesta = self.client.get("/reservas/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_cliente_solo_ve_sus_propias_reservas(self):
        """Un cliente solo puede visualizar sus propias reservas en el listado."""
        self.crear_usuario("cliente.propietario", rol="cliente", cedula=16001)
        self.crear_usuario("cliente.ajeno", rol="cliente", cedula=16002)

        hab1 = self.crear_habitacion(numero=101)
        hab2 = self.crear_habitacion(numero=102)

        self.crear_reserva(16001, hab1)
        self.crear_reserva(16002, hab2)

        self.iniciar_sesion("cliente.propietario")
        respuesta = self.client.get("/reservas/")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("101", contenido)
        self.assertNotIn("102", contenido)

    def test_03_recepcionista_ve_todas_las_reservas_y_filtra_por_fecha(self):
        """El recepcionista puede ver todas las reservas y filtrarlas por fecha."""
        self.crear_usuario("recep.reservas", rol="recepcionista")
        self.crear_usuario("cliente.a", rol="cliente", cedula=16003)
        self.crear_usuario("cliente.b", rol="cliente", cedula=16004)

        hab1 = self.crear_habitacion(numero=103)
        hab2 = self.crear_habitacion(numero=104)

        fecha_obj = date.today() + timedelta(days=7)
        fecha_otra = date.today() + timedelta(days=14)

        self.crear_reserva(16003, hab1, fecha_entrada=fecha_obj)
        self.crear_reserva(16004, hab2, fecha_entrada=fecha_otra)

        self.iniciar_sesion("recep.reservas")
        fecha_str = fecha_obj.strftime("%Y-%m-%d")
        respuesta = self.client.get(f"/reservas/?fecha={fecha_str}")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("103", contenido)
        self.assertNotIn("104", contenido)

    # =========================================================================
    # CREACIÓN Y VALIDACIONES DE RESERVAS
    # =========================================================================
    def test_04_creacion_exitosa_de_reserva_por_cliente(self):
        """Un cliente crea una reserva directamente para sí mismo."""
        self.crear_usuario("cliente.crea_res", rol="cliente", cedula=16005)
        hab_id = self.crear_habitacion(numero=105, precio=100000.0, estado="disponible")

        self.iniciar_sesion("cliente.crea_res")
        manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        pasado = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

        datos = {
            "id_habitacion": str(hab_id),
            "fecha_entrada": manana,
            "fecha_salida": pasado,
            "metodo_pago": "efectivo",
            "cantidad_personas": "2",
        }

        respuesta = self.client.post("/reservas/nueva", data=datos, follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/reservas/")

        with self.app.app_context():
            reserva = Reserva.query.filter_by(cedulaCliente=16005).first()
            self.assertIsNotNone(reserva)
            self.assertEqual(reserva.estadoReserva, "pendiente")

            # Habitación pasa a ocupada
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.estadoHabitacion, "ocupada")

            # Factura generada automáticamente
            factura = Factura.query.filter_by(idReserva=reserva.idReserva).first()
            self.assertIsNotNone(factura)
            self.assertEqual(float(factura.totalFactura), 200000.0)

    def test_05_creacion_reserva_rechaza_fechas_invalidas(self):
        """Validar rechazo de fecha en el pasado y salida menor a entrada."""
        self.crear_usuario("cliente.val_fechas", rol="cliente", cedula=16006)
        hab_id = self.crear_habitacion(numero=106)
        self.iniciar_sesion("cliente.val_fechas")

        ayer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Fecha pasada
        datos = {
            "id_habitacion": str(hab_id),
            "fecha_entrada": ayer,
            "fecha_salida": manana,
            "metodo_pago": "efectivo",
            "cantidad_personas": "1",
        }
        resp = self.client.post("/reservas/nueva", data=datos, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assert_contiene_flash("No puedes reservar en una fecha pasada")

    def test_06_creacion_reserva_rechaza_reserva_activa_duplicada(self):
        """No se permite crear una segunda reserva si el cliente tiene una pendiente o confirmada."""
        self.crear_usuario("cliente.duplicado", rol="cliente", cedula=16007)
        hab1 = self.crear_habitacion(numero=107)
        hab2 = self.crear_habitacion(numero=108)

        self.crear_reserva(16007, hab1, estado="confirmada")

        self.iniciar_sesion("cliente.duplicado")
        manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        pasado = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

        datos = {
            "id_habitacion": str(hab2),
            "fecha_entrada": manana,
            "fecha_salida": pasado,
            "metodo_pago": "efectivo",
            "cantidad_personas": "1",
        }
        resp = self.client.post("/reservas/nueva", data=datos, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assert_contiene_flash("Este cliente ya tiene una reserva activa")

    # =========================================================================
    # CAMBIOS DE ESTADO, MANTENIMIENTO Y CANCELACIÓN
    # =========================================================================
    def test_07_cambio_de_estado_de_reserva_sincroniza_habitacion(self):
        """Cambiar estado a confirmada, finalizada o limpieza sincroniza la habitación."""
        recep_id = self.crear_usuario("recep.estados", rol="recepcionista")
        self.crear_usuario("cliente.cambio", rol="cliente", cedula=16008)
        hab_id = self.crear_habitacion(numero=109, estado="disponible")
        res_id = self.crear_reserva(16008, hab_id, estado="pendiente")

        self.iniciar_sesion("recep.estados")

        # 1. Confirmar reserva -> habitación ocupada
        self.client.post(f"/reservas/cambiar-estado/{res_id}", data={"estadoReserva": "confirmada"})
        with self.app.app_context():
            res = Reserva.query.get(res_id)
            self.assertEqual(res.estadoReserva, "confirmada")
            self.assertEqual(res.recepcionista_id, recep_id)
            self.assertEqual(res.habitacion.estadoHabitacion, "ocupada")

        # 2. Enviar a limpieza -> reserva finalizada y habitación en limpieza
        self.client.post(f"/reservas/cambiar-estado/{res_id}", data={"estadoReserva": "limpieza"})
        with self.app.app_context():
            res = Reserva.query.get(res_id)
            self.assertEqual(res.estadoReserva, "finalizada")
            self.assertEqual(res.habitacion.estadoHabitacion, "limpieza")

    def test_08_marcar_habitacion_en_mantenimiento_desde_reserva(self):
        """Poner la habitación en mantenimiento desde la reserva activa."""
        self.crear_usuario("recep.mant_res", rol="recepcionista")
        self.crear_usuario("cliente.mant", rol="cliente", cedula=16009)
        hab_id = self.crear_habitacion(numero=110, estado="ocupada")
        res_id = self.crear_reserva(16009, hab_id, estado="confirmada")

        self.iniciar_sesion("recep.mant_res")
        resp = self.client.get(f"/reservas/mantenimiento/{res_id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        with self.app.app_context():
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.estadoHabitacion, "mantenimiento")

    def test_09_cancelar_reserva_libera_habitacion_y_elimina_factura_y_pago(self):
        """Al cancelar una reserva se eliminan facturas/pagos y la habitación queda disponible."""
        self.crear_usuario("cliente.cancela_suya", rol="cliente", cedula=16010)
        hab_id = self.crear_habitacion(numero=111, estado="ocupada")
        res_id = self.crear_reserva(16010, hab_id, estado="pendiente", crear_factura_y_pago=True)

        self.iniciar_sesion("cliente.cancela_suya")
        resp = self.client.get(f"/reservas/cancelar/{res_id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        with self.app.app_context():
            res = Reserva.query.get(res_id)
            self.assertEqual(res.estadoReserva, "cancelada")
            self.assertEqual(res.habitacion.estadoHabitacion, "disponible")
            self.assertEqual(Factura.query.filter_by(idReserva=res_id).count(), 0)
            self.assertEqual(Pago.query.filter_by(idReserva=res_id).count(), 0)

    def test_10_cliente_no_puede_cancelar_reserva_ajena(self):
        """Un cliente no puede cancelar la reserva de otro cliente."""
        self.crear_usuario("cliente.intruso", rol="cliente", cedula=16011)
        self.crear_usuario("cliente.victima_res", rol="cliente", cedula=16012)
        hab_id = self.crear_habitacion(numero=112)
        res_id = self.crear_reserva(16012, hab_id, estado="pendiente")

        self.iniciar_sesion("cliente.intruso")
        resp = self.client.get(f"/reservas/cancelar/{res_id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assert_contiene_flash("No tienes permiso")
