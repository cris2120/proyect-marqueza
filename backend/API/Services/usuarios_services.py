from Services.helpers import (clean, execute, hash_password, new_uuid, query,
                              resolve_rol, scalar)


def servListUsuarios():
    rows = query(
        """SELECT u.USUA_ID AS id, u.USUA_UUID AS uuid, u.USUA_NOMBRE AS nombre,
                  u.USUA_CORREO AS correo, d.DET_ETC_NOMBRE AS rol,
                  u.USUA_DET_ETC_ID AS rol_id, u.USUA_ESTADO AS estado,
                  u.USUA_ULTIMO_ACCESO AS ultimo_acceso
           FROM t_usuarios u
           JOIN t_detalles_etc d ON d.DET_ETC_ID = u.USUA_DET_ETC_ID
           ORDER BY u.USUA_ID"""
    )
    return rows


def _payload(data):
    nombre = clean(data.get("nombre"))
    correo = clean(data.get("correo"))
    rol_nombre = clean(data.get("rol"), "Empleado")
    contrasena = data.get("contrasena")
    estado = clean(data.get("estado"), "Activo")
    if estado not in ("Activo", "Inactivo"):
        estado = "Activo"
    rol_id = resolve_rol(rol_nombre)
    if rol_id is None:
        try:
            rol_id = int(rol_nombre)
        except (TypeError, ValueError):
            rol_id = 2
    return nombre, correo, rol_nombre, contrasena, estado, rol_id


def addUsuarios(data):
    nombre, correo, rol_nombre, contrasena, estado, rol_id = _payload(data)
    if not nombre or not correo:
        return {"mensaje": "El nombre y el correo son obligatorios"}, 400
    if not contrasena:
        return {"mensaje": "La contrasena es obligatoria"}, 400
    if query("SELECT USUA_ID FROM t_usuarios WHERE USUA_CORREO = %s OR USUA_NOMBRE = %s", (correo, nombre)):
        return {"mensaje": "Ya existe un usuario con ese nombre o correo"}, 409

    usua_id = execute(
        """INSERT INTO t_usuarios
           (USUA_UUID, USUA_NOMBRE, USUA_CORREO, USUA_CONTRASENA, USUA_ESTADO, USUA_DET_ETC_ID)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (new_uuid(), nombre, correo, hash_password(contrasena), estado, rol_id),
    )
    return {"mensaje": "Usuario agregado correctamente", "id": usua_id}, 201


def updateUsuarios(id, data):
    if not query("SELECT USUA_ID FROM t_usuarios WHERE USUA_ID = %s", (id,)):
        return {"mensaje": "Usuario no encontrado"}, 404

    nombre, correo, rol_nombre, contrasena, estado, rol_id = _payload(data)
    if not nombre or not correo:
        return {"mensaje": "El nombre y el correo son obligatorios"}, 400
    if query("SELECT USUA_ID FROM t_usuarios WHERE (USUA_CORREO = %s OR USUA_NOMBRE = %s) AND USUA_ID <> %s",
             (correo, nombre, id)):
        return {"mensaje": "Ya existe otro usuario con ese nombre o correo"}, 409

    if contrasena:
        execute(
            """UPDATE t_usuarios SET USUA_NOMBRE = %s, USUA_CORREO = %s, USUA_CONTRASENA = %s,
               USUA_ESTADO = %s, USUA_DET_ETC_ID = %s
               WHERE USUA_ID = %s""",
            (nombre, correo, hash_password(contrasena), estado, rol_id, id),
        )
    else:
        execute(
            """UPDATE t_usuarios SET USUA_NOMBRE = %s, USUA_CORREO = %s, USUA_ESTADO = %s,
               USUA_DET_ETC_ID = %s
               WHERE USUA_ID = %s""",
            (nombre, correo, estado, rol_id, id),
        )
    return {"mensaje": "Usuario actualizado correctamente", "id": id}, 200


def deleteUsuarios(id):
    if not query("SELECT USUA_ID FROM t_usuarios WHERE USUA_ID = %s", (id,)):
        return {"mensaje": "Usuario no encontrado"}, 404
    try:
        execute("DELETE FROM t_usuarios WHERE USUA_ID = %s", (id,))
    except Exception:
        return {"mensaje": "No se puede eliminar: el usuario tiene ventas o cotizaciones asociadas"}, 409
    return {"mensaje": "Usuario eliminado correctamente"}, 200


def buscar_usuario(identificador):
    """Busca por correo o por nombre de usuario."""
    return query(
        """SELECT u.USUA_ID AS id, u.USUA_NOMBRE AS nombre, u.USUA_CORREO AS correo,
                  u.USUA_CONTRASENA AS contrasena, u.USUA_ESTADO AS estado,
                  u.USUA_DET_ETC_ID AS rol_id, d.DET_ETC_NOMBRE AS rol
           FROM t_usuarios u
           JOIN t_detalles_etc d ON d.DET_ETC_ID = u.USUA_DET_ETC_ID
           WHERE u.USUA_CORREO = %s OR u.USUA_NOMBRE = %s
           LIMIT 1""",
        (identificador, identificador),
    )


def marcar_ultimo_acceso(user_id):
    execute("UPDATE t_usuarios SET USUA_ULTIMO_ACCESO = NOW() WHERE USUA_ID = %s", (user_id,))


def obtener_rol(user_id):
    return scalar(
        """SELECT d.DET_ETC_NOMBRE FROM t_usuarios u
           JOIN t_detalles_etc d ON d.DET_ETC_ID = u.USUA_DET_ETC_ID
           WHERE u.USUA_ID = %s""",
        (user_id,),
    )
