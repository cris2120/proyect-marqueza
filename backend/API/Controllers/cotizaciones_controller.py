from flask import jsonify, request
from Services.cotizaciones_services import cotizaciones_services

class cotizaciones_controller:
    def cntListCotizaciones():
        data = cotizaciones_services.servListCotizaciones()
        return jsonify(data), 200

    def cntAddCotizaciones():
        data = request.get_json(silent=True) or {}
        products = data.get("productos") or []
        if not products or not all(key in data for key in ("fecha", "estado", "notas", "usuario_id", "cliente_id", "total_pagar")):
            return jsonify({"error": "Faltan campos requeridos para la cotizacion."}), 400
        first = products[0]
        record_id = cotizaciones_services.addCotizaciones(
            str(first.get("codigo", ""))[:45],
            str(first.get("nombre", ""))[:45],
            sum(int(item.get("cantidad", 0)) for item in products),
            int(first.get("precio", 0)),
            int(data["total_pagar"]),
            int(data["usuario_id"]),
            int(data["cliente_id"]),
            data["fecha"],
            data["estado"],
            data["notas"],
            products,
        )
        return jsonify({"id": record_id}), 201

    def cntDelCotizaciones(id):
        data = cotizaciones_services.deleteCotizaciones(id)
        return jsonify(data), 200

    def cntModCotizaciones(id):
        data = request.get_json(silent=True) or {}
        products = data.get("productos") or []
        if not products or not all(key in data for key in ("fecha", "estado", "notas", "usuario_id", "cliente_id", "total_pagar")):
            return jsonify({"error": "Faltan campos requeridos para la cotizacion."}), 400
        first = products[0]
        result = cotizaciones_services.updateCotizaciones(
            id,
            str(first.get("codigo", ""))[:45],
            str(first.get("nombre", ""))[:45],
            sum(int(item.get("cantidad", 0)) for item in products),
            int(first.get("precio", 0)),
            int(data["total_pagar"]),
            int(data["usuario_id"]),
            int(data["cliente_id"]),
            data["fecha"],
            data["estado"],
            data["notas"],
            products,
        )
        return jsonify(result), 200

