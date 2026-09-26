from flask import Blueprint, jsonify
from Controllers.ventas_controller import cntListVentas, cntAddVentas, cntDelVentas, cntModVentas

ventas_bp = Blueprint('ventas_bp', __name__)

@ventas_bp.route('/', methods=['GET'])
def listVentas():
    x = cntListVentas()
    return x

@ventas_bp.route('/', methods=['POST'])
def createVentas():
    return cntAddVentas()

@ventas_bp.route('/<int:id>', methods=['PUT'])
def updateVentas(id):
    return cntModVentas(id)

@ventas_bp.route('/<int:id>', methods=['DELETE'])
def deleteVentas(id):
    return cntDelVentas(id)