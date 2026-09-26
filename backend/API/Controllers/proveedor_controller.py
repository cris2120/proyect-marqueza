from flask import jsonify, request
from Services.proveedor_services import servListProveedor, addProveedor, deleteProveedor, updateProveedor
from Controllers.json_payload import required_json

def cntListProveedor():
    data = servListProveedor()
    return jsonify(data), 200

def cntAddProveedor():
    payload, error = required_json("persona_id")
    if error:
        return error
    return jsonify(addProveedor(payload["persona_id"])), 201

def cntDelProveedor(id):
    return jsonify(deleteProveedor(id)), 200

def cntModProveedor(id):
    payload, error = required_json("persona_id")
    if error:
        return error
    return jsonify(updateProveedor(id, payload["persona_id"])), 200

