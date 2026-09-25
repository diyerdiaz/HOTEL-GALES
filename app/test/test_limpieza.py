"""Pruebas unitarias y de integración para el módulo de Limpieza."""

from app import db
from app.models.habitacion import Habitacion
from app.models.tarea_limpieza import TareaLimpieza
from app.models.tipohabitacion import TipoHabitacion
from app.models.users import User
from app.test.base import HotelTestCase


class TestLimpieza(HotelTestCase):
    """Suite de pruebas para la asignación y ejecución de tareas de limpieza."""

    def crear_tipo_habitacion(self, nombre="Estándar"):
        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo=nombre, descripcionTipo="Tipo prueba")
            db.session.add(tipo)
            db.session.commit()
            return tipo.idTipoHabitacion

    def crear_habitacion(self, numero=101, estado="limpieza"):
        tipo_id = self.crear_tipo_habitacion(f"Tipo_{numero}")
        with self.app.app_context():
            hab = Habitacion(
                numeroHabitacion=numero,
                idTipoHabitacion=tipo_id,
                precioNoche=100000.0,
                estadoHabitacion=estado,
            )
            db.session.add(hab)
            db.session.commit()
            return hab.idHabitacion

    def crear_tarea_limpieza(self, id_habitacion, id_personal, instrucciones="Aseo general", estado="pendiente"):
        with self.app.app_context():
            tarea = TareaLimpieza(
                idHabitacion=id_habitacion,
                idPersonal=id_personal,
                instrucciones=instrucciones,
                estado=estado,
            )
            db.session.add(tarea)
            db.session.commit()
            return tarea.idTarea

    # =========================================================================
    # CONSULTA Y PERMISOS DE TAREAS
    # =========================================================================
    def test_01_consulta_de_tareas_requiere_autenticacion(self):
        """La vista de tareas de limpieza no es accesible sin inicio de sesión."""
        respuesta = self.client.get("/limpieza/tareas")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_cliente_no_puede_ver_tareas_de_limpieza(self):
        """Un usuario con rol cliente tiene denegado el acceso a las tareas de limpieza."""
        self.crear_usuario("cliente.sin_limpieza", rol="cliente", cedula=17001)
        self.iniciar_sesion("cliente.sin_limpieza")

        respuesta = self.client.get("/limpieza/tareas")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    def test_03_personal_limpieza_solo_visualiza_sus_propias_tareas(self):
        """El personal de limpieza solo ve las tareas asignadas a su identificador."""
        user1 = self.crear_usuario("limp.ana", rol="servicio_limpieza")
        user2 = self.crear_usuario("limp.carlos", rol="servicio_limpieza")

        hab1 = self.crear_habitacion(numero=201)
        hab2 = self.crear_habitacion(numero=202)

        self.crear_tarea_limpieza(hab1, user1, instrucciones="Limpieza suite Ana")
        self.crear_tarea_limpieza(hab2, user2, instrucciones="Limpieza suite Carlos")

        self.iniciar_sesion("limp.ana")
        respuesta = self.client.get("/limpieza/tareas")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("Limpieza suite Ana", contenido)
        self.assertNotIn("Limpieza suite Carlos", contenido)

    def test_04_recepcionista_y_administrador_ven_todas_las_tareas(self):
        """El recepcionista y el administrador pueden supervisar todas las tareas."""
        self.crear_usuario("recep.supervisor", rol="recepcionista")
        user1 = self.crear_usuario("limp.staff1", rol="servicio_limpieza")
        hab1 = self.crear_habitacion(numero=203)
        self.crear_tarea_limpieza(hab1, user1, instrucciones="Aseo para recepcion")

        self.iniciar_sesion("recep.supervisor")
        respuesta = self.client.get("/limpieza/tareas")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Aseo para recepcion", respuesta.get_data(as_text=True))

    # =========================================================================
    # ASIGNACIÓN DE TAREAS
    # =========================================================================
    def test_05_recepcionista_asigna_tarea_de_limpieza_exitosamente(self):
        """El recepcionista asigna una tarea de limpieza a un empleado de aseo."""
        self.crear_usuario("recep.asigna", rol="recepcionista")
        personal_id = self.crear_usuario("limp.operario", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=204)

        self.iniciar_sesion("recep.asigna")
        datos = {
            "id_habitacion": str(hab_id),
            "id_personal": str(personal_id),
            "instrucciones": "Limpieza post check-out",
        }
        respuesta = self.client.post("/limpieza/asignar", data=datos, follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/limpieza/tareas")

        with self.app.app_context():
            tarea = TareaLimpieza.query.filter_by(idHabitacion=hab_id).first()
            self.assertIsNotNone(tarea)
            self.assertEqual(tarea.idPersonal, personal_id)
            self.assertEqual(tarea.estado, "pendiente")

    def test_06_personal_de_limpieza_no_puede_asignar_tareas(self):
        """El personal de limpieza no tiene permiso para crear/asignar órdenes de aseo."""
        self.crear_usuario("limp.sin_permiso_asig", rol="servicio_limpieza")
        self.iniciar_sesion("limp.sin_permiso_asig")

        respuesta = self.client.get("/limpieza/asignar")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

    # =========================================================================
    # INICIO Y COMPLETADO DE TAREAS
    # =========================================================================
    def test_07_personal_inicia_tarea_asignada(self):
        """Al iniciar la tarea, su estado pasa a 'en curso', el empleado a 'ocupado' y la habitación a 'limpieza'."""
        user_id = self.crear_usuario("limp.inicia", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=205, estado="disponible")
        tarea_id = self.crear_tarea_limpieza(hab_id, user_id, estado="pendiente")

        self.iniciar_sesion("limp.inicia")
        respuesta = self.client.get(f"/limpieza/iniciar/{tarea_id}", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)

        with self.app.app_context():
            tarea = TareaLimpieza.query.get(tarea_id)
            self.assertEqual(tarea.estado, "en curso")
            user = User.query.get(user_id)
            self.assertEqual(user.estado_limpieza, "ocupado")
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.estadoHabitacion, "limpieza")

    def test_08_personal_completa_tarea_asignada(self):
        """Al completar la tarea, pasa a 'finalizado', el empleado a 'disponible' y la habitación a 'disponible'."""
        user_id = self.crear_usuario("limp.completa", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=206, estado="limpieza")
        tarea_id = self.crear_tarea_limpieza(hab_id, user_id, estado="en curso")

        self.iniciar_sesion("limp.completa")
        respuesta = self.client.get(f"/limpieza/completar/{tarea_id}", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)

        with self.app.app_context():
            tarea = TareaLimpieza.query.get(tarea_id)
            self.assertEqual(tarea.estado, "finalizado")
            self.assertIsNotNone(tarea.fechaFinalizacion)
            user = User.query.get(user_id)
            self.assertEqual(user.estado_limpieza, "disponible")
            hab = Habitacion.query.get(hab_id)
            self.assertEqual(hab.estadoHabitacion, "disponible")

    def test_09_personal_no_puede_iniciar_ni_completar_tareas_de_otros(self):
        """Un empleado de aseo no puede modificar el estado de una tarea asignada a otro compañero."""
        user1 = self.crear_usuario("limp.dueno", rol="servicio_limpieza")
        user2 = self.crear_usuario("limp.ajeno", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=207)
        tarea_id = self.crear_tarea_limpieza(hab_id, user1, estado="pendiente")

        self.iniciar_sesion("limp.ajeno")
        resp_iniciar = self.client.get(f"/limpieza/iniciar/{tarea_id}", follow_redirects=False)
        self.assertEqual(resp_iniciar.status_code, 302)
        self.assert_contiene_flash("No puedes iniciar una tarea que no tienes asignada")

        resp_completar = self.client.get(f"/limpieza/completar/{tarea_id}", follow_redirects=False)
        self.assertEqual(resp_completar.status_code, 302)
        self.assert_contiene_flash("No puedes completar una tarea que no tienes asignada")
