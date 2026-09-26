from Models.detalles_etc import Detalles_etc
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class detalles_etc_services:
    def servListDetalles_etc():
        return orm_list("t_detalles_etc", Detalles_etc)

    def addDetalles_etc(det_etc_nombre, det_etc_etc_id, det_etc_per_id):
        orm_insert("t_detalles_etc", {
            "DET_ETC_UUID": str(uuid_lib.uuid4()),
            "DET_ETC_NOMBRE": det_etc_nombre,
            "DET_ETC_ETC_ID": det_etc_etc_id,
            "DET_ETC_PER_ID": det_etc_per_id,
        })
        return "Detalle agregado correctamente"

    def deleteDetalles_etc(id):
        orm_delete("t_detalles_etc", id)

        return "Detalle eliminado correctamente"  

    def updateDetalles_etc(id, det_etc_nombre, det_etc_etc_id, det_etc_per_id):
        orm_update("t_detalles_etc", id, {
            "DET_ETC_NOMBRE": det_etc_nombre,
            "DET_ETC_ETC_ID": det_etc_etc_id,
            "DET_ETC_PER_ID": det_etc_per_id,
        })

        return "Detalle actualizado correctamente"