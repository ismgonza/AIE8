#!/bin/bash

echo "🚀 Starting Local Development Setup"
echo ""

# Start Qdrant in Docker
echo "📦 Starting Qdrant in Docker..."
docker-compose up -d

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to be ready..."
sleep 3

# Check if Qdrant is running
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is running at http://localhost:6333"
else
    echo "❌ Qdrant failed to start"
    exit 1
fi

echo ""
echo "✅ Qdrant started successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Run the app: ./run_app.sh"
echo "   2. Test it: ./test_system.sh"
echo ""
echo "📌 Qdrant Web UI: http://localhost:6333/dashboard"
echo "🛑 To stop: docker-compose down"

