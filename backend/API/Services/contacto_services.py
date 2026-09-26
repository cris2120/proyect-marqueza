from Models.contacto import Contacto
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class contacto_services:
    def servListContacto():
        return orm_list("t_contacto", Contacto)

    def addContacto(tipo_contacto, contenido, proveedor_id):
        return orm_insert("t_contacto", {
            "CONT_UUID": str(uuid_lib.uuid4()),
            "CONT_TIPO_DATO": tipo_contacto,
            "CONT_CONTENIDO": contenido,
            "CONT_PROV_ID": proveedor_id,
        })
        return "Contacto agregado correctamente"

    def deleteContacto(id):
        orm_delete("t_contacto", id)

        return "Contacto eliminado correctamente"

    def updateContacto(id, tipo_contacto, contenido, proveedor_id):
        orm_update("t_contacto", id, {
            "CONT_TIPO_DATO": tipo_contacto,
            "CONT_CONTENIDO": contenido,
            "CONT_PROV_ID": proveedor_id,
        })

        return "Contacto actualizado correctamente"
