from flask import Blueprint
from Controllers.productos_controller import (
    cntListProductos,
    cntGetProducto,
    cntAddProductos,
    cntDelProductos,
    cntModProductos,
)

productos_bp = Blueprint('productos_bp', __name__)

@productos_bp.route('/', methods=['GET'])
def listProductos():
    return cntListProductos()

@productos_bp.route('/<int:prod_id>', methods=['GET'])
def getProducto(prod_id):
    return cntGetProducto(prod_id)

@productos_bp.route('/', methods=['POST'])
def createProductos():
    return cntAddProductos()

@productos_bp.route('/<int:prod_id>', methods=['PUT'])
def updateProductos(prod_id):
    return cntModProductos(prod_id)

@productos_bp.route('/<int:prod_id>', methods=['DELETE'])
def deleteProductos(prod_id):
    return cntDelProductos(prod_id)
