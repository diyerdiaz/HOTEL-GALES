"""Pruebas unitarias y de integración para el módulo de Mantenimiento."""

from datetime import datetime, date
from app import db
from app.models.habitacion import Habitacion
from app.models.tipohabitacion import TipoHabitacion
from app.models.mantenimiento import MantenimientoHabitacion
from app.models.tarea_limpieza import TareaLimpieza
from app.models.empleado import Empleado
from app.models.rolempleado import RolEmpleado
from app.models.users import User
from app.test.base import HotelTestCase


class TestMantenimiento(HotelTestCase):
    """Suite de pruebas para la gestión y monitoreo de mantenimientos y disponibilidad de personal."""

    def crear_tipo_habitacion(self, nombre="Estándar"):
        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo=nombre, descripcionTipo="Tipo prueba")
            db.session.add(tipo)
            db.session.commit()
            return tipo.idTipoHabitacion

    def crear_habitacion(self, numero=101, estado="mantenimiento"):
        tipo_id = self.crear_tipo_habitacion(f"Tipo_{numero}")
        with self.app.app_context():
            hab = Habitacion(
                numeroHabitacion=numero,
                idTipoHabitacion=tipo_id,
                precioNoche=120000.0,
                estadoHabitacion=estado,
            )
            db.session.add(hab)
            db.session.commit()
            return hab.idHabitacion

    def crear_mantenimiento(self, id_habitacion, descripcion="Reparación eléctrica", costo=50000.0, estado="en proceso"):
        with self.app.app_context():
            # Crear un rol y ficha de empleado técnico
            rol = RolEmpleado(nombreRol="Técnico", descripcionRol="Mantenimiento")
            db.session.add(rol)
            db.session.flush()

            emp = Empleado(
                nombre="Pedro",
                apellido="Tecnico",
                idRolEmpleado=rol.idRolEmpleado,
                cargo="Técnico de Mantenimiento",
            )
            db.session.add(emp)
            db.session.flush()

            mant = MantenimientoHabitacion(
                idHabitacion=id_habitacion,
                idEmpleado=emp.idEmpleado,
                descripcionProblema=descripcion,
                costoMantenimiento=costo,
                estadoMantenimiento=estado,
            )
            db.session.add(mant)
            db.session.commit()
            return mant.idMantenimiento

    # =========================================================================
    # ACCESO Y PERMISOS DEL MÓDULO DE MANTENIMIENTO
    # =========================================================================
    def test_01_mantenimiento_requiere_autenticacion(self):
        """No se puede acceder a la sección de mantenimiento sin iniciar sesión."""
        respuesta = self.client.get("/mantenimientos/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_cliente_y_servicio_limpieza_no_acceden_a_mantenimiento(self):
        """Los roles de cliente y limpieza son redirigidos al intentar acceder a mantenimientos."""
        self.crear_usuario("cliente.sin_mant", rol="cliente", cedula=18002)
        self.iniciar_sesion("cliente.sin_mant")

        resp_cliente = self.client.get("/mantenimientos/")
        self.assertEqual(resp_cliente.status_code, 302)
        self.assertEqual(resp_cliente.headers["Location"], "/menu")
        self.assert_contiene_flash("No tienes permiso")

        self.crear_usuario("limpieza.sin_mant", rol="servicio_limpieza")
        self.iniciar_sesion("limpieza.sin_mant")

        resp_limp = self.client.get("/mantenimientos/")
        self.assertEqual(resp_limp.status_code, 302)
        self.assertEqual(resp_limp.headers["Location"], "/menu")

    def test_03_recepcionista_y_administrador_acceden_a_mantenimiento(self):
        """El administrador y recepcionista pueden acceder a la vista de mantenimientos."""
        self.crear_usuario("recep.mant_ok", rol="recepcionista")
        self.iniciar_sesion("recep.mant_ok")

        respuesta = self.client.get("/mantenimientos/")
        self.assertEqual(respuesta.status_code, 200)

    # =========================================================================
    # CONSULTA, FILTROS Y REGISTROS DE MANTENIMIENTO
    # =========================================================================
    def test_04_consulta_lista_de_mantenimientos_y_personal(self):
        """La vista muestra la sección de mantenimientos y el personal de limpieza operativo."""
        self.crear_usuario("admin.mant_ver", rol="administrador")
        self.crear_usuario("limp.operario1", rol="servicio_limpieza")
        hab_id = self.crear_habitacion(numero=301)
        self.crear_mantenimiento(hab_id, descripcion="Cambio de griferia")

        self.iniciar_sesion("admin.mant_ver")
        respuesta = self.client.get("/mantenimientos/")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("Personal de Limpieza", contenido)
        self.assertIn("limp.operario1", contenido)

    def test_05_busqueda_de_personal_por_nombre(self):
        """Permite filtrar el personal de limpieza por nombre de usuario."""
        self.crear_usuario("admin.mant_busca", rol="administrador")
        self.crear_usuario("limp.maria", rol="servicio_limpieza")
        self.crear_usuario("limp.jose", rol="servicio_limpieza")

        self.iniciar_sesion("admin.mant_busca")
        respuesta = self.client.get("/mantenimientos/?search=maria")
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.get_data(as_text=True)
        self.assertIn("limp.maria", contenido)
        self.assertNotIn("limp.jose", contenido)

    # =========================================================================
    # CAMBIO DE ESTADO DE DISPONIBILIDAD DEL PERSONAL
    # =========================================================================
    def test_06_cambiar_estado_de_disponibilidad_de_personal(self):
        """Permite alternar el estado de disponibilidad del personal de limpieza entre disponible y ocupado."""
        self.crear_usuario("recep.cambia_estado", rol="recepcionista")
        staff_id = self.crear_usuario("limp.cambio", rol="servicio_limpieza")

        self.iniciar_sesion("recep.cambia_estado")
        respuesta = self.client.get(f"/mantenimientos/cambiar-estado/{staff_id}/ocupado", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/mantenimientos/")

        with self.app.app_context():
            user = User.query.get(staff_id)
            self.assertEqual(user.estado_limpieza, "ocupado")

    def test_07_cambiar_estado_rechaza_roles_que_no_son_limpieza(self):
        """No se puede cambiar el estado de disponibilidad a usuarios que no son de servicio de limpieza."""
        self.crear_usuario("admin.valida_staff", rol="administrador")
        cliente_id = self.crear_usuario("cliente.no_staff", rol="cliente", cedula=18003)

        self.iniciar_sesion("admin.valida_staff")
        respuesta = self.client.get(f"/mantenimientos/cambiar-estado/{cliente_id}/ocupado", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Usuario no es personal de limpieza")

    def test_08_cambiar_estado_rechaza_estado_invalido(self):
        """Rechazar estados diferentes a 'disponible' u 'ocupado'."""
        self.crear_usuario("admin.valida_estado", rol="administrador")
        staff_id = self.crear_usuario("limp.invalido", rol="servicio_limpieza")

        self.iniciar_sesion("admin.valida_estado")
        respuesta = self.client.get(f"/mantenimientos/cambiar-estado/{staff_id}/estado_falso", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("Estado inválido")
