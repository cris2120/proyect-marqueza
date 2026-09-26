# Reporte de bugs, fallas y mejoras — MARQUEZA

Fecha: 2026-09-26.
Alcance: `backend/API` (Flask + MySQL) y `frontend/` (HTML/CSS/JS vanilla).
Método: lectura directa del código, `git diff`, `py_compile`,
`python generate_openapi.py` y `docker compose config`.
Stack a mantener: Flask + `flask_mysqldb` + MySQL/MariaDB + frontend sin framework.

> Nota para el compañero: ya están hechos el OpenAPI (`generate_openapi.py` +
> `swagger.json`, 23 paths) y el módulo `productos` como plantilla correcta.
> Todo lo que sigue es lo que **tú debes replicar** en los demás módulos.
> `productos` es la referencia; no inventes otra forma de hacerlo.

---

## 1. Resumen ejecutivo

| # | Problema | Severidad | Estado |
|---|----------|-----------|--------|
| B1 | 4 blueprints devuelven referencia a función en vez de respuesta (`POST/PUT/DELETE` muertos) | Crítica | Pendiente (compañero) |
| B2 | 4 services insertan strings literales (`"vent_uuid, ..."`) como datos | Crítica | Pendiente |
| B3 | `UPDATE` sin `WHERE` en 4 módulos (sobrescribe toda la tabla) | Crítica | Pendiente |
| B4 | `DELETE` con id literal (`"vent_id"`) que nunca borra el registro pedido | Crítica | Pendiente |
| B5 | Auth real inexistente (solo `forgot-password` en memoria, sin login/register/hash) | Crítica | Pendiente |
| B6 | Frontend 100% `localStorage`, sin `fetch` al API, login en claro, XSS por `innerHTML` | Alta | Pendiente |
| B7 | Sin validación ni `404/400` fuera de `productos`; `KeyError` ante JSON incompleto | Alta | Pendiente |
| B8 | `print()` de debug, cursores sin `try/finally`, códigos HTTP fijos `200` | Media | Pendiente |
| B9 | `schema.sql` sin FKs, sin `UNIQUE`, sin índices, sin seed | Media | Pendiente |
| B10 | Rutas con `/<id>` sin conversor, sin `GET /<id>`, inconsistencias de estilo | Media | Pendiente |
| B11 | CORS solo en `auth_bp`, sin `/health`, config frágil, docs incompletos | Media | Parcial (docs OK) |
| B12 | Duplicación frontend (`productos.js` 528 líneas repite sidebar) y exports inconsistentes | Media | Pendiente |

Lo ya corregido (base para replicar): `productos_bp.py`, `productos_controller.py`,
`productos_services.py`, `config.py` (`MYSQL_PORT`), `app.py` (shim PyMySQL +
`__main__`), `requirements.txt`, `schema.sql`, `Dockerfile`/`compose` livianos,
`swagger.json` + generador, `CHANGELOG.md`.

---

## 2. Backend — bugs críticos (grupo B: `usuarios`, `ventas`, `proveedores`, `ventas-productos`)

### B1. Rutas que no invocan al controlador

Archivos:
`Routes/ventas_bp.py:13,18,23`, `Routes/usuarios_bp.py:13,18,23`,
`Routes/proveedor_bp.py:13,18,23`, `Routes/vent_prod_bp.py:13,18,23`.

Código actual:

```python
@ventas_bp.route('/', methods=['POST'])
def createVentas():
    x = cntAddVentas   # ← falta ()
    return x
```

Efecto: Flask intenta serializar una función Python como respuesta.
`GET` sí funciona (lleva `()`), pero `POST/PUT/DELETE` están muertos.
Además `PUT/DELETE` van a `/` sin identificador, así que aunque se invocaran
no sabrían qué registro tocar.

Referencia correcta (`Routes/productos_bp.py:20-30`):

```python
@productos_bp.route('/', methods=['POST'])
def createProductos():
    return cntAddProductos()

@productos_bp.route('/<int:prod_id>', methods=['PUT'])
def updateProductos(prod_id):
    return cntModProductos(prod_id)
```

Qué hacer: copiar ese patrón en los 4 archivos, con `GET /<int:id>` nuevo.

### B2. Services que insertan basura literal

Archivos:
`Services/ventas_services.py:26,46`, `Services/usuarios_services.py:26,46`,
`Services/vent_prod_services.py:26,46`, `Services/proveedor_services.py:26,46`.

Código actual:

```python
c.execute(sql, ("vent_uuid, vent_pro_codigo, vent_pro_nombre, vent_usua_id, vent_cli_id"))
```

Dos errores en una línea: (a) no lee `request.get_json()`, inserta el nombre
de las columnas como si fuera el valor; (b) el segundo argumento de
`execute()` debe ser una tupla con un elemento por `%s` — aquí se pasa un
string único (o tupla mal formada), así que el INSERT mete basura o falla
según el driver. Compárese con la plantilla (`productos_services.py:61-81`)
que valida el payload y pasa 8 parámetros reales.

Qué hacer: cada `addX(payload)` debe recibir `dict`, validar campos
obligatorios y tipos (`cantidad int >= 0`, `precio number >= 0`, `correo` con
`@`, etc.), generar `uuid` en servidor y devolver `{"id": new_id, ...}`.

### B3. `UPDATE` sin `WHERE` — actualiza toda la tabla

Archivos:
`Services/ventas_services.py:43`, `Services/usuarios_services.py:43`,
`Services/proveedor_services.py:43`, `Services/vent_prod_services.py:43`.

```sql
UPDATE T_VENTAS SET VENT_UUID = %s, ...   -- sin WHERE
```

Un solo `PUT` sobrescribe **todos** los registros. Los módulos del grupo A
(`cotizaciones_services.py:46`, `insumos_services.py:47`,
`cliente_services.py:50`, etc.) sí tienen `WHERE ID = %s`; los del grupo B no.
La plantilla (`productos_services.py:98-102`) termina con
`WHERE PROD_ID = %s` y devuelve `c.rowcount > 0` para distinguir `404`.

Qué hacer: agregar `WHERE <PK> = %s` y pasar el `id` de la URL como último
parámetro. Jamás tomar el `id` del body.

### B4. `DELETE` con id literal

```python
c.execute(sql, ("vent_id",))   # Services/ventas_services.py:36
c.execute(sql, ("usua_id",))   # Services/usuarios_services.py:36
```

Se borra (o se intenta borrar) el registro cuyo id sea el texto `"vent_id"`,
que nunca existe. El controlador además ignora la URL porque la ruta no tiene
`/<id>`. Plantilla: `deleteProductos(prod_id)` con `WHERE PROD_ID = %s` y
`return c.rowcount > 0`.

### B5. Controladores que ignoran el request y mienten el status

`Controllers/usuarios_controller.py:8-18`, `ventas_controller.py`,
`proveedor_controller.py`, `vent_prod_controller.py`: `addX()` sin argumentos,
sin `request.get_json()`, siempre `200` (incluso `update` devuelve `201` en
usuarios, al revés de lo estándar). No hay `try/except ValueError → 400` ni
`404` cuando `rowcount == 0`.

Plantilla (`productos_controller.py:20-42`): `payload = request.get_json(silent=True) or {}`,
`try/except ValueError → 400`, `if not updated/deleted → 404`, `POST → 201`.

---

## 3. Backend — fallas altas/medias (grupo A + transversal)

Los módulos `clientes`, `insumos`, `cotizaciones`, `contactos`, `personas`,
`etc`, `detalles-etc`, `productos-insumos` están mejor (rutas con `()`,
services con parámetros y `WHERE`), pero comparten estas fallas:

### B7a. Sin validación, `KeyError` ante JSON incompleto

`Controllers/insumos_controller.py:11-18` hace `data["codigo"]` directo.
Si el frontend omite un campo o manda `Content-Type` distinto,
`data` es `None` y la app responde `500` con traceback (en `debug=True`
expone código fuente). `cliente_controller.py:10` usa `request.json["persona_id"]`
con el mismo riesgo.

Mejora (plantilla): `_validate_payload()` central por módulo +
`request.get_json(silent=True) or {}` + `400 {"message": "Faltan campos: ..."}`.

### B7b. Sin `GET /<id>` ni `404`

Ningún módulo del grupo A tiene detalle por id. El frontend no puede
precargar un formulario de edición desde el API. Agregar
`GET /<int:id> → 200 | 404` como en `productos`.

### B8. Higiene: `print()`, cursores, status fijos

- `print(data)` en `usuarios_services.py:11,17`, `ventas_services.py:11,17`,
  `cotizaciones_services.py:13,19`, `cliente_services.py:13,19`, etc.
  Contaminan logs de Docker y pueden filtrar datos.
- Cursores abiertos sin `try/finally`: si `execute()` lanza, la conexión
  queda colgada. Plantilla usa `try: ... finally: c.close()`.
- `POST → 200` y `PUT → 201` mezclados (`insumos_controller.py:21,40`).
  Estándar: `POST → 201`, `PUT/DELETE → 200`, `GET → 200`, `400/404` según caso.

### B10. Rutas con `/<id>` sin conversor

`cliente_bp.py:16-23`, `insumos_bp.py:15-22`, `cotizaciones_bp.py`, etc.
usan `/<id>` (string). Debe ser `/<int:id>` para rechazar `/abc` con `404`
automático y evitar inyección de tipo en SQL. Solo `productos` lo hace bien.

### B11. Auth, CORS, config, docs

- `Routes/auth_bp.py:48-67`: solo `forgot-password`. Tokens en dict en memoria
  (`_reset_tokens`), se pierden al reiniciar, sin endpoint de consumo del
  token ni cambio real de contraseña. Sin `register/login/logout`,
  sin hash (`werkzeug.security` está en requirements pero sin usar),
  sin protección en ningún otro blueprint.
- CORS solo vía `after_request` en `auth_bp` (`auth_bp.py:40-45`):
  el resto de blueprints no aceptan `fetch` cross-origin. Mover a CORS global
  en `app.py` o extensión `flask-cors`.
- `config.py`: ya corregido el `TypeError` del puerto, pero sigue sin validar
  que `MYSQL_HOST/USER/DB` existan; el error aparece tarde y confuso.
- `documentacion_bp.py`: título `CCCCC`, sin `try` si falta `swagger.json`.
- `app.py` corre con `debug=True` siempre: bien para SENA local, prohibido
  para cualquier despliegue.

---

## 4. Base de datos (`schema.sql`)

`schema.sql:1-129` crea las 13 tablas y hoy es suficiente para levantar,
pero:

1. Sin FKs (`PROD_USUA_ID`, `VENT_CLI_ID`, etc. son `INT NULL` sueltos).
   Se pueden borrar usuarios con ventas huérfanas. Decisión temporal
   documentada; agregar `FOREIGN KEY ... ON DELETE RESTRICT` cuando los
   services validen existencia.
2. Sin `UNIQUE` (`PROD_CODIGO`, `USUA_CORREO`, `INS_CODIGO` aceptan duplicados).
3. Sin índices (`INDEX idx_ventas_cli (VENT_CLI_ID)`, etc.).
4. Sin `seed.sql`: cada frontend arranca con datos quemados distintos
   (`productos.js:47-52` trae 2 productos de ejemplo).
5. Tipos: `UUID VARCHAR(64)` sin `UNIQUE NOT NULL`; `PRECIO DECIMAL(12,2)`
   correcto, pero el frontend manda floats sin redondeo.

---

## 5. Frontend

### B6a. Desconectado del API

Todos los CRUD leen/escriben `localStorage`:
`shared/pagina-crud.js:35-45`, `productos/productos.js:36-57`,
`clientes/clientes.js`, `proveedores`, `ventas`, `usuarios`.
No existe ningún `fetch()`, ni `API_BASE_URL`, ni `api-client.js`.
El backend puede estar caído y la app "funciona", ocultando que nada persiste
en MySQL. Migración pendiente (contrato en `FRONTEND_PROMPT.md:77-79`):
centralizar `fetchJSON()`, piloto `productos`, resto después, `localStorage`
como caché con migración de claves (`marqueza_clientes`, etc. no renombrar).

### B6b. Login en claro

`inicio_sesion/inicio_sesion.js:12-56`: compara
`String(user.contrasena) === password` contra usuarios guardados en claro en
`localStorage`. Sin hash, sin sesión expirable, `marqueza_usuario_sesion`
falsificable desde consola. Cuando exista `POST /auth/login`, guardar solo
token en `sessionStorage` y proteger rutas con redirección
(`?motivo=sesion_requerida` ya existe).

### B6c. XSS por `innerHTML`

`productos/productos.js:155-175` interpola `producto.codigo/nombre/...`
en `tr.innerHTML`. Con datos locales es inocuo; contra el API un nombre como
`<img src=x onerror=...>` se ejecuta. `pagina-crud.js:82-89` sí usa
`textContent` (correcto). Unificar todo a `createElement`/`textContent`.

### B12. Duplicación y consistencia

- `productos.js` (528 líneas) repite sidebar/responsive/tema
  (`productos.js:369-528`) en vez de `MarquezaAppShell` (`shared/`).
  `insumos.js` hace lo mismo. Cualquier cambio de menú hay que hacerlo N veces.
- Export: `pagina-crud.js:52-70` exporta CSV, `productos.js:220-268` exporta PDF
  con `jsPDF`. Definir uno solo (PDF para entregable SENA) o ambos en el base.
- Validación solo de presencia (`pagina-crud.js:135`, `productos.js:279-283`):
  sin rangos, sin `type=email`, sin mensajes por campo.

---

## 6. Matriz por módulo (qué copiar de `productos`)

| Módulo | Ruta invoca `()` | `PUT/DELETE /<id>` | Service lee payload | `WHERE` | Valida + `400/404` | Acción |
|--------|------------------|---------------------|---------------------|---------|---------------------|--------|
| productos | ✅ | ✅ `/<int:prod_id>` | ✅ | ✅ | ✅ | Referencia, no tocar |
| clientes | ✅ | ⚠️ `/<id>` string | ✅ | ✅ | ❌ | Cambiar a `<int:id>`, agregar validación + `GET /<id>` + `404` |
| insumos | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual + `400` tipos |
| cotizaciones | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| contactos | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| personas | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| etc | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| detalles-etc | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| productos-insumos | ✅ | ⚠️ `/<id>` | ✅ | ✅ | ❌ | Igual |
| usuarios | ❌ | ❌ `/` | ❌ literal | ❌ | ❌ | Reescribir completo desde plantilla |
| ventas | ❌ | ❌ `/` | ❌ literal | ❌ | ❌ | Reescribir completo |
| proveedores | ❌ | ❌ `/` | ❌ literal | ❌ | ❌ | Reescribir completo |
| ventas-productos | ❌ | ❌ `/` | ❌ literal | ❌ | ❌ | Reescribir completo |

---

## 7. Plan de mejoras (mismo stack, por fases)

**Fase 0 — Estabilidad (hacer ya, 1-2 días).**
Reescribir grupo B copiando `productos` archivo por archivo; en grupo A
cambiar `/<id>` → `/<int:id>`, agregar `GET /<id>`, `_validate_payload`,
`try/finally`, quitar `print()`, unificar `200/201/400/404`. Regenerar
`swagger.json`. Criterio de salida: `POST → 201`, `PUT/DELETE inexistente → 404`,
`POST sin campos → 400`, ningún `UPDATE` sin `WHERE`.

**Fase 1 — Auth mínima.**
`POST /auth/register` (hash `werkzeug.security`), `POST /auth/login`
(token con `itsdangerous`), decorador `@login_required`, `POST /auth/reset`
que consuma el token de `forgot-password`. Frontend guarda token, no claves.

**Fase 2 — Frontend→API.**
`shared/api-client.js` + piloto `productos` end-to-end, luego resto.
`textContent` en todas las tablas, estados carga/vacío/error.

**Fase 3 — Datos.**
FKs + `UNIQUE` + índices + `seed.sql` demo para la sustentación.

**Fase 4 — Entregable SENA.**
`README.md` con arranque en 5 comandos, manual de uso, checklist de demo
(CRUD × módulo, login, export PDF, docs `/documentacion`).

---

## 8. Checklist para el compañero (antes de pedir revisión)

- [ ] Los 4 módulos del grupo B responden `POST/PUT/DELETE` (no devuelven función).
- [ ] Ningún `UPDATE` sin `WHERE`; ningún `DELETE` con id literal.
- [ ] Ningún `c.execute(sql, ("texto_con_comas"))`; cada `%s` tiene su parámetro.
- [ ] `POST` incompleto → `400`; `GET/PUT/DELETE` inexistente → `404`.
- [ ] Cero `print()`; cursores con `try/finally`.
- [ ] `python generate_openapi.py` regenerado y `/documentacion` abre sin 404.
- [ ] `docker compose up --build` levanta `db` sana + `api` respondiendo `/productos/`.

## 9. Comandos de verificación

```bash
pip install -r backend/API/requirements.txt
python -m py_compile backend/API/app.py backend/API/config.py backend/API/generate_openapi.py
cd backend/API && python generate_openapi.py
cd backend/API && docker compose config > /dev/null && echo "compose OK"
cd backend/API && cp .env.example .env && docker compose up --build
curl -s http://localhost:5000/productos/ | head -c 300
curl -s -X POST http://localhost:5000/productos/ -H 'Content-Type: application/json' -d '{}' -w '\n%{http_code}\n'
```
