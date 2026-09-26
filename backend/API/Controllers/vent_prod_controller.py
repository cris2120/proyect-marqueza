from flask import jsonify, request
from Services.vent_prod_services import servListVentProd, addVentProd, deleteVentProd, updateVentProd
from Controllers.json_payload import required_json

def cntListVentProd():
    data = servListVentProd()
    return jsonify(data), 200

def cntAddVentProd():
    payload, error = required_json("cantidad", "vent_id", "prod_id")
    if error:
        return error
    result = addVentProd(payload["cantidad"], payload["vent_id"], payload["prod_id"])
    return jsonify(result), 201

def cntDelVentProd(id):
    return jsonify(deleteVentProd(id)), 200

def cntModVentProd(id):
    payload, error = required_json("cantidad", "vent_id", "prod_id")
    if error:
        return error
    result = updateVentProd(id, payload["cantidad"], payload["vent_id"], payload["prod_id"])
    return jsonify(result), 200

