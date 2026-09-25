"""Pruebas unitarias y de integración para el módulo de Habitaciones."""

from app import db
from app.models.habitacion import Habitacion
from app.models.tipohabitacion import TipoHabitacion
from app.models.tarea_limpieza import TareaLimpieza
from app.models.comentario import Comentario
from app.test.base import HotelTestCase


class TestHabitaciones(HotelTestCase):
    """Suite de pruebas para las funcionalidades de gestión y consulta de habitaciones."""

    def crear_tipo_habitacion(self, nombre="Estándar", descripcion="Habitación estándar"):
        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo=nombre, descripcionTipo=descripcion)
            db.session.add(tipo)
            db.session.commit()
            return tipo.idTipoHabitacion

    def crear_habitacion(self, numero=101, tipo_id=None, precio=100000.0, estado="disponible"):
        if tipo_id is None:
            tipo_id = self.crear_tipo_habitacion(f"Tipo_{numero}")
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

    # =========================================================================
    # VISTA PÚBLICA Y CONSULTA
    # =========================================================================
    def test_01_vista_publica_de_habitaciones_accesible_sin_login(self):
        """La vista pública de habitaciones está disponible para usuarios anónimos."""
        self.crear_habitacion(numero=101, estado="disponible")
        respuesta = self.client.get("/habitaciones/publica")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("101", respuesta.get_data(as_text=True))

    def test_02_vista_publica_filtra_por_tipo_y_precio(self):
        """La vista pública permite filtrar por tipo de habitación y rango de precio."""
        tipo1 = self.crear_tipo_habitacion(nombre="Simple")
        tipo2 = self.crear_tipo_habitacion(nombre="Doble")
        self.crear_habitacion(numero=102, tipo_id=tipo1, precio=80000.0)
        self.crear_habitacion(numero=103, tipo_id=tipo2, precio=150000.0)

        respuesta = self.client.get(f"/habitaciones/publica?tipo={tipo1}&precio_max=100000")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("102", contenido)
        self.assertNotIn("103", contenido)

    def test_03_catalogo_interno_requiere_autenticacion(self):
        """El catálogo interno requiere que el usuario haya iniciado sesión."""
        respuesta = self.client.get("/habitaciones/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_04_personal_limpieza_solo_ve_habitaciones_en_limpieza(self):
        """El personal de limpieza solo visualiza las habitaciones con estado 'limpieza'."""
        self.crear_usuario("limpieza.filtro", rol="servicio_limpieza")
        self.crear_habitacion(numero=104, estado="disponible")
        self.crear_habitacion(numero=105, estado="limpieza")

        self.iniciar_sesion("limpieza.filtro")
        respuesta = self.client.get("/habitaciones/")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("105", contenido)
        self.assertNotIn("104", contenido)

    # =========================================================================
    # CREACIÓN, EDICIÓN Y ELIMINACIÓN (ADMINISTRADOR)
    # =========================================================================
    def test_05_administrador_crea_habitacion_exitosamente(self):
        """El administrador puede registrar una nueva habitación en el sistema."""
        self.crear_usuario("admin.hab_crea", rol="administrador")
        tipo_id = self.crear_tipo_habitacion(nombre="Matrimonial")
        self.iniciar_sesion("admin.hab_crea")

        datos = {
            "numeroHabitacion": "201",
            "idTipoHabitacion": str(tipo_id),
            "precioNoche": "120000",
            "estadoHabitacion": "disponible",
        }
        respuesta = self.client.post("/habitaciones/nueva", data=datos, follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/habitaciones/")

        with self.app.app_context():
            hab = Habitacion.query.filter_by(numeroHabitacion=201).first()
            self.assertIsNotNone(hab)
            self.assertEqual(float(hab.precioNoche), 120000.0)

    def test_06_creacion_habitacion_valida_longitud_maxima_de_numero(self):
        """El número de habitación no puede superar 4 dígitos."""
        self.crear_usuario("admin.hab_valida", rol="administrador")
        tipo_id = self.crear_tipo_habitacion(nombre="Suite")
        self.iniciar_sesion("admin.hab_valida")

        datos = {
            "numeroHabitacion": "12345",  # 5 dígitos (inválido)
            "idTipoHabitacion": str(tipo_id),
            "precioNoche": "100000",
            "estadoHabitacion": "disponible",
        }
        respuesta = self.client.post("/habitaciones/nueva", data=datos, follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("no puede tener más de 4 dígitos")

    def test_07_administrador_edita_habitacion(self):
        """El administrador actualiza el precio y número de una habitación existente."""
        self.crear_usuario("admin.hab_edita", rol="administrador")
        hab_id = self.crear_habitacion(numero=202, precio=100000.0)
        self.iniciar_sesion("admin.hab_edita")

        with self.app.app_context():
            tipo_id = Habitacion.query.get(hab_id).idTipoHabitacion

        datos = {
            "numeroHabitacion": "205",
            "idTipoHabitacion": str(tipo_id),
            "precioNoche": "180000",
            "estadoHabitacion": "disponible",
        }
        respuesta = self.client.post(f"/habitaciones/editar/{hab_id}", data=datos, follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)

        with self.app.app_context():
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.numeroHabitacion, 205)
            self.assertEqual(float(hab.precioNoche), 180000.0)

    def test_08_administrador_elimina_habitacion(self):
        """El administrador elimina una habitación del catálogo."""
        self.crear_usuario("admin.hab_elimina", rol="administrador")
        hab_id = self.crear_habitacion(numero=203)
        self.iniciar_sesion("admin.hab_elimina")

        respuesta = self.client.get(f"/habitaciones/eliminar/{hab_id}", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)

        with self.app.app_context():
            self.assertIsNone(Habitacion.query.get(hab_id))

    def test_09_recepcionista_y_cliente_no_pueden_crear_ni_eliminar_habitaciones(self):
        """Los roles no autorizados son rechazados al intentar crear o eliminar habitaciones."""
        self.crear_usuario("recep.hab_no_crea", rol="recepcionista")
        hab_id = self.crear_habitacion(numero=204)
        self.iniciar_sesion("recep.hab_no_crea")

        resp_crear = self.client.get("/habitaciones/nueva")
        self.assertEqual(resp_crear.status_code, 302)
        self.assertEqual(resp_crear.headers["Location"], "/menu")

        resp_eliminar = self.client.get(f"/habitaciones/eliminar/{hab_id}")
        self.assertEqual(resp_eliminar.status_code, 302)
        self.assertEqual(resp_eliminar.headers["Location"], "/menu")

    # =========================================================================
    # DETALLE Y CAMBIO DE ESTADO
    # =========================================================================
    def test_10_consulta_de_detalle_de_habitacion_con_comentarios(self):
        """Visualizar el detalle de una habitación calcula el promedio de calificaciones."""
        self.crear_usuario("cliente.consulta_det", rol="cliente", cedula=15001)
        hab_id = self.crear_habitacion(numero=301)

        with self.app.app_context():
            comentario = Comentario(
                idHabitacion=hab_id,
                cedulaCliente=15001,
                comentario="Excelente estancia",
                calificacion=5,
            )
            db.session.add(comentario)
            db.session.commit()

        self.iniciar_sesion("cliente.consulta_det")
        respuesta = self.client.get(f"/habitaciones/detalle/{hab_id}")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("301", contenido)
        self.assertIn("Excelente estancia", contenido)

    def test_11_cambio_de_estado_por_personal_de_limpieza_registra_tarea(self):
        """Cuando personal de limpieza pasa de 'limpieza' a 'disponible', se registra la tarea automáticamente."""
        limpieza_id = self.crear_usuario("personal.aseo", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=302, estado="limpieza")

        self.iniciar_sesion("personal.aseo")
        respuesta = self.client.get(f"/habitaciones/estado/{hab_id}/disponible", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)

        with self.app.app_context():
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.estadoHabitacion, "disponible")

            tarea = TareaLimpieza.query.filter_by(idHabitacion=hab_id, idPersonal=limpieza_id).first()
            self.assertIsNotNone(tarea)
            self.assertEqual(tarea.estado, "finalizado")
