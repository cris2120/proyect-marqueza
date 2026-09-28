# MARQUEZA en Dokploy

El repositorio incluye un `docker-compose.yml` con tres servicios:

- `frontend`: Nginx sirve el sitio y reenvía `/api/*` al backend en la red interna.
- `api`: FastAPI autentica con JWT y sirve las colecciones y usuarios.
- `db`: PostgreSQL con volumen persistente `marqueza_db`.

La API usa tablas propias para usuarios, auditoría y solicitudes de recuperación. Los seis módulos operativos guardan sus registros como documentos JSON versionados en PostgreSQL; esto conserva los campos actuales y los productos anidados de las cotizaciones sin perder los datos al cambiar de dispositivo.

## Configuración

En Dokploy crea una aplicación Compose desde la raíz del repositorio. No publiques PostgreSQL ni el puerto de la API. Asigna el dominio público al servicio `frontend` y configura su puerto destino como `80`.

Agrega estas variables en la configuración de entorno de Dokploy antes de desplegar:

| Variable | Valor |
| --- | --- |
| `POSTGRES_DB` | `marqueza` |
| `POSTGRES_USER` | `marqueza` |
| `POSTGRES_PASSWORD` | Contraseña larga y única para PostgreSQL |
| `JWT_SECRET` | Secreto aleatorio de al menos 32 caracteres |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | `admin1234` para el primer acceso; reemplázala por una contraseña robusta al desplegar |
| `ADMIN_EMAIL` | Correo operativo del administrador |

No uses los valores de ejemplo para las claves de producción. Guarda las variables en Dokploy, no en el repositorio. La contraseña del administrador se almacena con hash Argon2; se vuelve a aplicar desde `ADMIN_PASSWORD` al iniciar la API.

Abre `https://tu-dominio/api/health` para comprobar la API y `https://tu-dominio/api/docs` para revisar OpenAPI. Inicia sesión con `admin` y la contraseña configurada. La base de datos se conserva en el volumen de PostgreSQL aunque se reconstruyan los contenedores.

## Datos locales existentes

Al entrar por primera vez como administrador, la interfaz importa a PostgreSQL los datos que ya existan en el `localStorage` de ese navegador. Esa importación solo puede copiar datos desde un dispositivo; después, los cambios sincronizados quedan disponibles desde otros dispositivos.

Los nuevos registros creados desde el formulario público se asignan al rol `Empleado`. La cuenta `admin` se crea automáticamente y no se puede editar ni eliminar desde el módulo de usuarios.

## Desarrollo local

Desde la raíz del repositorio, copia `.env.example` a `.env`, reemplaza las claves de ejemplo y ejecuta:

```sh
docker compose up --build
```

Abre `http://localhost:8080`. Para desarrollo, el archivo `.env.example` define el puerto local `8080`; en Dokploy el proxy enruta el dominio al puerto interno `80` del frontend.