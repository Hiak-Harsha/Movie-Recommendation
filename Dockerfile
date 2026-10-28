# ==========================================
# CineMatch Unified Full-Stack Production Container
# Packages Next.js 16 frontend + FastAPI ML backend into 1 service
# ==========================================

# Stage 1: Build Next.js Web Frontend
FROM node:20-alpine AS web-builder
WORKDIR /app

COPY package.json package-lock.json* ./
COPY packages/api-client/package.json ./packages/api-client/
COPY apps/web/package.json ./apps/web/

RUN npm install

COPY packages/ ./packages/
COPY apps/web/ ./apps/web/

RUN cd packages/api-client && npm run build
RUN cd apps/web && npm run build

# Stage 2: Unified Python + Node Production Runtime
FROM python:3.11-slim

WORKDIR /app

# Install Node.js, npm, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application source, artifacts, and data
COPY apps/ apps/
COPY ml/ ml/
COPY artifacts/ artifacts/
COPY data/ data/
COPY packages/ packages/
COPY eval_results.json strategy.json ./

# Copy built Next.js artifacts and dependencies from Stage 1
COPY --from=web-builder /app/apps/web/public ./apps/web/public
COPY --from=web-builder /app/apps/web/.next ./apps/web/.next
COPY --from=web-builder /app/apps/web/node_modules ./apps/web/node_modules
COPY --from=web-builder /app/apps/web/package.json ./apps/web/package.json

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Public port (Render, Railway, Cloud Run assign $PORT)
ENV PORT=3000
ENV NODE_ENV=production
ENV INTERNAL_API_URL=http://127.0.0.1:8000
EXPOSE 3000

CMD ["./start.sh"]
