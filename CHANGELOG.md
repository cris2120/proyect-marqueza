# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).
Este proyecto aún no tiene releases versionados; los cambios se agrupan bajo `[No publicado]`.

## [No publicado] - 2026-09-26

### Contexto

El repositorio es un proyecto de grado SENA para la gestión de una empresa de
confecciones (MARQUEZA). Backend en Flask + MySQL (`backend/API`) con
organización por capas `Routes → Controllers → Services → Models`, y frontend
multipágina en HTML/CSS/JS vanilla (`frontend/`).

Antes de estos cambios el backend no era ejecutable de forma reproducible:
no había `requirements.txt`, ni DDL (`schema.sql`), ni spec OpenAPI fiable
(`swagger.json` solo documentaba `/usuarios` y un recurso fantasma `/eventos`
que no existe en `Routes/__init__.py`), y el único módulo funcional era
ninguno — incluso `productos` tenía rutas que devolvían referencias a función
en lugar de respuestas.

El objetivo de esta serie de cambios es: (1) dejar el proyecto instalable y
levantable con Docker o en local, (2) documentar la superficie real del API,
(3) dejar **un módulo de referencia correcto (`productos`)** para que el resto
de módulos se migren copiando su plantilla, sin cambiar de stack.

### Agregado

- `backend/API/requirements.txt`: fija las dependencias mínimas para correr
  la API sin adivinarlas desde los imports.
  Contenido: `flask`, `flask-mysqldb`, `PyMySQL`, `python-dotenv`, `werkzeug`.
  `PyMySQL` se usa como driver puro-Python vía
  `pymysql.install_as_MySQLdb()` en `app.py`, de modo que `flask_mysqldb`
  funciona sin compilar `mysqlclient` (sin `apt`, sin `build-essential`).
  Instalación: `pip install -r backend/API/requirements.txt`.

- `backend/API/schema.sql`: DDL de las 13 tablas inferidas de los
  `INSERT/UPDATE` de `Services/*.py` y de los campos de `Models/*.py`
  (`T_PERSONA`, `T_ESTADO_TIPOS_CATEGORIAS`, `T_DETALLES_ETC`, `T_USUARIOS`,
  `T_CLIENTE`, `T_PROVEEDORES`, `T_CONTACTO`, `T_PRODUCTOS`, `T_INSUMOS`,
  `T_PRODU_INSUM`, `T_COTIZACIONES`, `T_VENTAS`, `T_VENT_PROD`).
  No existía ningún DDL en el repo; ahora `mariadb -u root < schema.sql`
  crea la base `marqueza` completa. Decisión consciente: sin FKs por ahora
  porque el código actual no las define ni las respeta; se proponen en el
  reporte de mejoras.

- `backend/API/generate_openapi.py`: generador del spec OpenAPI 3.0.3.
  Fuente de verdad: prefijos de `Routes/__init__.py` + verbos HTTP de cada
  `*_bp.py` + campos de `to_dic()` en `Models/*.py`. Solo `productos`
  declara `required` y respuestas `400/404` porque es el único con
  validación real; el resto documenta la superficie tal cual está para
  no inventar un contrato que el código no cumple.
  Uso: `cd backend/API && python generate_openapi.py`.

- `backend/API/swagger.json`: reescrito desde cero con el generador
  (23 paths, 54 operaciones, 28 esquemas). Antes documentaba recursos
  inexistentes y omitía 12 de los 15 blueprints registrados.
  Se sirve en `/documentacion` vía `Routes/documentacion_bp.py`.

- `backend/API/Dockerfile` + `docker-compose.yml` + `.dockerignore` +
  `.env.example`: entorno reproducible `api + db` (MariaDB 11).
  `schema.sql` se monta en `/docker-entrypoint-initdb.d` y se carga solo al
  primer arranque con volumen vacío; la API espera a la DB sana
  (`depends_on: service_healthy`). El `Dockerfile` final no usa `apt`:
  al usar PyMySQL no hay nada que compilar, por lo que el build es rápido
  incluso en máquinas sin Debian (ej. Arch). Arranque:
  `cd backend/API && cp .env.example .env && docker compose up --build`,
  o solo DB para desarrollo local: `docker compose up db`.

- `backend/API/ejemplos/productos_sqlalchemy.py`: ejemplo de referencia del
  modelo `T_PRODUCTOS` con SQLAlchemy 2 sobre SQLite en memoria. No se usa
  en producción; sirve como muestra de cómo se vería el modelo con un ORM.

- `REPORTE_BUGS_Y_MEJORAS.md`: auditoría amplia de bugs, fallas y mejoras
  pendientes (rutas, servicios, controladores, auth, config, frontend,
  seguridad y DX), con severidad, evidencia `archivo:línea`, impacto y
  cómo corregirlo tomando `productos` como plantilla.

### Corregido

- `backend/API/config.py`: `MYSQL_PORT` ahora usa `3306` por defecto.
  Antes `int(os.getenv(...) or ...)` evaluaba `int(None)` y lanzaba
  `TypeError` al importar la app si el `.env` no definía el puerto.
  Ahora la app arranca sin `.env` completo (falla después solo al conectar,
  que es lo esperado).

- `backend/API/app.py`: agregado shim de PyMySQL (ver arriba) y guard
  `if __name__ == "__main__":` para que importar la app (tests, OpenAPI)
  no levante el servidor. Antes el `app.run(...)` estaba a nivel de módulo.

- Módulo `productos` como plantilla de referencia
  (`Routes/productos_bp.py`, `Controllers/productos_controller.py`,
  `Services/productos_services.py`):
  - Las rutas `POST/PUT/DELETE` ahora invocan al controlador con `()`.
    Antes `x = cntAddProductos` devolvía la función sin ejecutarla.
  - `PUT/DELETE` (y nuevo `GET`) usan `/<int:prod_id>`; antes iban a `/`
    sin identificador, haciendo imposible operar sobre un registro.
  - Los services reciben `(payload)` / `(prod_id, payload)` desde el
    controlador con `request.get_json()` y validan
    (`codigo`, `nombre`, `cantidad>=0`, `precio>=0`); antes usaban strings
    literales como `"vent_uuid, vent_pro_codigo, ..."` que se insertaban
    como datos basura.
  - El `UPDATE` lleva `WHERE PROD_ID = %s`; antes actualizaba toda la tabla.
  - Nuevo `GET /<id>` con `404` si no existe; `POST` devuelve `201`;
    validación devuelve `400`. Antes todo devolvía `200/201` fijos.
  - Cursor MySQL con `try/finally` + `close()` garantizado.

- `.gitignore`: se agrega `AGENTS.md` (guía local de agentes, no versionable)
  junto a las reglas existentes de `.env` y `.venv`.

### Eliminado

- `backend/API/API.txt`: archivo residual de 1 línea sin uso.
- `AGENTS.md`: guía local de trabajo con agentes; se elimina del
  versionado y se ignora vía `.gitignore` (era archivo de apoyo, no parte
  del entregable SENA).

### Pendiente (no incluido, ver `REPORTE_BUGS_Y_MEJORAS.md`)

- Replicar la plantilla `productos` en los otros 12 módulos
  (`usuarios`, `ventas`, `clientes`, `proveedores`, `insumos`,
  `cotizaciones`, `contactos`, `personas`, `etc`, `detalles-etc`,
  `productos-insumos`, `ventas-productos`).
- Auth real (`register/login` con hash + token); hoy solo existe
  `POST /auth/forgot-password` con tokens en memoria.
- Migración del frontend de `localStorage` a `fetch` contra la API
  (piloto sugerido: `productos`).
- FKs, `UNIQUE`, índices y `seed.sql` en `schema.sql`.

### Cómo verificar

```bash
# 1. Sintaxis
python -m py_compile backend/API/app.py backend/API/config.py backend/API/generate_openapi.py

# 2. Regenerar spec (debe imprimir 23 paths, 54 operaciones, 28 esquemas)
cd backend/API && python generate_openapi.py

# 3. Validar compose (sin necesidad de daemon corriendo)
cd backend/API && docker compose config > /dev/null && echo "compose OK"

# 4. Levantar todo
cd backend/API && cp .env.example .env && docker compose up --build
# API en http://localhost:5000, docs en http://localhost:5000/documentacion
```
