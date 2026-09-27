from Services.helpers import (clean, execute, new_uuid, query,
                              resolve_categoria, serialize_rows)


def servListProductos():
    rows = query(
        """SELECT id, uuid, codigo, nombre, cantidad, precio, valor_inventario,
                  estado, categoria, nivel_stock, clase_badge
           FROM v_catalogo_productos
           ORDER BY nombre"""
    )
    return serialize_rows(rows)


def _payload(data):
    codigo = clean(data.get("codigo"))
    nombre = clean(data.get("nombre"))
    try:
        cantidad = int(float(data.get("cantidad") or 0))
    except (TypeError, ValueError):
        cantidad = 0
    try:
        precio = float(data.get("precio") or 0)
    except (TypeError, ValueError):
        precio = 0.0
    estado = clean(data.get("estado"), "Activo")
    if estado not in ("Activo", "Inactivo"):
        estado = "Activo"
    categoria = resolve_categoria(clean(data.get("categoria"), "General"), "CATEGORIAS_PRODUCTOS")
    return codigo, nombre, cantidad, precio, estado, categoria


def addProductos(data):
    codigo, nombre, cantidad, precio, estado, categoria = _payload(data)
    if not codigo or not nombre:
        return {"mensaje": "El codigo y el nombre son obligatorios"}, 400

    existente = query("SELECT PROD_ID FROM t_productos WHERE PROD_CODIGO = %s", (codigo,))
    if existente:
        return {"mensaje": "Ya existe un producto con ese codigo"}, 409

    prod_id = execute(
        """INSERT INTO t_productos
           (PROD_UUID, PROD_CODIGO, PROD_NOMBRE, PROD_CANTIDAD, PROD_PRECIO,
            PROD_ESTADO, PROD_USUA_ID, PROD_DET_ETC_ID)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (new_uuid(), codigo, nombre, cantidad, precio, estado,
         data.get("usua_id") or None, categoria),
    )
    return {"mensaje": "Producto agregado correctamente", "id": prod_id}, 201


def updateProductos(id, data):
    if not query("SELECT PROD_ID FROM t_productos WHERE PROD_ID = %s", (id,)):
        return {"mensaje": "Producto no encontrado"}, 404

    codigo, nombre, cantidad, precio, estado, categoria = _payload(data)
    if not codigo or not nombre:
        return {"mensaje": "El codigo y el nombre son obligatorios"}, 400

    duplicado = query(
        "SELECT PROD_ID FROM t_productos WHERE PROD_CODIGO = %s AND PROD_ID <> %s",
        (codigo, id),
    )
    if duplicado:
        return {"mensaje": "Ya existe otro producto con ese codigo"}, 409

    execute(
        """UPDATE t_productos SET PROD_CODIGO = %s, PROD_NOMBRE = %s, PROD_CANTIDAD = %s,
           PROD_PRECIO = %s, PROD_ESTADO = %s, PROD_DET_ETC_ID = %s
           WHERE PROD_ID = %s""",
        (codigo, nombre, cantidad, precio, estado, categoria, id),
    )
    return {"mensaje": "Producto actualizado correctamente", "id": id}, 200


def deleteProductos(id):
    if not query("SELECT PROD_ID FROM t_productos WHERE PROD_ID = %s", (id,)):
        return {"mensaje": "Producto no encontrado"}, 404
    try:
        execute("DELETE FROM t_productos WHERE PROD_ID = %s", (id,))
    except Exception:
        return {"mensaje": "No se puede eliminar: el producto tiene ventas o cotizaciones asociadas"}, 409
    return {"mensaje": "Producto eliminado correctamente"}, 200
