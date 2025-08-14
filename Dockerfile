# Build stage (optional here, but leaves room for node/asset pipelines later)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000
# use gunicorn in prod
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
