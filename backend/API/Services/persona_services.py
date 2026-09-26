from Models.persona import Persona
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class persona_services:
    def servListPersona():
        return orm_list("t_persona", Persona)

    def addPersona(nombre, seg_nombre, pri_apellido, seg_apellido, correo, direccion, identificacion, telefono):
        orm_insert("t_persona", {
            "PER_UUID": str(uuid_lib.uuid4()),
            "PER_NOMBRE": nombre,
            "PER_SEG_NOMBRE": seg_nombre,
            "PER_PRI_APELLIDO": pri_apellido,
            "PER_SEG_APELLIDO": seg_apellido,
            "PER_CORREO": correo,
            "PER_DIRECCION": direccion,
            "PER_IDENTIFICACION": identificacion,
            "PER_TELEFONO": telefono,
        })
        return "Persona agregada correctamente"

    def deletePersona(id):
        orm_delete("t_persona", id)

        return "Persona eliminada correctamente"

    def updatePersona(id, nombre, seg_nombre, pri_apellido, seg_apellido, correo, direccion, identificacion, telefono):
        orm_update("t_persona", id, {
            "PER_NOMBRE": nombre,
            "PER_SEG_NOMBRE": seg_nombre,
            "PER_PRI_APELLIDO": pri_apellido,
            "PER_SEG_APELLIDO": seg_apellido,
            "PER_CORREO": correo,
            "PER_DIRECCION": direccion,
            "PER_IDENTIFICACION": identificacion,
            "PER_TELEFONO": telefono,
        })

        return "Persona actualizada correctamente"