"""Pruebas de los roles internos del personal."""

from app.models.rolempleado import RolEmpleado
from app.test.base import HotelTestCase


class TestRoles(HotelTestCase):
    def test_01_roles_requieren_inicio_de_sesion(self):
        respuesta = self.client.get("/admin/roles-empleados/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.headers["Location"])

    def test_02_usuario_no_administrador_no_accede_a_roles(self):
        self.crear_usuario("recepcion.roles", rol="recepcionista")
        self.iniciar_sesion("recepcion.roles")

        respuesta = self.client.get("/admin/roles-empleados/")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/menu")
        self.assert_contiene_flash("Solo administradores")

    def test_03_administrador_consulta_roles(self):
        self.crear_usuario("admin.roles", rol="administrador")
        self.iniciar_sesion("admin.roles")

        respuesta = self.client.get("/admin/roles-empleados/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Roles Definidos", respuesta.get_data(as_text=True))

    def test_04_administrador_crea_rol(self):
        self.crear_usuario("admin.crea_rol", rol="administrador")
        self.iniciar_sesion("admin.crea_rol")

        respuesta = self.client.post(
            "/admin/roles-empleados/crear",
            data={"nombre": "Auditor", "descripcion": "Revisión de operaciones"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            rol = RolEmpleado.query.filter_by(nombreRol="Auditor").one()
            self.assertEqual(rol.descripcionRol, "Revisión de operaciones")

    def test_05_creacion_rechaza_nombre_vacio(self):
        self.crear_usuario("admin.rol_vacio", rol="administrador")
        self.iniciar_sesion("admin.rol_vacio")

        respuesta = self.client.post(
            "/admin/roles-empleados/crear",
            data={"nombre": "", "descripcion": "Sin nombre"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assert_contiene_flash("El nombre del rol es obligatorio")
        with self.app.app_context():
            self.assertEqual(RolEmpleado.query.count(), 0)

    def test_06_administrador_edita_rol(self):
        rol_id = self.crear_rol_empleado("Recepción", "Rol anterior")
        self.crear_usuario("admin.edita_rol", rol="administrador")
        self.iniciar_sesion("admin.edita_rol")

        respuesta = self.client.post(
            f"/admin/roles-empleados/editar/{rol_id}",
            data={"nombre": "Recepción y atención", "descripcion": "Rol actualizado"},
            follow_redirects=False,
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            rol = RolEmpleado.query.get(rol_id)
            self.assertEqual(rol.nombreRol, "Recepción y atención")
            self.assertEqual(rol.descripcionRol, "Rol actualizado")

    def test_07_administrador_elimina_rol(self):
        rol_id = self.crear_rol_empleado("Temporal", "Debe eliminarse")
        self.crear_usuario("admin.elimina_rol", rol="administrador")
        self.iniciar_sesion("admin.elimina_rol")

        respuesta = self.client.post(
            f"/admin/roles-empleados/eliminar/{rol_id}", follow_redirects=False
        )

        self.assertEqual(respuesta.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(RolEmpleado.query.get(rol_id))

    def test_08_operaciones_sobre_rol_inexistente_devuelven_404(self):
        self.crear_usuario("admin.rol_inexistente", rol="administrador")
        self.iniciar_sesion("admin.rol_inexistente")

        editar = self.client.post(
            "/admin/roles-empleados/editar/999999", data={"nombre": "No existe"}
        )
        eliminar = self.client.post(
            "/admin/roles-empleados/eliminar/999999"
        )

        self.assertEqual(editar.status_code, 404)
        self.assertEqual(eliminar.status_code, 404)
