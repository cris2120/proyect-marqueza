from flask import Blueprint, jsonify
from Controllers.usuarios_controller import cntListUsuarios, cntAddUsuarios, cntDelUsuarios, cntModUsuarios

usuarios_bp = Blueprint('usuarios_bp', __name__)

@usuarios_bp.route('/', methods=['GET'])
def listUsuarios():
    x = cntListUsuarios()
    return x

@usuarios_bp.route('/', methods=['POST'])
def createUsuarios():
    return cntAddUsuarios()

@usuarios_bp.route('/<int:id>', methods=['PUT'])
def updateUsuarios(id):
    return cntModUsuarios(id)

@usuarios_bp.route('/<int:id>', methods=['DELETE'])
def deleteUsuarios(id):
    return cntDelUsuarios(id)