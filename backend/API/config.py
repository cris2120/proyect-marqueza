import os
from dotenv import load_dotenv

load_dotenv()


def _setting(*names):
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return None


def _mysql_port():
    value = _setting("MYSQL_PORT", "mysql_port")
    try:
        port = int(value or 3306)
    except ValueError as error:
        raise RuntimeError("MYSQL_PORT debe ser un numero entre 1 y 65535.") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("MYSQL_PORT debe ser un numero entre 1 y 65535.")
    return port


class Config:
    MYSQL_HOST = _setting("MYSQL_HOST", "mysql_host")
    MYSQL_PORT = _mysql_port()
    MYSQL_USER = _setting("MYSQL_USER", "mysql_user")
    MYSQL_PASSWORD = _setting("MYSQL_PASSWORD", "mysql_password")
    MYSQL_DB = _setting("MYSQL_DB", "MYSQL_DATABASE", "mysql_db")


def validate_mysql_config(config):
    missing = [
        name for name in ("MYSQL_HOST", "MYSQL_USER", "MYSQL_DB")
        if not config.get(name) or not str(config[name]).strip()
    ]
    if config.get("MYSQL_PASSWORD") is None:
        missing.append("MYSQL_PASSWORD")
    if missing:
        raise RuntimeError("Faltan variables de base de datos: " + ", ".join(missing))
