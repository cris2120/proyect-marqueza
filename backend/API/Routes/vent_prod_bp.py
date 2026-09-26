from flask import Blueprint, jsonify
from Controllers.vent_prod_controller import cntListVentProd, cntAddVentProd, cntDelVentProd, cntModVentProd

vent_prod_bp = Blueprint('vent_prod_bp', __name__)

@vent_prod_bp.route('/', methods=['GET'])
def listVentProd():
    x = cntListVentProd()
    return x

@vent_prod_bp.route('/', methods=['POST'])
def createVentProd():
    return cntAddVentProd()

@vent_prod_bp.route('/<int:id>', methods=['PUT'])
def updateVentProd(id):
    return cntModVentProd(id)

@vent_prod_bp.route('/<int:id>', methods=['DELETE'])
def deleteVentProd(id):
    return cntDelVentProd(id)