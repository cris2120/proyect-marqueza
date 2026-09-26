from Models.insumos import Insumos
from orm import orm_delete, orm_insert, orm_model, orm_session, orm_update
from sqlalchemy import select
import uuid as uuid_lib

class insumos_services:
    def servListInsumos():
        model = orm_model("t_insumos")
        with orm_session() as session:
            rows = session.scalars(select(model).order_by(model.INS_ID)).all()
            result = []
            for row in rows:
                item = Insumos(row.INS_ID, row.INS_UUID, row.INS_CODIGO, row.INS_NOMBRE, row.INS_CANTIDAD, row.INS_PRECIO, row.INS_ESTADO, row.INS_USUA_ID, row.INS_PROV_ID, row.INS_DET_ETC_ID).to_dic()
                item["unidad"] = getattr(row, "INS_UNIDAD", "unidad")
                result.append(item)
            return result

    def addInsumos(codigo, nombre, cantidad, precio, estado, usuario_id, proveedor_id, etc_id, unidad):
        return orm_insert("t_insumos", {
            "INS_UUID": str(uuid_lib.uuid4()),
            "INS_CODIGO": codigo,
            "INS_NOMBRE": nombre,
            "INS_CANTIDAD": cantidad,
            "INS_PRECIO": precio,
            "INS_ESTADO": estado,
            "INS_USUA_ID": usuario_id,
            "INS_PROV_ID": proveedor_id,
            "INS_DET_ETC_ID": etc_id,
            "INS_UNIDAD": unidad,
        })

    def deleteInsumos(id):
        orm_delete("t_insumos", id)
        return "Insumo eliminado correctamente"
        
    def updateInsumos(id, codigo, nombre, cantidad, precio, estado, usuario_id, proveedor_id, etc_id, unidad):
        orm_update("t_insumos", id, {
            "INS_CODIGO": codigo,
            "INS_NOMBRE": nombre,
            "INS_CANTIDAD": cantidad,
            "INS_PRECIO": precio,
            "INS_ESTADO": estado,
            "INS_USUA_ID": usuario_id,
            "INS_PROV_ID": proveedor_id,
            "INS_DET_ETC_ID": etc_id,
            "INS_UNIDAD": unidad,
        })

        return "Insumo actualizado correctamente"
        