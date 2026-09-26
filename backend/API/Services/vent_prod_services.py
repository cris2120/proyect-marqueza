from Models.vent_prod import Vent_prod
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

def servListVentProd():
    return orm_list("t_vent_prod", Vent_prod)

def addVentProd(cantidad, venta_id, producto_id):
    orm_insert("t_vent_prod", {
        "VENPRO_UUID": str(uuid_lib.uuid4()),
        "VENPRO_CANTIDAD": cantidad,
        "VENPRO_VENT_ID": venta_id,
        "VENPRO_PROD_ID": producto_id,
    })
    return "Venta_producto agregado correctamente"

def deleteVentProd(id):
    orm_delete("t_vent_prod", id)
    return "Venta_producto eliminado correctamente"

def updateVentProd(id, cantidad, venta_id, producto_id):
    orm_update("t_vent_prod", id, {
        "VENPRO_CANTIDAD": cantidad,
        "VENPRO_VENT_ID": venta_id,
        "VENPRO_PROD_ID": producto_id,
    })
    return "Venta_producto actualizado correctamente"