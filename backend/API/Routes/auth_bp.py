import os
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from orm import orm_model, orm_session


auth_bp = Blueprint("auth_bp", __name__)
_reset_tokens = {}


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "El cuerpo debe ser un objeto JSON."}), 400

    username = str(payload.get("usuario", "")).strip()
    password = str(payload.get("contrasena", ""))
    if not username or not password:
        return jsonify({"error": "Ingresa usuario y contraseña."}), 400

    model = orm_model("t_usuarios")
    with orm_session() as session:
        user = session.scalar(
            select(model).where(func.lower(model.USUA_NOMBRE) == username.lower())
        )
        stored_password = str(getattr(user, "USUA_CONTRASEÑA", "")) if user else ""
        if not user or not secrets.compare_digest(stored_password, password):
            return jsonify({"error": "El usuario o la contraseña son incorrectos."}), 401

        return jsonify({
            "usuario": {
                "id": user.USUA_ID,
                "uuid": user.USUA_UUID,
                "nombre": user.USUA_NOMBRE,
                "correo": user.USUA_CORREO,
                "estado": user.USUA_ESTADO,
                "det_etc_id": user.USUA_DET_ETC_ID,
            }
        }), 200


def send_reset_email(recipient, reset_url):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", username)
    if not all((host, username, password, sender)):
        raise RuntimeError("SMTP no está configurado en el servidor.")

    message = EmailMessage()
    message["Subject"] = "Restablece tu contraseña | MARQUEZA"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "Hola,\n\n"
        "Recibimos una solicitud para cambiar tu contraseña de MARQUEZA. "
        f"Abre este enlace para continuar: {reset_url}\n\n"
        "Este enlace vence en 30 minutos. Si no realizaste esta solicitud, ignora este mensaje.\n\n"
        "MARQUEZA"
    )

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


@auth_bp.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@auth_bp.route("/forgot-password", methods=["POST", "OPTIONS"])
def forgot_password():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    email = str(data.get("correo", "")).strip().lower()
    if not email or "@" not in email:
        return jsonify({"message": "Ingresa un correo electrónico válido."}), 400

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {"correo": email, "expires": datetime.now(timezone.utc) + timedelta(minutes=30)}
    frontend_url = os.getenv("FRONTEND_RESET_URL", "http://localhost:5500/frontend/olvido_contrasena/restablecer.html")
    try:
        send_reset_email(email, f"{frontend_url}?token={token}")
    except RuntimeError as error:
        return jsonify({"message": str(error)}), 503
    except OSError:
        return jsonify({"message": "No fue posible conectar con el servidor de correo."}), 502

    return jsonify({"message": "Correo enviado correctamente."}), 200
