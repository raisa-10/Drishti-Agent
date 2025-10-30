#!/bin/bash

# Drishti Streamlit UI Startup Script
# This script sets up and runs the Streamlit application

echo "🛡️ Starting Drishti Command Center UI..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Using default configuration."
    echo "You may want to create a .env file with your custom settings."
fi

# Get backend URL from user if needed
if [ -z "$BACKEND_URL" ]; then
    echo "🔗 Please specify the backend URL (default: http://localhost:8000):"
    read -r backend_url
    if [ -n "$backend_url" ]; then
        export BACKEND_URL="$backend_url"
        export API_BASE_URL="$backend_url/api/v1"
    fi
fi

# Set default port if not specified
if [ -z "$STREAMLIT_PORT" ]; then
    export STREAMLIT_PORT=8501
fi

echo "🚀 Starting Streamlit application on port $STREAMLIT_PORT..."
echo "📱 You can access the UI at: http://localhost:$STREAMLIT_PORT"
echo "🔗 Backend API: ${BACKEND_URL:-http://localhost:8000}"
echo ""
echo "🛑 Press Ctrl+C to stop the application"
echo ""

# Run Streamlit
streamlit run app.py --server.port=$STREAMLIT_PORT --server.address=0.0.0.0
