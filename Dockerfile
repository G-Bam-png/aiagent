# Universal image — works on Render, Koyeb, Fly.io, Hugging Face Spaces, Railway, etc.
FROM python:3.12-slim

WORKDIR /app

# deps first (better layer caching)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# app + frontend (backend serves the frontend from ../frontend)
COPY backend backend
COPY frontend frontend

WORKDIR /app/backend

# Hosts inject the port via $PORT; default 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
