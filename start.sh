#!/bin/sh
set -e

echo "Starting CineMatch FastAPI serving engine on 127.0.0.1:8000..."
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 &

echo "Waiting for backend health check..."
until curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; do
  sleep 0.5
done
echo "Backend is healthy!"

echo "Starting CineMatch Next.js web application on port ${PORT:-3000}..."
cd apps/web
exec npm start -- -p ${PORT:-3000}
