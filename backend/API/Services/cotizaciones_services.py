from Models.cotizaciones import Cotizaciones
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

class cotizaciones_services:
    def servListCotizaciones():
        return orm_list("t_cotizaciones", Cotizaciones)

    def addCotizaciones(pro_codigo, pro_nombre, pro_cantidad, pro_precio, total_pagar, usuario_id, cliente_id):
        orm_insert("t_cotizaciones", {
            "COT_UUID": str(uuid_lib.uuid4()),
            "COT_PRO_CODIGO": pro_codigo,
            "COT_PRO_NOMBRE": pro_nombre,
            "COT_PRO_CANTIDAD": pro_cantidad,
            "COT_PRO_PRECIO": pro_precio,
            "COT_TOTAL_PAGAR": total_pagar,
            "COT_USUA_ID": usuario_id,
            "COT_CLI_ID": cliente_id,
        })
        return "Cotización agregada correctamente"

    def deleteCotizaciones(id):
        orm_delete("t_cotizaciones", id)

        return "Cotización eliminada correctamente"

    def updateCotizaciones(id, pro_codigo, pro_nombre, pro_cantidad, pro_precio, total_pagar, usuario_id, cliente_id):
        orm_update("t_cotizaciones", id, {
            "COT_PRO_CODIGO": pro_codigo,
            "COT_PRO_NOMBRE": pro_nombre,
            "COT_PRO_CANTIDAD": pro_cantidad,
            "COT_PRO_PRECIO": pro_precio,
            "COT_TOTAL_PAGAR": total_pagar,
            "COT_USUA_ID": usuario_id,
            "COT_CLI_ID": cliente_id,
        })

        return "Cotización actualizada correctamente"