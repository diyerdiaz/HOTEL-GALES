"""
Sistema de Roles y Permisos para el Hotel
"""

# Definición de roles disponibles
ROLES = {
    'cliente': 'Cliente - Solo lectura de información',
    'administrador': 'Administrador - Control total del sistema',
    'recepcionista': 'Recepcionista - Gestión de huéspedes y reservas',
    'servicio_limpieza': 'Servicio de Limpieza - Mantenimiento y aseo'
}

# Permisos por rol
PERMISOS_ROL = {
    'cliente': [
        'ver_perfil',
        'ver_habitaciones',
        'crear_reservas',
        'ver_reservas',
        'ver_facturacion'
    ],
    'administrador': [
        'ver_usuarios',
        'crear_usuarios',
        'editar_usuarios',
        'eliminar_usuarios',
        'gestionar_roles',
        'ver_reportes',
        'gestionar_sistema',
        'ver_reservas',
        'crear_reservas',
        'editar_reservas',
        'eliminar_reservas',
        'ver_huespedes',
        'crear_huespedes',
        'editar_huespedes',
        'ver_facturacion',
        'crear_factura',
        'editar_factura',
        'ver_habitaciones',
        'crear_habitacion',
        'editar_habitacion',
        'eliminar_habitacion',
        'ver_tareas_limpieza',
        'gestionar_tareas_limpieza'
    ],
    'recepcionista': [
        'ver_reservas',
        'crear_reservas',
        'editar_reservas',
        'ver_huespedes',
        'crear_huespedes',
        'editar_huespedes',
        'ver_facturacion',
        'crear_factura',
        'ver_habitaciones',
        'actualizar_habitaciones',
        'ver_tareas_limpieza',
        'gestionar_tareas_limpieza'
    ],
    'servicio_limpieza': [
        'ver_habitaciones',
        'actualizar_habitaciones',
        'ver_tareas_limpieza'
    ]
}

# Descripción de permisos
DESCRIPCIONES_PERMISOS = {
    'ver_perfil': 'Ver perfil personal',
    'ver_tareas_limpieza': 'Ver órdenes de aseo e indicaciones',
    'gestionar_tareas_limpieza': 'Asignar tareas de limpieza a habitaciones',
    'ver_usuarios': 'Ver lista de usuarios',
    'crear_usuarios': 'Crear nuevos usuarios',
    'editar_usuarios': 'Editar información de usuarios',
    'eliminar_usuarios': 'Eliminar usuarios',
    'gestionar_roles': 'Asignar y cambiar roles',
    'ver_reportes': 'Acceder a reportes del sistema',
    'gestionar_sistema': 'Acceso a configuración del sistema',
    'ver_reservas': 'Ver reservas',
    'crear_reservas': 'Crear nuevas reservas',
    'editar_reservas': 'Editar reservas',
    'eliminar_reservas': 'Eliminar reservas',
    'ver_huespedes': 'Ver información de huéspedes',
    'crear_huespedes': 'Crear nuevos huéspedes',
    'editar_huespedes': 'Editar información de huéspedes',
    'ver_facturacion': 'Ver facturación',
    'crear_factura': 'Crear facturas',
    'editar_factura': 'Editar facturas',
    'ver_habitaciones': 'Ver estado de habitaciones',
    'crear_habitacion': 'Crear nuevas habitaciones',
    'editar_habitacion': 'Editar habitaciones existentes',
    'eliminar_habitacion': 'Eliminar habitaciones',
    'actualizar_habitaciones': 'Actualizar estado de habitaciones',
    'ver_servicios': 'Ver servicios disponibles'
}
