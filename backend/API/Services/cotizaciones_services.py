import json
from datetime import date

from Models.cotizaciones import Cotizaciones
from orm import orm_delete, orm_insert, orm_model, orm_session, orm_update
from sqlalchemy import select
import uuid as uuid_lib

class cotizaciones_services:
    def servListCotizaciones():
        model = orm_model("t_cotizaciones")
        with orm_session() as session:
            rows = session.scalars(select(model).order_by(model.COT_ID.desc())).all()
            result = []
            for row in rows:
                quote = Cotizaciones(row.COT_ID, row.COT_UUID, row.COT_PRO_CODIGO, row.COT_PRO_NOMBRE, row.COT_PRO_CANTIDAD, row.COT_PRO_PRECIO, row.COT_TOTAL_PAGAR, row.COT_USUA_ID, row.COT_CLI_ID).to_dic()
                quote["total"] = float(row.COT_TOTAL_PAGAR)
                raw_items = getattr(row, "COT_DETALLE_JSON", None)
                quote["productos"] = json.loads(raw_items) if raw_items else [{
                    "codigo": row.COT_PRO_CODIGO,
                    "nombre": row.COT_PRO_NOMBRE,
                    "cantidad": row.COT_PRO_CANTIDAD,
                    "precio": row.COT_PRO_PRECIO,
                }]
                quote["fecha"] = getattr(row, "COT_FECHA", None).isoformat() if getattr(row, "COT_FECHA", None) else ""
                quote["estado"] = getattr(row, "COT_ESTADO", "Pendiente")
                quote["notas"] = getattr(row, "COT_NOTAS", None) or ""
                result.append(quote)
            return result

    def addCotizaciones(pro_codigo, pro_nombre, pro_cantidad, pro_precio, total_pagar, usuario_id, cliente_id, fecha, estado, notas, productos):
        return orm_insert("t_cotizaciones", {
            "COT_UUID": str(uuid_lib.uuid4()),
            "COT_PRO_CODIGO": pro_codigo,
            "COT_PRO_NOMBRE": pro_nombre,
            "COT_PRO_CANTIDAD": pro_cantidad,
            "COT_PRO_PRECIO": pro_precio,
            "COT_TOTAL_PAGAR": total_pagar,
            "COT_USUA_ID": usuario_id,
            "COT_CLI_ID": cliente_id,
            "COT_FECHA": date.fromisoformat(fecha) if isinstance(fecha, str) else fecha,
            "COT_ESTADO": estado,
            "COT_NOTAS": notas,
            "COT_DETALLE_JSON": json.dumps(productos, ensure_ascii=False),
        })

    def deleteCotizaciones(id):
        orm_delete("t_cotizaciones", id)

        return "Cotización eliminada correctamente"

    def updateCotizaciones(id, pro_codigo, pro_nombre, pro_cantidad, pro_precio, total_pagar, usuario_id, cliente_id, fecha, estado, notas, productos):
        if isinstance(fecha, str):
            fecha = date.fromisoformat(fecha)
        orm_update("t_cotizaciones", id, {
            "COT_PRO_CODIGO": pro_codigo,
            "COT_PRO_NOMBRE": pro_nombre,
            "COT_PRO_CANTIDAD": pro_cantidad,
            "COT_PRO_PRECIO": pro_precio,
            "COT_TOTAL_PAGAR": total_pagar,
            "COT_USUA_ID": usuario_id,
            "COT_CLI_ID": cliente_id,
            "COT_FECHA": fecha,
            "COT_ESTADO": estado,
            "COT_NOTAS": notas,
            "COT_DETALLE_JSON": json.dumps(productos, ensure_ascii=False),
        })

        return "Cotización actualizada correctamente"