import uuid
from flask import current_app
from Models.productos import Productos

REQUIRED_FIELDS = ("codigo", "nombre", "cantidad", "precio")


def _validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("El cuerpo debe ser un JSON objeto.")
    missing = [f for f in REQUIRED_FIELDS if payload.get(f) in (None, "")]
    if missing:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(missing)}.")
    try:
        cantidad = int(payload["cantidad"])
        precio = float(payload["precio"])
    except (TypeError, ValueError):
        raise ValueError("cantidad debe ser entero y precio debe ser número.")
    if cantidad < 0 or precio < 0:
        raise ValueError("cantidad y precio no pueden ser negativos.")
    return {
        "uuid": payload.get("uuid") or str(uuid.uuid4()),
        "codigo": str(payload["codigo"]).strip(),
        "nombre": str(payload["nombre"]).strip(),
        "cantidad": cantidad,
        "precio": precio,
        "estado": payload.get("estado", "activo"),
        "usua_id": payload.get("usua_id"),
        "det_etc_id": payload.get("det_etc_id"),
    }


def servListProductos():
    sql = "SELECT * FROM T_PRODUCTOS"

    c = current_app.mysql.connection.cursor()
    try:
        c.execute(sql)
        data = c.fetchall()
    finally:
        c.close()

    return [Productos(u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8]).to_dic() for u in data]


def servGetProducto(prod_id):
    sql = "SELECT * FROM T_PRODUCTOS WHERE PROD_ID = %s"

    c = current_app.mysql.connection.cursor()
    try:
        c.execute(sql, (prod_id,))
        u = c.fetchone()
    finally:
        c.close()

    if u is None:
        return None
    return Productos(u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8]).to_dic()


def addProductos(payload):
    clean = _validate_payload(payload)
    sql = (
        "INSERT INTO T_PRODUCTOS "
        "(PROD_UUID, PROD_CODIGO, PROD_NOMBRE, PROD_CANTIDAD, PROD_PRECIO, "
        "PROD_ESTADO, PROD_USUA_ID, PROD_DET_ETC_ID) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    c = current_app.mysql.connection.cursor()
    try:
        c.execute(sql, (
            clean["uuid"], clean["codigo"], clean["nombre"], clean["cantidad"],
            clean["precio"], clean["estado"], clean["usua_id"], clean["det_etc_id"],
        ))
        current_app.mysql.connection.commit()
        new_id = c.lastrowid
    finally:
        c.close()

    return {"id": new_id, "uuid": clean["uuid"], **{k: clean[k] for k in ("codigo", "nombre", "cantidad", "precio", "estado")}}


def deleteProductos(prod_id):
    sql = "DELETE FROM T_PRODUCTOS WHERE PROD_ID = %s"

    c = current_app.mysql.connection.cursor()
    try:
        c.execute(sql, (prod_id,))
        current_app.mysql.connection.commit()
        return c.rowcount > 0
    finally:
        c.close()


def updateProductos(prod_id, payload):
    clean = _validate_payload(payload)
    sql = (
        "UPDATE T_PRODUCTOS SET PROD_UUID = %s, PROD_CODIGO = %s, PROD_NOMBRE = %s, "
        "PROD_CANTIDAD = %s, PROD_PRECIO = %s, PROD_ESTADO = %s, "
        "PROD_USUA_ID = %s, PROD_DET_ETC_ID = %s WHERE PROD_ID = %s"
    )

    c = current_app.mysql.connection.cursor()
    try:
        c.execute(sql, (
            clean["uuid"], clean["codigo"], clean["nombre"], clean["cantidad"],
            clean["precio"], clean["estado"], clean["usua_id"], clean["det_etc_id"],
            prod_id,
        ))
        current_app.mysql.connection.commit()
        return c.rowcount > 0
    finally:
        c.close()
