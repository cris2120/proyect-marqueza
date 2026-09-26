from datetime import date

from Models.ventas import Ventas
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

def servListVentas():
    return orm_list("t_ventas", Ventas)

def addVentas(fecha, usuario_id, cliente_id):
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)
    return orm_insert("t_ventas", {
        "VENT_UUID": str(uuid_lib.uuid4()),
        "VENT_FECHA": fecha,
        "VENT_USUA_ID": usuario_id,
        "VENT_CLI_ID": cliente_id,
    })

def deleteVentas(id):
    orm_delete("t_ventas", id)
    return "Venta eliminado correctamente"

def updateVentas(id, fecha, usuario_id, cliente_id):
    if isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)
    orm_update("t_ventas", id, {
        "VENT_FECHA": fecha,
        "VENT_USUA_ID": usuario_id,
        "VENT_CLI_ID": cliente_id,
    })
    return "Venta actualizado correctamente"