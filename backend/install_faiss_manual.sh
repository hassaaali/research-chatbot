#!/bin/bash

echo "🔧 Manual FAISS Installation Script"
echo "===================================="

# Detect operating system
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "📍 Detected OS: ${MACHINE}"

# Install SWIG (required for FAISS compilation)
echo "🔧 Installing SWIG..."

if [[ "$MACHINE" == "Mac" ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        echo "📦 Installing SWIG via Homebrew..."
        brew install swig
    else
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
elif [[ "$MACHINE" == "Linux" ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        echo "📦 Installing SWIG via apt..."
        sudo apt-get update
        sudo apt-get install -y swig libopenblas-dev
    elif command -v yum &> /dev/null; then
        echo "📦 Installing SWIG via yum..."
        sudo yum install -y swig openblas-devel
    elif command -v dnf &> /dev/null; then
        echo "📦 Installing SWIG via dnf..."
        sudo dnf install -y swig openblas-devel
    else
        echo "❌ Package manager not found. Please install SWIG manually."
        exit 1
    fi
else
    echo "❌ Unsupported operating system: ${MACHINE}"
    echo "Please install SWIG manually and then run:"
    echo "   pip install faiss-cpu"
    exit 1
fi

# Verify SWIG installation
if command -v swig &> /dev/null; then
    echo "✅ SWIG installed successfully"
    swig -version
else
    echo "❌ SWIG installation failed"
    exit 1
fi

# Install FAISS
echo "🔍 Installing FAISS..."
pip install faiss-cpu --no-cache-dir

# Verify FAISS installation
echo "🧪 Testing FAISS installation..."
python -c "import faiss; print('✅ FAISS installed successfully')" || echo "❌ FAISS installation failed"

echo "✅ Manual FAISS installation completed!"