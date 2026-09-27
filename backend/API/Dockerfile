FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=80 \
    MYSQL_PORT=3306 \
    MYSQL_HOST=https://api-marqueza.zona52.lat \
    MYSQL_USER=root \
    MYSQL_PASSWORD= \
    MYSQL_DB=marqueza_db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . ./

EXPOSE 80
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]
