FROM python:3.11-slim-bookworm

LABEL maintainer="iamValen" \
      description="Media Downloader - YouTube and media content downloader" \
      version="1.0.0"

RUN groupadd -r appuser -g 1000 && \
    useradd -r -g appuser -u 1000 -m -s /sbin/nologin appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --chown=appuser:appuser requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/downloads /app/temp && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/api/config', timeout=5)" || exit 1

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]