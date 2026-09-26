from sqlalchemy import select

from Models.etc import ETC
from orm import orm_model, orm_session
import uuid as uuid_lib

class etc_services:
    def servListETC():
        model = orm_model("t_estado_tipos_categorias")
        with orm_session() as session:
            rows = session.scalars(select(model).order_by(model.ETC_ID)).all()
            return [ETC(row.ETC_ID, row.ETC_UUID, row.ETC_NOMBRE).to_dic() for row in rows]

    def addETC(etc_nombre):
        model = orm_model("t_estado_tipos_categorias")
        with orm_session() as session:
            session.add(model(ETC_UUID=str(uuid_lib.uuid4()), ETC_NOMBRE=etc_nombre))
        return "ETC agregado correctamente"

    def deleteETC(id):
        model = orm_model("t_estado_tipos_categorias")
        with orm_session() as session:
            row = session.get(model, int(id))
            if row is not None:
                session.delete(row)

        return "ETC eliminado correctamente"  

    def updateETC(id, etc_nombre):
        model = orm_model("t_estado_tipos_categorias")
        with orm_session() as session:
            row = session.get(model, int(id))
            if row is not None:
                row.ETC_NOMBRE = etc_nombre

        return "ETC actualizado correctamente"