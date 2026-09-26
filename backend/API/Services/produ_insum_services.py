from Models.produ_insum import Produ_insum
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class produ_insum_services:
    def servListProduInsum():
        return orm_list("t_produ_insum", Produ_insum)

    def addProduInsum(cantidad, producto_id, insumo_id):
        orm_insert("t_produ_insum", {
            "PROINSU_UUID": str(uuid_lib.uuid4()),
            "PROINSU_CANTIDAD": cantidad,
            "PROINSU_PROD_ID": producto_id,
            "PROINSU_INS_ID": insumo_id,
        })
        return "Producto_Insumo agregado correctamente"

    def deleteProduInsum(id):
        orm_delete("t_produ_insum", id)

        return "Producto_Insumo eliminado correctamente"  

    def updateProduInsum(id, cantidad, producto_id, insumo_id):
        orm_update("t_produ_insum", id, {
            "PROINSU_CANTIDAD": cantidad,
            "PROINSU_PROD_ID": producto_id,
            "PROINSU_INS_ID": insumo_id,
        })

        return "Producto_Insumo actualizado correctamente"