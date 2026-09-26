from flask import jsonify, request
from Services.ventas_services import servListVentas, addVentas, deleteVentas, updateVentas
from datetime import date
from Controllers.json_payload import required_json

def cntListVentas():
    data = servListVentas()
    return jsonify(data), 200

def cntAddVentas():
    payload, error = required_json("fecha", "usua_id", "cli_id")
    if error:
        return error
    try:
        fecha = date.fromisoformat(payload["fecha"])
    except (TypeError, ValueError):
        return jsonify({"error": "fecha debe usar el formato AAAA-MM-DD."}), 400
    record_id = addVentas(fecha, payload["usua_id"], payload["cli_id"])
    return jsonify({"id": record_id}), 201

def cntDelVentas(id):
    return jsonify(deleteVentas(id)), 200

def cntModVentas(id):
    payload, error = required_json("fecha", "usua_id", "cli_id")
    if error:
        return error
    try:
        fecha = date.fromisoformat(payload["fecha"])
    except (TypeError, ValueError):
        return jsonify({"error": "fecha debe usar el formato AAAA-MM-DD."}), 400
    return jsonify(updateVentas(id, fecha, payload["usua_id"], payload["cli_id"])), 200

