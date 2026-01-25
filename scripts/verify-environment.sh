#!/bin/bash

# Environment Verification Script for Whedifaqaui
# Run this after 'docker compose up' to verify all services are working

set -e

echo "=== Whedifaqaui Environment Verification ==="
echo ""

# Check Docker is running
echo "Checking Docker..."
docker info > /dev/null 2>&1 || {
    echo "ERROR: Docker is not running"
    exit 1
}
echo "OK"
echo ""

# Check Docker Compose
echo "Checking Docker Compose..."
docker compose version > /dev/null 2>&1 || {
    echo "ERROR: Docker Compose is not available"
    exit 1
}
echo "OK"
echo ""

# Check services are running
echo "Checking services are running..."
for service in postgres opensearch redis backend celery-worker frontend; do
    if ! docker compose ps --status running | grep -q "$service"; then
        echo "ERROR: Service $service is not running"
        echo "Run 'docker compose up -d' first"
        exit 1
    fi
done
echo "OK"
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
docker compose exec -T postgres pg_isready -U whedifaqaui -d whedifaqaui || {
    echo "ERROR: PostgreSQL is not ready"
    exit 1
}
echo "OK"
echo ""

# Check OpenSearch
echo "Checking OpenSearch..."
curl -s http://localhost:9200/_cluster/health | grep -E '"status":"(green|yellow)"' > /dev/null || {
    echo "ERROR: OpenSearch cluster is not healthy"
    exit 1
}
echo "OK"
echo ""

# Check Redis
echo "Checking Redis..."
docker compose exec -T redis redis-cli ping | grep -q "PONG" || {
    echo "ERROR: Redis is not responding"
    exit 1
}
echo "OK"
echo ""

# Check Backend health endpoint
echo "Checking Backend health endpoint..."
curl -s http://localhost:8000/api/health | grep -q '"status"' || {
    echo "ERROR: Backend health endpoint not responding"
    exit 1
}
echo "OK"
echo ""

# Check Frontend
echo "Checking Frontend..."
curl -s http://localhost:3000 | grep -q "Whedifaqaui" || {
    echo "ERROR: Frontend is not responding"
    exit 1
}
echo "OK"
echo ""

# Check FFmpeg in worker
echo "Checking FFmpeg in worker..."
docker compose exec -T celery-worker ffmpeg -version > /dev/null 2>&1 || {
    echo "ERROR: FFmpeg is not available in worker"
    exit 1
}
echo "OK"
echo ""

# Check data directories
echo "Checking data directories..."
for dir in data/videos/original data/videos/processed data/videos/audio data/videos/thumbnails data/videos/screenshots data/transcripts data/temp data/models; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Directory $dir does not exist"
        exit 1
    fi
done
echo "OK"
echo ""

# Check volume write access from container
echo "Checking volume write access..."
docker compose exec -T backend python -c "
from pathlib import Path
test_file = Path('/data/temp/write_test.txt')
test_file.write_text('test')
assert test_file.read_text() == 'test', 'Read back failed'
test_file.unlink()
print('Write/read/delete OK')
" || {
    echo "ERROR: Container cannot write to /data volume"
    exit 1
}
echo ""

# Check Celery task execution
echo "Checking Celery task execution..."
docker compose exec -T backend python -c "
from app.tasks.celery_app import celery_app
result = celery_app.send_task('tasks.ping')
response = result.get(timeout=10)
assert response == 'pong', f'Unexpected response: {response}'
print('Celery ping OK')
" || {
    echo "ERROR: Celery task execution failed"
    exit 1
}
echo ""

# Check Alembic configuration
echo "Checking Alembic..."
docker compose exec -T backend alembic current || {
    echo "ERROR: Alembic not configured correctly"
    exit 1
}
echo "OK"
echo ""

# Check database query execution
echo "Checking database query execution..."
docker compose exec -T backend python -c "
from sqlalchemy import text
from app.core.database import SessionLocal
db = SessionLocal()
result = db.execute(text('SELECT current_database(), current_user'))
row = result.fetchone()
assert row[0] == 'whedifaqaui', f'Wrong database: {row[0]}'
print(f'Connected to {row[0]} as {row[1]}')
db.close()
" || {
    echo "ERROR: Database query execution failed"
    exit 1
}
echo ""

# Check OpenSearch index operations
echo "Checking OpenSearch write capability..."
docker compose exec -T backend python -c "
from app.core.opensearch import get_opensearch_client
client = get_opensearch_client()
client.indices.create('test-phase0', body={})
client.indices.delete('test-phase0')
print('Index create/delete OK')
" || {
    echo "ERROR: OpenSearch index operations failed"
    exit 1
}
echo ""

# Check sentence-transformers import
echo "Checking sentence-transformers..."
docker compose exec -T celery-worker python -c "
from sentence_transformers import SentenceTransformer
print('Import OK')
" || {
    echo "ERROR: sentence-transformers not available"
    exit 1
}
echo ""

# Check WhisperX import
echo "Checking WhisperX..."
docker compose exec -T celery-worker python -c "
import whisperx
print('Import OK')
" || {
    echo "ERROR: WhisperX not available"
    exit 1
}
echo ""

# Check frontend API proxy (warning only - may not work in all setups)
echo "Checking frontend API proxy..."
docker compose exec -T frontend wget -q -O - http://localhost:3000/api/health 2>/dev/null | grep -q '"status"' || {
    echo "WARNING: Frontend proxy to backend may not be working (expected in production build)"
}
echo "OK"
echo ""

# Check type checking (warning only)
echo "Checking mypy..."
docker compose exec -T backend mypy app --ignore-missing-imports || {
    echo "WARNING: Type errors found (non-blocking)"
}
echo ""

echo "=== All checks passed ==="
echo ""
echo "Environment is ready for development!"
echo ""
echo "Useful commands:"
echo "  make logs           - View all service logs"
echo "  make shell-backend  - Open shell in backend container"
echo "  make test           - Run all tests"
echo "  make lint           - Run linters"
