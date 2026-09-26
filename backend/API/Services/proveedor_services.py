from Models.proveedor import Proveedor
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

def servListProveedor():
    return orm_list("t_proveedores", Proveedor)

def addProveedor(persona_id):
    return orm_insert("t_proveedores", {
        "PROV_UUID": str(uuid_lib.uuid4()),
        "PROV_PER_ID": persona_id,
    })
    return "Proveedor agregado correctamente"

def deleteProveedor(id):
    orm_delete("t_proveedores", id)
    return "Proveedor eliminado correctamente"

def updateProveedor(id, persona_id):
    orm_update("t_proveedores", id, {"PROV_PER_ID": persona_id})
    return "Proveedor actualizado correctamente"