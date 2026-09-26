from flask import Blueprint, jsonify
from Controllers.proveedor_controller import cntListProveedor, cntAddProveedor, cntDelProveedor, cntModProveedor

proveedor_bp = Blueprint('proveedor_bp', __name__)

@proveedor_bp.route('/', methods=['GET'])
def listProveedor():
    x = cntListProveedor()
    return x

@proveedor_bp.route('/', methods=['POST'])
def createProveedor():
    return cntAddProveedor()

@proveedor_bp.route('/<int:id>', methods=['PUT'])
def updateProveedor(id):
    return cntModProveedor(id)

@proveedor_bp.route('/<int:id>', methods=['DELETE'])
def deleteProveedor(id):
    return cntDelProveedor(id)