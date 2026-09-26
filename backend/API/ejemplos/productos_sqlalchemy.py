"""Muestra: como se veria el modelo de productos con SQLAlchemy.

NO es parte de la API todavia, es solo referencia para comparar con
Models/productos.py (clase suelta + SQL a mano en Services/).

Para probarlo:
    uv pip install --python .venv/bin/python sqlalchemy
    .venv/bin/python ejemplos/productos_sqlalchemy.py

Lo importante:
- __tablename__ = "T_PRODUCTOS": apunta a la MISMA tabla de schema.sql,
  asi que migrar no exige cambiar la base de datos.
- Las columnas describen tipo/nulo/primary_key una sola vez; con eso
  SQLAlchemy genera el INSERT/UPDATE/SELECT y Alembic las migraciones.
- to_dict() reemplaza al viejo to_dic() para seguir devolviendo el mismo JSON.
"""

from sqlalchemy import Integer, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Productos(Base):
    __tablename__ = "T_PRODUCTOS"

    id: Mapped[int] = mapped_column("PROD_ID", Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str | None] = mapped_column("PROD_UUID", String(64))
    codigo: Mapped[str] = mapped_column("PROD_CODIGO", String(50), nullable=False)
    nombre: Mapped[str] = mapped_column("PROD_NOMBRE", String(100), nullable=False)
    cantidad: Mapped[int] = mapped_column("PROD_CANTIDAD", Integer, nullable=False, default=0)
    precio: Mapped[float] = mapped_column("PROD_PRECIO", Numeric(12, 2), nullable=False, default=0)
    estado: Mapped[str | None] = mapped_column("PROD_ESTADO", String(20), default="activo")
    usua_id: Mapped[int | None] = mapped_column("PROD_USUA_ID", Integer)
    det_etc_id: Mapped[int | None] = mapped_column("PROD_DET_ETC_ID", Integer)

    def to_dict(self):  # mismo JSON que el viejo to_dic()
        return {
            "id": self.id,
            "uuid": self.uuid,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "precio": float(self.precio) if self.precio is not None else None,
            "estado": self.estado,
            "usua_id": self.usua_id,
            "det_etc_id": self.det_etc_id,
        }


if __name__ == "__main__":
    # Demo sin MySQL: SQLite en memoria, misma tabla/columnas.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as s:
        s.add(Productos(codigo="P001", nombre="Camisa", cantidad=5, precio=29.99))
        s.commit()
        print(s.query(Productos).all()[0].to_dict())
