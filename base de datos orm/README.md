# Base de datos, ORM SQLAlchemy y Dokploy

Esta carpeta documenta la estructura actual, permite inspeccionar el esquema MySQL con SQLAlchemy y contiene una configuracion Compose para desplegar el frontend y la API en Dokploy.

## Diagnostico del repositorio

Ejecuta desde cualquier directorio:

```powershell
python "base de datos orm sqlalchemy/analizar_estructura.py"
```

El informe enumera archivos por tipo y capas Python, detecta servicios que siguen usando cursores MySQL, busca definiciones SQL de tablas y muestra archivos de contenedor. Excluye entornos virtuales, dependencias y archivos generados. No lee valores de archivos `.env`.

Hallazgos del codigo revisado:

- `frontend/` contiene la interfaz estatica; el `Dockerfile` de la raiz la sirve con Nginx.
- `backend/API/` contiene una API Flask organizada en `Routes/`, `Controllers/`, `Services/` y `Models/`.
- Las clases en `Models/` son objetos de transferencia. SQLAlchemy refleja las 13 tablas al arrancar la API y los 13 servicios usan sesiones ORM.
- Las escrituras usan sesiones con commit/rollback. La reflexion no crea ni altera tablas; el DDL exportado es solo una fotografia del esquema.
- La respuesta de usuarios omite `contrasena`. La columna heredada sigue siendo `VARCHAR(45)` y el almacenamiento/autenticacion de contrasenas necesita una migracion de seguridad aparte antes de exponer la API en produccion.
- El esquema se exporta a `schema.mysql.sql` sin datos. Compose usa una instancia MySQL externa y no crea ni altera tablas.
- La interfaz no esta conectada a la API actualmente; publicarlas juntas no crea esa integracion.

## DDL y modelos ORM

Para exportar las definiciones reales de las tablas (sin registros), usa `backend/API/.env` o las variables `MYSQL_*`:

```powershell
python "base de datos orm sqlalchemy/exportar_ddl.py"
```

El comando genera `schema.mysql.sql` en esta carpeta. SQLAlchemy refleja y valida los 13 modelos a partir del esquema existente; no ejecuta cambios DDL.

## Inspeccion ORM del esquema existente

Instala las dependencias y define `DATABASE_URL` apuntando a una base que ya tenga las tablas:

```powershell
python -m pip install -r "base de datos orm sqlalchemy/requirements-backend.txt"
$env:DATABASE_URL = "mysql+mysqldb://usuario:clave@servidor:3306/base?charset=utf8mb4"
python "base de datos orm sqlalchemy/inspeccionar_esquema.py"
```

SQLAlchemy refleja tablas, columnas, tipos, claves primarias y foraneas; no crea, modifica ni borra tablas. Codifica caracteres especiales de usuario/clave como URL-encoding. El modulo `database.py` tambien expone `Base` y `SessionLocal` para empezar a consultar las clases reflejadas.

## Despliegue en Dokploy

1. Crea una aplicacion de tipo Docker Compose y usa `base de datos orm sqlalchemy/compose.yaml` como archivo Compose. El contexto de construccion esta configurado como la raiz del repositorio.
2. Configura estas variables en Dokploy, usando una base MySQL existente y accesible desde la red del despliegue:
   - `MYSQL_HOST`: hostname privado o direccion del servidor MySQL.
   - `MYSQL_PORT`: puerto, normalmente `3306`.
   - `MYSQL_USER`: usuario de la API.
   - `MYSQL_PASSWORD`: clave de la API.
   - `MYSQL_DB`: nombre de la base que ya contiene el esquema esperado por la API.
3. Despliega los servicios `frontend` (puerto interno `80`) y `api` (puerto interno `5000`) y asigna dominios desde Dokploy. No publiques MySQL a Internet.
4. Si la API debe ser accesible desde el navegador, configura el proxy/dominio de `api` y actualiza la URL base de la interfaz: el frontend actual aun no consume sus endpoints.

El despliegue del backend no inicializa la base. Haz una copia de seguridad antes de cualquier migracion; la migracion de servicios debe continuar gradualmente y validarse contra este esquema.

## Contratos CRUD

Las rutas usan `POST /recurso` con JSON, y `PUT /recurso/<id>` o `DELETE /recurso/<id>` para modificar por ID. Los campos obligatorios son:

- `/productos`: `codigo`, `nombre`, `cantidad`, `precio`, `estado`, `usuario_id`, `det_etc_id`.
- `/proveedores`: `persona_id`.
- `/usuarios`: `nombre`, `correo`, `contrasena`, `estado`, `det_etc_id`.
- `/ventas`: `fecha` en formato `AAAA-MM-DD`, `usua_id`, `cli_id`.
- `/ventas-productos`: `cantidad`, `vent_id`, `prod_id`.

Las cinco rutas responden `400` si falta algun campo obligatorio. No se devuelve la contrasena en `GET /usuarios`.

## Instalar Docker Desktop en Windows

En esta maquina falta WSL y la sesion no tiene permisos de administrador, por lo que la instalacion automatica no se pudo completar. Ejecuta PowerShell como administrador, instala WSL y reinicia Windows; despues instala Docker Desktop:

```powershell
wsl --install
winget install --id Docker.DockerDesktop -e
```

Abre Docker Desktop y espera a que el motor este activo. Comprueba con `docker version` y `docker compose version`.
