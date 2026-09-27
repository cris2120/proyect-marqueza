from flask import current_app

from Services.helpers import (clean, execute, hash_password, new_uuid, query,
                              resolve_rol, scalar, verify_password)


def _master_username():
    return str(current_app.config.get("MARQUEZA_MASTER_ADMIN_USERNAME", "admin")).strip()


def _master_email():
    return str(current_app.config.get("MARQUEZA_MASTER_ADMIN_EMAIL", "admin@marqueza.local")).strip().lower()


def _is_master_identity(nombre=None, correo=None):
    return (
        bool(nombre) and str(nombre).casefold() == _master_username().casefold()
    ) or (
        bool(correo) and str(correo).casefold() == _master_email().casefold()
    )


def provisionar_admin_maestro(password):
    username = _master_username()
    email = _master_email()
    role_id = resolve_rol("Administrador")
    if not username or not email or role_id is None:
        raise RuntimeError("Configura el usuario, correo y rol Administrador de la cuenta maestra.")

    matches = query(
        """SELECT USUA_ID, USUA_NOMBRE, USUA_CORREO, USUA_CONTRASENA,
                  USUA_ESTADO, USUA_DET_ETC_ID
           FROM t_usuarios
           WHERE LOWER(USUA_NOMBRE) = LOWER(%s) OR LOWER(USUA_CORREO) = LOWER(%s)""",
        (username, email),
    )
    if len(matches) > 1:
        raise RuntimeError("El usuario y correo configurados para la cuenta maestra pertenecen a filas distintas.")
    if matches:
        user = matches[0]
        email_owner = query(
            """SELECT USUA_ID FROM t_usuarios
               WHERE LOWER(USUA_CORREO) = LOWER(%s) AND USUA_ID <> %s LIMIT 1""",
            (email, user["USUA_ID"]),
        )
        if email_owner:
            raise RuntimeError("El correo configurado para la cuenta maestra ya pertenece a otro usuario.")
        password_matches = verify_password(user["USUA_CONTRASENA"], password)
        if (
            user["USUA_NOMBRE"] != username
            or user["USUA_CORREO"].casefold() != email.casefold()
            or user["USUA_ESTADO"] != "Activo"
            or user["USUA_DET_ETC_ID"] != role_id
            or not password_matches
        ):
            stored_password = user["USUA_CONTRASENA"] if password_matches else hash_password(password)
            execute(
                """UPDATE t_usuarios SET USUA_NOMBRE = %s, USUA_CORREO = %s,
                   USUA_CONTRASENA = %s, USUA_ESTADO = 'Activo', USUA_DET_ETC_ID = %s
                   WHERE USUA_ID = %s""",
                (username, email, stored_password, role_id, user["USUA_ID"]),
            )
        return user["USUA_ID"]

    if query("SELECT USUA_ID FROM t_usuarios WHERE LOWER(USUA_CORREO) = LOWER(%s) LIMIT 1", (email,)):
        raise RuntimeError("El correo configurado para la cuenta maestra ya pertenece a otro usuario.")

    return execute(
        """INSERT INTO t_usuarios
           (USUA_UUID, USUA_NOMBRE, USUA_CORREO, USUA_CONTRASENA, USUA_ESTADO, USUA_DET_ETC_ID)
           VALUES (%s, %s, %s, %s, 'Activo', %s)""",
        (new_uuid(), username, email, hash_password(password), role_id),
    )


def servListUsuarios():
    rows = query(
        """SELECT u.USUA_ID AS id, u.USUA_UUID AS uuid, u.USUA_NOMBRE AS nombre,
                  u.USUA_CORREO AS correo, d.DET_ETC_NOMBRE AS rol,
                  u.USUA_DET_ETC_ID AS rol_id, u.USUA_ESTADO AS estado,
            u.USUA_ULTIMO_ACCESO AS ultimo_acceso,
                                    CASE WHEN LOWER(u.USUA_NOMBRE) = LOWER(%s)
                                                 OR LOWER(u.USUA_CORREO) = LOWER(%s)
                                             THEN TRUE ELSE FALSE END AS protegido
           FROM t_usuarios u
           JOIN t_detalles_etc d ON d.DET_ETC_ID = u.USUA_DET_ETC_ID
        ORDER BY u.USUA_ID""",
    (_master_username(), _master_email()),
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
    if _is_master_identity(nombre, correo):
        return {"mensaje": "Ese usuario o correo está reservado para la cuenta maestra"}, 409
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
    current_user = query("SELECT USUA_ID, USUA_NOMBRE, USUA_CORREO FROM t_usuarios WHERE USUA_ID = %s", (id,))
    if not current_user:
        return {"mensaje": "Usuario no encontrado"}, 404
    if _is_master_identity(current_user[0]["USUA_NOMBRE"], current_user[0]["USUA_CORREO"]):
        return {"mensaje": "La cuenta maestra no se puede modificar"}, 403

    nombre, correo, rol_nombre, contrasena, estado, rol_id = _payload(data)
    if not nombre or not correo:
        return {"mensaje": "El nombre y el correo son obligatorios"}, 400
    if _is_master_identity(nombre, correo):
        return {"mensaje": "Ese usuario o correo está reservado para la cuenta maestra"}, 409
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
    current_user = query("SELECT USUA_ID, USUA_NOMBRE, USUA_CORREO FROM t_usuarios WHERE USUA_ID = %s", (id,))
    if not current_user:
        return {"mensaje": "Usuario no encontrado"}, 404
    if _is_master_identity(current_user[0]["USUA_NOMBRE"], current_user[0]["USUA_CORREO"]):
        return {"mensaje": "La cuenta maestra no se puede eliminar"}, 403
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
