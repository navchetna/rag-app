#!/bin/bash
# Quick Start Script for RAG Backend

set -e

echo "🚀 RAG Backend - Quick Start"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Setup environment
echo ""
echo "📦 Setting up environment..."
python3 setup.py setup

# Instructions
echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   - Set GROQ_API_KEY"
echo "   - Verify microservice endpoints match your setup"
echo ""
echo "2. Start the server:"
echo "   python setup.py run          # Production mode"
echo "   python setup.py run --debug  # Development mode"
echo ""
echo "3. API will be available at: http://localhost:8080"
echo ""
echo "4. View API documentation at: http://localhost:8080/docs"
echo ""
echo "Microservices that should be running:"
echo "  - PDF Parser:  http://localhost:8000"
echo "  - DataPrep:    http://localhost:5000"
echo "  - Retriever:   http://localhost:7000"
echo "  - Qdrant DB:   http://localhost:6333"
echo ""
