from Models.insumos import Insumos
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class insumos_services:
    def servListInsumos():
        return orm_list("t_insumos", Insumos)

    def addInsumos(codigo, nombre, cantidad, precio, estado, usuario_id, proveedor_id, etc_id):
        orm_insert("t_insumos", {
            "INS_UUID": str(uuid_lib.uuid4()),
            "INS_CODIGO": codigo,
            "INS_NOMBRE": nombre,
            "INS_CANTIDAD": cantidad,
            "INS_PRECIO": precio,
            "INS_ESTADO": estado,
            "INS_USUA_ID": usuario_id,
            "INS_PROV_ID": proveedor_id,
            "INS_DET_ETC_ID": etc_id,
        })
        return "Insumo agregado correctamente"

    def deleteInsumos(id):
        orm_delete("t_insumos", id)
        return "Insumo eliminado correctamente"
        
    def updateInsumos(id, codigo, nombre, cantidad, precio, estado, usuario_id, proveedor_id, etc_id):
        orm_update("t_insumos", id, {
            "INS_CODIGO": codigo,
            "INS_NOMBRE": nombre,
            "INS_CANTIDAD": cantidad,
            "INS_PRECIO": precio,
            "INS_ESTADO": estado,
            "INS_USUA_ID": usuario_id,
            "INS_PROV_ID": proveedor_id,
            "INS_DET_ETC_ID": etc_id,
        })

        return "Insumo actualizado correctamente"
        