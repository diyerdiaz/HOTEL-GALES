# Pruebas de software — Persona 1

Paquete de pruebas para autenticación, perfil, usuarios, roles, huéspedes y
seguridad de Hotel Gales.

## Ejecutar

Desde la raíz del proyecto:

```bash
python -m pytest app/test -v
```

Ejecutar un archivo específico:

```bash
python -m pytest app/test/test_autenticacion.py -v
```

## Aislamiento

Las pruebas utilizan `pytest` y una base de datos SQLite temporal. No se modifica
la base de datos del proyecto y los archivos de prueba no forman parte del flujo
normal de la aplicación.

## Estado de la primera ejecución

La suite contiene **99 pruebas**:

- 94 pruebas se ejecutan correctamente.
- 5 están marcadas como `expectedFailure` porque detectan problemas del código
  actual que no se modificaron por la instrucción de no tocar la aplicación.
- Si una de esas cinco falla posteriormente en un entorno de producción, la
  prueba se marca como una falla normal y bloquea la suite.

Problemas actualmente documentados:

1. `GET /perfil/eliminar` devuelve 500 en lugar de 405.
2. `GET /clientes/nuevo` devuelve 500 porque `clientes/form.html` no existe.
3. El perfil acepta nombres de usuario que no cumplen el formato permitido.
4. El perfil permite usar un correo que ya pertenece a otra ficha.
5. El perfil permite teléfonos con un formato inválido.
