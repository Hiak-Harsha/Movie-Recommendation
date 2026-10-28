#!/bin/sh
set -e

PUBLIC_PORT="${PORT:-10000}"

echo "Starting CineMatch FastAPI serving engine on 127.0.0.1:8000..."
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 &

echo "Waiting for backend health check..."
COUNT=0
until curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; do
  COUNT=$((COUNT + 1))
  if [ $COUNT -gt 60 ]; then
    echo "Backend startup timed out after 30 seconds."
    exit 1
  fi
  sleep 0.5
done
echo "Backend is healthy!"

echo "Starting CineMatch Next.js web application on 0.0.0.0:${PUBLIC_PORT}..."
cd apps/web
exec npx next start -H 0.0.0.0 -p "${PUBLIC_PORT}"
