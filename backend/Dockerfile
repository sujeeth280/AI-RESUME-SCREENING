# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY ../frontend/package*.json ./
RUN npm ci
COPY ../frontend/ ./
RUN npm run build

# ── Stage 2: Python backend + serve built frontend ────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Copy built React app into backend/static
COPY --from=frontend-builder /frontend/dist /app/static

# Create runtime directories
RUN mkdir -p uploads output /app/data

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
