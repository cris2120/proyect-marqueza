FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Sin apt: PyMySQL es puro-Python, no hay nada que compilar.
# (Antes: build-essential + default-libmysqlclient-dev ~300MB y lento.)

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
