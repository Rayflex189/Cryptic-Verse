FROM python:3.11-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------- Backend ----------
COPY backend/ /app/backend/

RUN pip install --upgrade pip
RUN pip install -r /app/backend/requirements.txt

# ---------- Frontend ----------
COPY frontend/ /app/frontend/

WORKDIR /app/frontend

RUN npm install
RUN npm run build

# Copy built frontend into Django static folder
RUN mkdir -p /app/backend/staticfiles
RUN cp -r dist/* /app/backend/staticfiles/

# ---------- Django ----------
WORKDIR /app/backend

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
