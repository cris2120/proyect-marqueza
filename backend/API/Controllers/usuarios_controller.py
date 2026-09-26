from flask import jsonify, request
from Services.usuarios_services import servListUsuarios, addUsuarios, deleteUsuarios, updateUsuarios
from Controllers.json_payload import required_json

def cntListUsuarios():
    data = servListUsuarios()
    return jsonify(data), 200

def cntAddUsuarios():
    payload, error = required_json("nombre", "correo", "contrasena", "estado", "det_etc_id")
    if error:
        return error
    result = addUsuarios(payload["nombre"], payload["correo"], payload["contrasena"], payload["estado"], payload["det_etc_id"])
    return jsonify(result), 201

def cntDelUsuarios(id):
    return jsonify(deleteUsuarios(id)), 200

def cntModUsuarios(id):
    payload, error = required_json("nombre", "correo", "contrasena", "estado", "det_etc_id")
    if error:
        return error
    result = updateUsuarios(id, payload["nombre"], payload["correo"], payload["contrasena"], payload["estado"], payload["det_etc_id"])
    return jsonify(result), 200

