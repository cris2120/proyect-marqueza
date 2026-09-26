from flask import jsonify, request
from Services.vent_prod_services import servListVentProd, addVentProd, deleteVentProd, updateVentProd
from Controllers.json_payload import required_json

def cntListVentProd():
    data = servListVentProd()
    return jsonify(data), 200

def cntAddVentProd():
    payload, error = required_json("cantidad", "vent_id", "prod_id", "precio")
    if error:
        return error
    record_id = addVentProd(payload["cantidad"], payload["vent_id"], payload["prod_id"], payload["precio"])
    return jsonify({"id": record_id}), 201

def cntDelVentProd(id):
    return jsonify(deleteVentProd(id)), 200

def cntModVentProd(id):
    payload, error = required_json("cantidad", "vent_id", "prod_id", "precio")
    if error:
        return error
    result = updateVentProd(id, payload["cantidad"], payload["vent_id"], payload["prod_id"], payload["precio"])
    return jsonify(result), 200

