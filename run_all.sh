#!/bin/bash

# Script to run both the RAG backend and Streamlit frontend

echo "🚀 Starting RAG Backend and Streamlit Frontend..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend in background
echo -e "${BLUE}Starting FastAPI backend on port 8080...${NC}"
cd "$SCRIPT_DIR"
python setup.py run --debug &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"

# Wait a bit for backend to start
sleep 3

# Start Streamlit frontend
echo -e "${BLUE}Starting Streamlit frontend on port 8501...${NC}"
streamlit run streamlit_app.py --logger.level=info

# Cleanup: Kill backend when Streamlit exits
kill $BACKEND_PID 2>/dev/null
echo -e "${GREEN}Services stopped${NC}"
