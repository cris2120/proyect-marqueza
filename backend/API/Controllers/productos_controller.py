from flask import jsonify, request
from Services.productos_services import servListProductos, addProductos, deleteProductos, updateProductos
from Controllers.json_payload import required_json

def cntListProductos():
    data = servListProductos()
    return jsonify(data), 200

def cntAddProductos():
    payload, error = required_json("codigo", "nombre", "cantidad", "precio", "estado", "usuario_id", "det_etc_id")
    if error:
        return error
    result = addProductos(payload["codigo"], payload["nombre"], payload["cantidad"], payload["precio"], payload["estado"], payload["usuario_id"], payload["det_etc_id"])
    return jsonify(result), 201

def cntDelProductos(id):
    return jsonify(deleteProductos(id)), 200

def cntModProductos(id):
    payload, error = required_json("codigo", "nombre", "cantidad", "precio", "estado", "usuario_id", "det_etc_id")
    if error:
        return error
    result = updateProductos(id, payload["codigo"], payload["nombre"], payload["cantidad"], payload["precio"], payload["estado"], payload["usuario_id"], payload["det_etc_id"])
    return jsonify(result), 200

