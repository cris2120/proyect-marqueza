from flask import Blueprint, current_app, jsonify, request

from Services.chat_services import ChatServiceError, reply


chat_bp = Blueprint("chat_bp", __name__)


@chat_bp.route("/", methods=["POST"])
def chat():
    if request.content_length is not None and request.content_length > 32000:
        return jsonify({"message": "La solicitud es demasiado grande."}), 413

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "El cuerpo debe ser un objeto JSON."}), 400

    try:
        return jsonify({"reply": reply(data.get("messages"))}), 200
    except ChatServiceError as error:
        if error.status_code >= 500:
            current_app.logger.warning("No se pudo responder al chat: %s", error)
        return jsonify({"message": str(error)}), error.status_code
