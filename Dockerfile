FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CORPUS_SOURCE_DIR=/app/corpus \
    RAG_DATA_DIR=/data/rag
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY crawler/output/wontfallinyourlap/metadata/ ./corpus/metadata/
COPY crawler/output/xuzhe/*.mhtml ./corpus/manual/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
RUN useradd --create-home appuser && mkdir -p /data/rag && chown appuser:appuser /data/rag
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
