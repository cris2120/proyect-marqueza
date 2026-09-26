# MARQUEZA

Aplicacion web de gestion para MARQUEZA.

## Despliegue en Dokploy

1. Crea una aplicacion desde este repositorio y selecciona el metodo de construccion `Dockerfile`.
2. Usa la raiz del repositorio como contexto de construccion y `/Dockerfile` como archivo Dockerfile.
3. Configura el puerto del contenedor como `80` y asigna el dominio de la aplicacion.
4. Despliega la aplicacion. La pagina de inicio redirige al formulario de inicio de sesion.

La imagen publica los archivos de `frontend/` con Nginx. No requiere variables de entorno para servir la pagina.

## Ejecucion local con Docker

```sh
docker build -t marqueza-frontend .
docker run --rm -p 8080:80 marqueza-frontend
```

Abre `http://localhost:8080`.

## Alcance actual

Esta configuracion despliega solo el frontend. Actualmente, las pantallas guardan sus datos en `localStorage`; la API Flask y MySQL no se incluyen en esta imagen ni estan conectadas al frontend.
