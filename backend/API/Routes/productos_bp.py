from flask import Blueprint, jsonify
from Controllers.productos_controller import cntListProductos, cntAddProductos, cntDelProductos, cntModProductos

productos_bp = Blueprint('productos_bp', __name__)

@productos_bp.route('/', methods=['GET'])
def listProductos():
    x = cntListProductos()
    return x

@productos_bp.route('/', methods=['POST'])
def createProductos():
    return cntAddProductos()

@productos_bp.route('/<int:id>', methods=['PUT'])
def updateProductos(id):
    return cntModProductos(id)

@productos_bp.route('/<int:id>', methods=['DELETE'])
def deleteProductos(id):
    return cntDelProductos(id)