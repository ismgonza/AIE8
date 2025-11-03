#!/bin/bash

# Load environment variables from root .env file
if [ -f "../.env" ]; then
    echo "📝 Loading environment variables from root .env..."
    set -a
    source ../.env
    set +a
elif [ -f ".env" ]; then
    echo "📝 Loading environment variables from app/.env..."
    set -a
    source .env
    set +a
else
    echo "⚠️  No .env file found in root or app/ directory"
    echo "   Make sure OPENAI_API_KEY and other variables are set"
fi

# Set Qdrant connection for local development
export QDRANT_HOST=localhost
export QDRANT_PORT=6333

# Check if Qdrant is running
if ! curl -s http://localhost:6333/health > /dev/null; then
    echo "❌ Qdrant is not running!"
    echo "   Start it with: ./start_qdrant.sh"
    exit 1
fi

echo "✅ Qdrant is running"

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
    echo "✓ Port 8000 freed"
fi

echo "🚀 Starting FastAPI app locally..."
echo ""

# Start the app from the parent directory (so imports work)
cd ..
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

