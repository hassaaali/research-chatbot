#!/bin/bash

echo "🚀 Setting up Research Paper RAG Backend"
echo "========================================"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
echo "📍 Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Try different installation approaches
echo "🔧 Installing dependencies..."

# Method 1: Try the custom installer
if python install_requirements.py; then
    echo "✅ Installation completed successfully!"
else
    echo "⚠️  Custom installer failed, trying minimal requirements..."
    
    # Method 2: Try minimal requirements
    if pip install -r requirements-minimal.txt; then
        echo "✅ Minimal installation completed!"
        echo "⚠️  Some advanced features may not be available"
    else
        echo "❌ Installation failed. Please install manually:"
        echo "pip install fastapi uvicorn python-multipart python-dotenv"
    fi
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/vectors data/documents data/faiss_index uploads logs

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your configuration"
fi

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Run: python main.py"
echo "3. Backend will be available at http://localhost:8000"