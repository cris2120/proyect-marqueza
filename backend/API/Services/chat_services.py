import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


logger = logging.getLogger(__name__)
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
MAX_MESSAGES = 12
MAX_MESSAGE_LENGTH = 2000

SYSTEM_PROMPT = (
    "Eres el asistente de MARQUEZA, una aplicacion de gestion para una empresa de "
    "confecciones. Ayudas en espanol con el uso de sus modulos: inicio, insumos, "
    "productos, ventas, cotizaciones, clientes, proveedores, usuarios y registro de "
    "actividad. El frontend usa HTML, CSS y JavaScript; el backend usa Flask y MySQL. "
    "Algunas pantallas aun conservan datos en el navegador. No tienes acceso a la "
    "base de datos ni a informacion en tiempo real: no inventes registros, cantidades, "
    "ventas ni datos personales. No solicites contrasenas, claves API ni informacion "
    "sensible. Si preguntan por informacion en vivo, explica esta limitacion y dirige "
    "al usuario al modulo correspondiente. Da instrucciones claras y concisas."
)


class ChatServiceError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def _validate_messages(messages):
    if not isinstance(messages, list) or not messages or len(messages) > MAX_MESSAGES:
        raise ChatServiceError("La conversacion no tiene un formato valido.", 400)

    validated = []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
            raise ChatServiceError("La conversacion contiene un mensaje no valido.", 400)
        content = message.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_MESSAGE_LENGTH:
            raise ChatServiceError("Cada mensaje debe tener texto de hasta 2000 caracteres.", 400)
        validated.append({"role": message["role"], "content": content.strip()})

    if validated[-1]["role"] != "user":
        raise ChatServiceError("El ultimo mensaje debe ser una pregunta del usuario.", 400)
    return validated


def reply(messages):
    conversation = _validate_messages(messages)
    api_key = (current_app.config.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ChatServiceError("El chatbot no esta configurado: falta OPENAI_API_KEY.", 503)

    payload = json.dumps({
        "model": current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *conversation],
        "max_tokens": 500,
        "temperature": 0.4,
    }).encode("utf-8")
    request = Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=current_app.config.get("OPENAI_TIMEOUT", 30)) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        if error.code == 429:
            raise ChatServiceError("OpenAI alcanzo su limite de uso. Intenta mas tarde.", 503) from error
        logger.warning("OpenAI rechazo la solicitud del chatbot (HTTP %s).", error.code)
        raise ChatServiceError("El servicio de IA no pudo procesar la solicitud.", 502) from error
    except (URLError, TimeoutError, OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        logger.warning("No se pudo completar la solicitud a OpenAI: %s", error)
        raise ChatServiceError("No se pudo conectar con el servicio de IA.", 502) from error

    try:
        answer = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        logger.error("OpenAI devolvio una respuesta con formato inesperado.")
        raise ChatServiceError("El servicio de IA devolvio una respuesta no valida.", 502) from error

    if not isinstance(answer, str) or not answer.strip():
        logger.error("OpenAI devolvio una respuesta vacia.")
        raise ChatServiceError("El servicio de IA devolvio una respuesta vacia.", 502)
    return answer.strip()
