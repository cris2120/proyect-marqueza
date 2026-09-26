"""Genera backend/API/swagger.json a partir de las rutas y modelos reales.

Uso:
    cd backend/API && python generate_openapi.py      # o: uv run python generate_openapi.py

Fuente de verdad: Routes/__init__.py (prefijos) + cada *_bp.py (verbos) +
Models/*.py (campos de to_dic). Solo `productos` tiene validacion real
(Services/productos_services.py); el resto documenta campos del modelo
sin `required` hasta que cada modulo replique la plantilla.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

ERROR = {
    "type": "object",
    "required": ["message"],
    "properties": {"message": {"type": "string"}},
}
MESSAGE = {
    "type": "object",
    "required": ["message"],
    "properties": {"message": {"type": "string"}},
}


def schema(props, required=()):
    return {
        "type": "object",
        "properties": {"id": {"type": "integer"}, **props},
        "required": ["id", *required],
    }


def input_schema(props, required=()):
    return {
        "type": "object",
        "properties": props,
        "required": list(required),
    }


STR = {"type": "string"}
INT = {"type": "integer"}
NUM = {"type": "number"}

# Recurso: prefijo, tag, descripcion, esquema respuesta, esquema entrada,
# tiene GET detalle, PUT/DELETE con /{id} (False = solo "/" como hoy).
RESOURCES = [
    dict(prefix="/clientes", tag="Clientes", schema=schema({
        "uuid": STR, "per_id": INT}),
        input=input_schema({"uuid": STR, "per_id": INT}),
        detail=False, id_in_path=True),
    dict(prefix="/contactos", tag="Contactos", schema=schema({
        "uuid": STR, "tipo_dato": STR, "contenido": STR, "prov_id": INT}),
        input=input_schema({"uuid": STR, "tipo_dato": STR, "contenido": STR, "prov_id": INT}),
        detail=False, id_in_path=True),
    dict(prefix="/cotizaciones", tag="Cotizaciones", schema=schema({
        "uuid": STR, "pro_codigo": STR, "pro_nombre": STR, "cantidad": INT,
        "precio": NUM, "total_pagar": NUM, "usua_id": INT, "cli_id": INT}),
        input=input_schema({"uuid": STR, "pro_codigo": STR, "pro_nombre": STR,
            "cantidad": INT, "precio": NUM, "total_pagar": NUM,
            "usua_id": INT, "cli_id": INT}),
        detail=False, id_in_path=True),
    dict(prefix="/detalles-etc", tag="DetallesEtc", schema=schema({
        "uuid": STR, "nombre": STR, "etc_id": INT, "per_id": INT}),
        input=input_schema({"uuid": STR, "nombre": STR, "etc_id": INT, "per_id": INT}),
        detail=False, id_in_path=True),
    dict(prefix="/etc", tag="Etc", schema=schema({
        "uuid": STR, "nombre": STR}),
        input=input_schema({"uuid": STR, "nombre": STR}),
        detail=False, id_in_path=True),
    dict(prefix="/insumos", tag="Insumos", schema=schema({
        "uuid": STR, "codigo": STR, "nombre": STR, "cantidad": INT,
        "precio": NUM, "estado": STR, "usua_id": INT, "prov_id": INT,
        "det_etc_id": INT}),
        input=input_schema({"uuid": STR, "codigo": STR, "nombre": STR,
            "cantidad": INT, "precio": NUM, "estado": STR, "usua_id": INT,
            "prov_id": INT, "det_etc_id": INT}),
        detail=False, id_in_path=True),
    dict(prefix="/personas", tag="Personas", schema=schema({
        "uuid": STR, "nombre": STR, "seg_nombre": STR, "pri_apellido": STR,
        "seg_apellido": STR, "correo": STR, "direccion": STR,
        "identificacion": STR, "telefono": STR}),
        input=input_schema({"uuid": STR, "nombre": STR, "seg_nombre": STR,
            "pri_apellido": STR, "seg_apellido": STR, "correo": STR,
            "direccion": STR, "identificacion": STR, "telefono": STR}),
        detail=False, id_in_path=True),
    dict(prefix="/productos-insumos", tag="ProductosInsumos", schema=schema({
        "uuid": STR, "cantidad": INT, "prod_id": INT, "ins_id": INT}),
        input=input_schema({"uuid": STR, "cantidad": INT, "prod_id": INT, "ins_id": INT}),
        detail=False, id_in_path=True),
    # Plantilla de referencia: validacion real, GET detalle, 400/404.
    dict(prefix="/productos", tag="Productos", schema=schema({
        "uuid": STR, "codigo": STR, "nombre": STR, "cantidad": INT,
        "precio": NUM, "estado": STR, "usua_id": INT, "det_etc_id": INT}),
        input=input_schema(
            {"uuid": STR, "codigo": STR, "nombre": STR, "cantidad": INT,
             "precio": NUM, "estado": STR, "usua_id": INT, "det_etc_id": INT},
            required=("codigo", "nombre", "cantidad", "precio")),
        detail=True, id_in_path=True, validated=True),
    # Aun sin /{id}: PUT/DELETE van a "/" (pendiente de plantilla).
    dict(prefix="/proveedores", tag="Proveedores", schema=schema({
        "uuid": STR, "per_id": INT}),
        input=input_schema({"uuid": STR, "per_id": INT}),
        detail=False, id_in_path=False),
    dict(prefix="/usuarios", tag="Usuarios", schema=schema({
        "uuid": STR, "nombre": STR, "correo": STR,
        "estado": STR, "det_etc_id": INT}),
        input=input_schema({"uuid": STR, "nombre": STR, "correo": STR,
            "contrasena": STR, "estado": STR, "det_etc_id": INT}),
        detail=False, id_in_path=False),
    dict(prefix="/ventas", tag="Ventas", schema=schema({
        "uuid": STR, "fecha": STR, "usua_id": INT, "cli_id": INT}),
        input=input_schema({"uuid": STR, "fecha": STR, "usua_id": INT, "cli_id": INT}),
        detail=False, id_in_path=False),
    dict(prefix="/ventas-productos", tag="VentasProductos", schema=schema({
        "uuid": STR, "cantidad": INT, "vent_id": INT, "prod_id": INT}),
        input=input_schema({"uuid": STR, "cantidad": INT, "vent_id": INT, "prod_id": INT}),
        detail=False, id_in_path=False),
]


def id_param(name="id"):
    return {"name": name, "in": "path", "required": True,
            "schema": {"type": "integer"}}


def err_responses(*codes):
    out = {}
    for c in codes:
        out[str(c)] = {"description": {400: "Validación", 404: "No encontrado"}.get(c, "Error"),
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}}
    return out


def build():
    paths = {}
    schemas = {"Error": ERROR, "Message": MESSAGE}
    for r in RESOURCES:
        name = r["tag"]
        schemas[name] = r["schema"]
        schemas[name + "Input"] = r["input"]
        validated = r.get("validated", False)
        post_codes = {"201": {"description": name[:-1] + " creado" if name.endswith("s") else name + " creado",
                              "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}}}}
        if validated:
            post_codes.update(err_responses(400))

        if r["id_in_path"]:
            paths[r["prefix"] + "/"] = {
                "get": {"tags": [name], "summary": f"Listar {r['prefix'][1:]}",
                        "responses": {"200": {"description": "Lista",
                                              "content": {"application/json": {"schema": {
                                                  "type": "array",
                                                  "items": {"$ref": f"#/components/schemas/{name}"}}}}}}},
                "post": {"tags": [name], "summary": f"Crear {r['prefix'][1:]}",
                         "requestBody": {"required": True, "content": {"application/json": {
                             "schema": {"$ref": f"#/components/schemas/{name}Input"}}}},
                         "responses": post_codes},
            }
            detail = {
                "put": {"tags": [name], "summary": f"Actualizar {r['prefix'][1:]}",
                        "parameters": [id_param()], "requestBody": {"required": True,
                        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}Input"}}}},
                        "responses": {"200": {"description": "Actualizado",
                                              "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}},
                                      **err_responses(400 if validated else 404, 404)}},
                "delete": {"tags": [name], "summary": f"Eliminar {r['prefix'][1:]}",
                           "parameters": [id_param()],
                           "responses": {"200": {"description": "Eliminado",
                                                 "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}},
                                         **err_responses(404)}},
            }
            if r["detail"]:
                detail["get"] = {"tags": [name], "summary": f"Obtener {r['prefix'][1:]} por ID",
                                 "parameters": [id_param("prod_id") if r["prefix"] == "/productos" else id_param()],
                                 "responses": {"200": {"description": "Encontrado",
                                                       "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}}},
                                               **err_responses(404)}}
                key = r["prefix"] + "/{prod_id}" if r["prefix"] == "/productos" else r["prefix"] + "/{id}"
            else:
                key = r["prefix"] + "/{id}"
            paths[key] = detail
        else:
            # Estado real: sin /{id}; PUT/DELETE a "/" (roto, pendiente plantilla).
            paths[r["prefix"] + "/"] = {
                "get": {"tags": [name], "summary": f"Listar {r['prefix'][1:]}",
                        "responses": {"200": {"description": "Lista",
                                              "content": {"application/json": {"schema": {
                                                  "type": "array",
                                                  "items": {"$ref": f"#/components/schemas/{name}"}}}}}}},
                "post": {"tags": [name], "summary": f"Crear {r['prefix'][1:]}",
                         "requestBody": {"required": True, "content": {"application/json": {
                             "schema": {"$ref": f"#/components/schemas/{name}Input"}}}},
                         "responses": post_codes},
                "put": {"tags": [name], "summary": f"Actualizar {r['prefix'][1:]} (pendiente plantilla: hoy sin /{{id}})",
                        "responses": {"200": {"description": "Actualizado",
                                              "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}}}},
                "delete": {"tags": [name], "summary": f"Eliminar {r['prefix'][1:]} (pendiente plantilla: hoy sin /{{id}})",
                           "responses": {"200": {"description": "Eliminado",
                                                 "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}}}},
            }

    paths["/auth/forgot-password"] = {
        "post": {"tags": ["Auth"], "summary": "Solicitar restablecimiento de contraseña",
                 "requestBody": {"required": True, "content": {"application/json": {
                     "schema": {"type": "object", "required": ["correo"],
                                "properties": {"correo": {"type": "string", "format": "email"}}}}}},
                 "responses": {"200": {"description": "Correo enviado",
                                       "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Message"}}}},
                               **err_responses(400, 502, 503)}}
    }

    return {
        "openapi": "3.0.3",
        "info": {"title": "API MARQUEZA",
                 "description": "API REST de gestión para confecciones MARQUEZA. "
                                "Solo `productos` replica la plantilla validada; el resto documenta "
                                "la superficie real y queda pendiente de migración.",
                 "version": "1.0.0"},
        "servers": [{"url": "http://localhost:5000"}],
        "tags": [{"name": r["tag"]} for r in RESOURCES] + [{"name": "Auth"}],
        "paths": paths,
        "components": {"schemas": schemas},
    }


if __name__ == "__main__":
    spec = build()
    out = BASE / "swagger.json"
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Escrito {out}: {len(spec['paths'])} paths, "
          f"{sum(len(v) for v in spec['paths'].values())} operaciones, "
          f"{len(spec['components']['schemas'])} esquemas.")
