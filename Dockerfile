
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build



FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist


ENV PYTHONPATH=/app
ENV FLASK_APP=app.py

EXPOSE 5000

CMD ["python", "app.py"]