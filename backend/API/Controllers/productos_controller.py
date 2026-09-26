from flask import jsonify, request
from Services.productos_services import (
    servListProductos,
    servGetProducto,
    addProductos,
    deleteProductos,
    updateProductos,
)

def cntListProductos():
    data = servListProductos()
    return jsonify(data), 200

def cntGetProducto(prod_id):
    data = servGetProducto(prod_id)
    if data is None:
        return jsonify({"message": "Producto no encontrado."}), 404
    return jsonify(data), 200

def cntAddProductos():
    payload = request.get_json(silent=True) or {}
    try:
        data = addProductos(payload)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    return jsonify(data), 201

def cntDelProductos(prod_id):
    deleted = deleteProductos(prod_id)
    if not deleted:
        return jsonify({"message": "Producto no encontrado."}), 404
    return jsonify({"message": "Producto eliminado correctamente."}), 200

def cntModProductos(prod_id):
    payload = request.get_json(silent=True) or {}
    try:
        updated = updateProductos(prod_id, payload)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    if not updated:
        return jsonify({"message": "Producto no encontrado."}), 404
    return jsonify({"message": "Producto actualizado correctamente."}), 200
