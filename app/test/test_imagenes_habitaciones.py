"""Pruebas de la carga de imágenes de habitaciones (máximo 3 por habitación)."""

import io
import os
from tempfile import TemporaryDirectory

from PIL import Image

from app.models.habitacion import Habitacion
from app.models.tipohabitacion import TipoHabitacion
from app.test.base import HotelTestCase


def imagen_png(nombre="foto.png"):
    contenido = io.BytesIO()
    Image.new("RGB", (40, 30), "red").save(contenido, "PNG")
    contenido.seek(0)
    return (contenido, nombre)


class TestImagenesHabitaciones(HotelTestCase):
    def setUp(self):
        super().setUp()
        # Las imágenes se guardan en una carpeta temporal, nunca en app/static
        self._carpeta = TemporaryDirectory(prefix="hotel-gales-imagenes-")
        self.app.config["HABITACIONES_UPLOAD_FOLDER"] = self._carpeta.name
        self.crear_usuario("admin.imagenes", rol="administrador")
        self.iniciar_sesion("admin.imagenes")

    def tearDown(self):
        self.app.config.pop("HABITACIONES_UPLOAD_FOLDER", None)
        self._carpeta.cleanup()
        super().tearDown()

    def tipo_id(self):
        from app import db

        with self.app.app_context():
            tipo = TipoHabitacion(nombreTipo="Suite", descripcionTipo="Tipo de prueba")
            db.session.add(tipo)
            db.session.commit()
            return tipo.idTipoHabitacion

    def datos(self, numero="501", tipo_id=None, **extra):
        return {
            "numeroHabitacion": numero,
            "idTipoHabitacion": tipo_id or self.tipo_id(),
            "precioNoche": "150000",
            "estadoHabitacion": "disponible",
            **extra,
        }

    def habitacion(self, numero):
        with self.app.app_context():
            return Habitacion.query.filter_by(numeroHabitacion=numero).first()

    def archivo_existe(self, nombre):
        return os.path.exists(os.path.join(self._carpeta.name, nombre))

    def test_01_formulario_tiene_un_solo_boton_y_acepta_archivos(self):
        contenido = self.client.get("/habitaciones/nueva").get_data(as_text=True)

        self.assertIn('enctype="multipart/form-data"', contenido)
        self.assertEqual(contenido.count('id="btnAgregarImagenes"'), 1)
        self.assertIn("Máximo 3", contenido)

    def test_02_registra_habitacion_con_varias_imagenes_juntas(self):
        respuesta = self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png("a.png"), imagen_png("b.jpg")]),
            content_type="multipart/form-data",
        )

        self.assertEqual(respuesta.status_code, 302)
        hab = self.habitacion(501)
        self.assertEqual(len(hab.imagenes), 2)
        self.assertIsNone(hab.imagen3)
        self.assertTrue(all(self.archivo_existe(img) for img in hab.imagenes))

    def test_03_nombre_del_archivo_se_reemplaza_por_uno_aleatorio(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png("../../malicioso.png")]),
            content_type="multipart/form-data",
        )

        nombre = self.habitacion(501).imagen1
        self.assertNotIn("malicioso", nombre)
        self.assertNotIn("/", nombre)
        self.assertTrue(nombre.endswith(".png"))

    def test_04_rechaza_mas_de_tres_imagenes(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png() for _ in range(4)]),
            content_type="multipart/form-data",
        )

        self.assertIsNone(self.habitacion(501))
        self.assert_contiene_flash("máximo 3 imágenes")
        self.assertEqual(os.listdir(self._carpeta.name), [])

    def test_05_rechaza_extension_no_permitida(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[(io.BytesIO(b"MZ..."), "virus.exe")]),
            content_type="multipart/form-data",
        )

        self.assertIsNone(self.habitacion(501))
        self.assert_contiene_flash("JPG, PNG o WEBP")

    def test_06_rechaza_imagen_vacia(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[(io.BytesIO(b""), "vacia.png")]),
            content_type="multipart/form-data",
        )

        self.assertIsNone(self.habitacion(501))
        self.assert_contiene_flash("vacía o dañada")

    def test_07_rechaza_archivo_que_no_es_imagen_real(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[(io.BytesIO(b"<?php echo 1; ?>"), "falsa.png")]),
            content_type="multipart/form-data",
        )

        self.assertIsNone(self.habitacion(501))
        self.assert_contiene_flash("vacía o dañada")

    def test_08_registra_habitacion_sin_imagenes(self):
        respuesta = self.client.post(
            "/habitaciones/nueva", data=self.datos(), content_type="multipart/form-data"
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.habitacion(501).imagenes, [])

    def test_09_editar_agrega_imagenes_en_espacios_libres(self):
        tipo = self.tipo_id()
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)
        original = hab.imagen1

        self.client.post(
            f"/habitaciones/editar/{hab.idHabitacion}",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )

        hab = self.habitacion(501)
        self.assertEqual(hab.imagen1, original)
        self.assertEqual(len(hab.imagenes), 3)

    def test_10_editar_rechaza_superar_el_limite(self):
        tipo = self.tipo_id()
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)

        self.client.post(
            f"/habitaciones/editar/{hab.idHabitacion}",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )

        self.assertEqual(len(self.habitacion(501).imagenes), 2)
        self.assert_contiene_flash("máximo 3 imágenes")

    def test_11_editar_elimina_imagen_marcada_y_su_archivo(self):
        tipo = self.tipo_id()
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)
        quitada = hab.imagen1

        self.client.post(
            f"/habitaciones/editar/{hab.idHabitacion}",
            data=self.datos(tipo_id=tipo, eliminar_imagen1="1"),
            content_type="multipart/form-data",
        )

        hab = self.habitacion(501)
        self.assertIsNone(hab.imagen1)
        self.assertEqual(len(hab.imagenes), 1)
        self.assertFalse(self.archivo_existe(quitada))

    def test_12_editar_muestra_imagenes_actuales(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)

        contenido = self.client.get(
            f"/habitaciones/editar/{hab.idHabitacion}"
        ).get_data(as_text=True)

        self.assertEqual(contenido.count("data-existente"), 2)
        self.assertIn(hab.imagen1, contenido)

    def test_13_detalle_muestra_galeria(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)

        contenido = self.client.get(
            f"/habitaciones/detalle/{hab.idHabitacion}"
        ).get_data(as_text=True)

        self.assertIn(f"uploads/habitaciones/{hab.imagen1}", contenido)

    def test_13b_tarjeta_del_listado_usa_la_primera_imagen_de_fondo(self):
        tipo = self.tipo_id()
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(tipo_id=tipo, imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )
        self.client.post("/habitaciones/nueva", data=self.datos(numero="502", tipo_id=tipo),
                         content_type="multipart/form-data")
        hab = self.habitacion(501)

        contenido = self.client.get("/habitaciones/").get_data(as_text=True)

        self.assertEqual(contenido.count("room-card-imagen\""), 1)
        self.assertIn(f"uploads/habitaciones/{hab.imagen1}", contenido)
        self.assertNotIn(f"uploads/habitaciones/{hab.imagen2}", contenido)

    def test_14_eliminar_habitacion_borra_sus_archivos(self):
        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png(), imagen_png()]),
            content_type="multipart/form-data",
        )
        hab = self.habitacion(501)
        imagenes = hab.imagenes

        self.client.post(f"/habitaciones/eliminar/{hab.idHabitacion}")

        self.assertIsNone(self.habitacion(501))
        self.assertFalse(any(self.archivo_existe(img) for img in imagenes))

    def test_15_recepcionista_no_puede_subir_imagenes(self):
        self.client.get("/logout")
        self.crear_usuario("recepcion.imagenes", rol="recepcionista")
        self.iniciar_sesion("recepcion.imagenes")

        self.client.post(
            "/habitaciones/nueva",
            data=self.datos(imagenes=[imagen_png()]),
            content_type="multipart/form-data",
        )

        self.assertIsNone(self.habitacion(501))
        self.assertEqual(os.listdir(self._carpeta.name), [])
