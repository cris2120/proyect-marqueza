from Models.productos import Productos
from orm import orm_delete, orm_insert, orm_list, orm_update
import uuid as uuid_lib

def servListProductos():
    return orm_list("t_productos", Productos)

def addProductos(codigo, nombre, cantidad, precio, estado, usuario_id, det_etc_id):
    orm_insert("t_productos", {
        "PROD_UUID": str(uuid_lib.uuid4()),
        "PROD_CODIGO": codigo,
        "PROD_NOMBRE": nombre,
        "PROD_CANTIDAD": cantidad,
        "PROD_PRECIO": precio,
        "PROD_ESTADO": estado,
        "PROD_USUA_ID": usuario_id,
        "PROD_DET_ETC_ID": det_etc_id,
    })
    return "Producto agregado correctamente"

def deleteProductos(id):
    orm_delete("t_productos", id)
    return "Producto eliminado correctamente"  

def updateProductos(id, codigo, nombre, cantidad, precio, estado, usuario_id, det_etc_id):
    orm_update("t_productos", id, {
        "PROD_CODIGO": codigo,
        "PROD_NOMBRE": nombre,
        "PROD_CANTIDAD": cantidad,
        "PROD_PRECIO": precio,
        "PROD_ESTADO": estado,
        "PROD_USUA_ID": usuario_id,
        "PROD_DET_ETC_ID": det_etc_id,
    })
    return "Producto actualizado correctamente"