import uuid as uuid_lib

from sqlalchemy import select

from Models.vent_prod import Vent_prod
from orm import orm_delete, orm_insert, orm_model, orm_session, orm_update


def servListVentProd():
    model = orm_model("t_vent_prod")
    with orm_session() as session:
        rows = session.scalars(select(model).order_by(model.VENPRO_ID)).all()
        result = []
        for row in rows:
            item = Vent_prod(
                row.VENPRO_ID,
                row.VENPRO_UUID,
                row.VENPRO_CANTIDAD,
                row.VENPRO_VENT_ID,
                row.VENPRO_PROD_ID,
            ).to_dic()
            item["precio"] = getattr(row, "VENPRO_PRECIO", 0)
            result.append(item)
        return result


def addVentProd(cantidad, venta_id, producto_id, precio):
    return orm_insert("t_vent_prod", {
        "VENPRO_UUID": str(uuid_lib.uuid4()),
        "VENPRO_CANTIDAD": cantidad,
        "VENPRO_VENT_ID": venta_id,
        "VENPRO_PROD_ID": producto_id,
        "VENPRO_PRECIO": precio,
    })


def deleteVentProd(id):
    orm_delete("t_vent_prod", id)
    return "Venta_producto eliminado correctamente"


def updateVentProd(id, cantidad, venta_id, producto_id, precio):
    orm_update("t_vent_prod", id, {
        "VENPRO_CANTIDAD": cantidad,
        "VENPRO_VENT_ID": venta_id,
        "VENPRO_PROD_ID": producto_id,
        "VENPRO_PRECIO": precio,
    })
    return "Venta_producto actualizado correctamente"