# Pruebas de software — Personas 1 y 3

Paquete de pruebas automatizadas de Hotel Gales. Utiliza `pytest`, el cliente de
pruebas de Flask y una base de datos SQLite temporal.

## Ejecutar toda la suite

Desde la raíz del proyecto:

```bash
python -m pytest -v
```

Ejecutar un archivo específico:

```bash
python -m pytest app/test/test_autenticacion.py -v
```

Ejecutar únicamente las pruebas de la Persona 3:

```bash
python -m pytest \
  app/test/test_facturacion.py \
  app/test/test_pagos.py \
  app/test/test_consumos.py \
  app/test/test_servicios.py \
  app/test/test_notificaciones.py \
  app/test/test_comentarios.py \
  app/test/test_reportes.py \
  app/test/test_dashboard.py \
  app/test/test_interfaz.py \
  app/test/test_idiomas.py -v
```

## Persona 1 — Acceso y gestión de cuentas

| Archivo | Cobertura | Pruebas |
|---|---|---:|
| `test_autenticacion.py` | Login, registro, logout y recuperación de contraseña | 30 |
| `test_perfil.py` | Perfil, contraseña y eliminación de cuenta | 14 |
| `test_usuarios.py` | Usuarios, roles, permisos e historiales | 23 |
| `test_roles.py` | CRUD de roles internos | 8 |
| `test_huespedes.py` | Directorio, búsqueda y filtros de huéspedes | 11 |
| `test_seguridad.py` | Sesión, autorización, roles simulados y datos sensibles | 13 |
| **Total Persona 1** | | **99** |

## Persona 3 — Facturación, avisos e interfaz

| Archivo | Cobertura | Pruebas |
|---|---|---:|
| `test_facturacion.py` | Facturas, permisos, QR y validación pública | 11 |
| `test_pagos.py` | Registro y consulta de pagos | 6 |
| `test_consumos.py` | Consumos por reserva y permisos | 5 |
| `test_servicios.py` | Servicios y categorías | 9 |
| `test_notificaciones.py` | Notificaciones, contador AJAX y avisos automáticos | 12 |
| `test_comentarios.py` | Reseñas, calificaciones, validación y seguridad | 17 |
| `test_reportes.py` | Ganancias, filtros mensuales, nómina y salarios | 10 |
| `test_dashboard.py` | Indicadores y navegación según el rol | 6 |
| `test_interfaz.py` | Diseño responsivo, sidebar y página 404 | 4 |
| `test_idiomas.py` | Español, inglés y persistencia del idioma | 5 |
| **Total Persona 3** | | **85** |

## Estado verificado

La suite completa contiene **184 pruebas**:

- **179 passed**: se ejecutan correctamente.
- **5 xfailed**: problemas ya conocidos del código actual, documentados mediante
  `expectedFailure` y no corregidos para no modificar la aplicación.

Resultado obtenido:

```text
179 passed, 5 xfailed
```

## Problemas actualmente documentados

1. `GET /perfil/eliminar` devuelve 500 en lugar de 405.
2. `GET /clientes/nuevo` devuelve 500 porque `clientes/form.html` no existe.
3. El perfil acepta nombres de usuario que no cumplen el formato permitido.
4. El perfil permite usar un correo que ya pertenece a otra ficha.
5. El perfil permite teléfonos con un formato inválido.

## Aislamiento

- No se modifica la base de datos del proyecto.
- No se escriben archivos de producción.
- Las pruebas no forman parte del flujo normal de la aplicación.
- GitHub Actions ejecuta toda la suite con Python 3.11 y `pytest`.
