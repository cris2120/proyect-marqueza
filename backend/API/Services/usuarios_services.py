from Models.usuarios import Usuarios
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

def servListUsuarios():
    return orm_list("t_usuarios", Usuarios)

def addUsuarios(nombre, correo, contrasena, estado, det_etc_id):
    orm_insert("t_usuarios", {
        "USUA_UUID": str(uuid_lib.uuid4()),
        "USUA_NOMBRE": nombre,
        "USUA_CORREO": correo,
        "USUA_CONTRASEÑA": contrasena,
        "USUA_ESTADO": estado,
        "USUA_DET_ETC_ID": det_etc_id,
    })
    return "Usuario agregado correctamente"

def deleteUsuarios(id):
    orm_delete("t_usuarios", id)
    return "Usuario eliminado correctamente"

def updateUsuarios(id, nombre, correo, contrasena, estado, det_etc_id):
    values = {
        "USUA_NOMBRE": nombre,
        "USUA_CORREO": correo,
        "USUA_ESTADO": estado,
        "USUA_DET_ETC_ID": det_etc_id,
    }
    if contrasena:
        values["USUA_CONTRASEÑA"] = contrasena
    orm_update("t_usuarios", id, values)
    return "Usuario actualizado correctamente"