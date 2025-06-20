# Troubleshooting Installation Issues

## Common Python 3.12 Issues

### 1. pkgutil.ImpImporter Error
This is a known issue with Python 3.12 and older packages.

**Solutions:**
```bash
# Option 1: Use the custom installer
python install_requirements.py

# Option 2: Install minimal requirements
pip install -r requirements-minimal.txt

# Option 3: Manual installation
pip install fastapi uvicorn python-multipart python-dotenv pydantic
pip install PyPDF2 python-docx numpy sentence-transformers
```

### 2. FAISS Installation Issues (SWIG Error)
FAISS requires SWIG to build from source. Here are solutions:

**Option 1: Install SWIG first**
```bash
# macOS
brew install swig

# Ubuntu/Debian
sudo apt-get install swig libopenblas-dev

# CentOS/RHEL
sudo yum install swig openblas-devel

# Then install FAISS
pip install faiss-cpu --no-cache-dir
```

**Option 2: Use conda instead**
```bash
conda install -c conda-forge faiss-cpu
```

**Option 3: Use alternative vector search**
```bash
# Install ChromaDB instead
pip install chromadb

# Or HNSWLIB
pip install hnswlib

# Or Annoy
pip install annoy
```

**Option 4: Use requirements without FAISS**
```bash
pip install -r requirements-no-faiss.txt
```

**Option 5: Run the manual FAISS installer**
```bash
chmod +x install_faiss_manual.sh
./install_faiss_manual.sh
```

### 3. PyTorch Installation Issues
For PyTorch compatibility:

```bash
# CPU version (recommended for most users) - Latest available version
pip install torch>=2.2.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Alternative: Let pip choose the version
pip install torch torchvision torchaudio

# Or use conda
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

### 4. Wheel Building Errors
If you get wheel building errors:

```bash
# Upgrade build tools first
pip install --upgrade pip setuptools wheel

# Install packages one by one
pip install fastapi
pip install uvicorn[standard]
pip install sentence-transformers
```

### 5. spaCy Model Download
If spaCy model download fails:

```bash
# Download manually
python -m spacy download en_core_web_sm

# Or use alternative
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

## Alternative Installation Methods

### Method 1: Conda Environment (Recommended for FAISS issues)
```bash
# Create conda environment
conda create -n rag-backend python=3.11
conda activate rag-backend

# Install packages via conda (avoids compilation issues)
conda install -c conda-forge fastapi uvicorn
conda install -c conda-forge pytorch torchvision torchaudio cpuonly
conda install -c conda-forge faiss-cpu
conda install -c huggingface transformers sentence-transformers

# Install remaining via pip
pip install python-multipart python-dotenv PyPDF2 python-docx
```

### Method 2: Docker
```bash
# Use the provided Dockerfile
docker build -t rag-backend .
docker run -p 8000:8000 rag-backend
```

### Method 3: Minimal Setup (No Vector Search)
For basic functionality only:

```bash
pip install fastapi uvicorn python-multipart python-dotenv
pip install PyPDF2 requests sqlalchemy loguru
```

### Method 4: Step-by-step Installation
```bash
# Install in this exact order to avoid conflicts:

# 1. Core packages
pip install fastapi uvicorn python-multipart python-dotenv pydantic

# 2. NumPy (compatible version)
pip install "numpy>=1.19.0,<2.0"

# 3. PyTorch (CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. ML packages
pip install scikit-learn sentence-transformers transformers

# 5. Vector search (try alternatives if FAISS fails)
pip install faiss-cpu || pip install chromadb || pip install hnswlib

# 6. Document processing
pip install PyPDF2 python-docx nltk spacy

# 7. Utilities
pip install requests beautifulsoup4 sqlalchemy loguru aiofiles
```

## Running Without Advanced Features

If you can't install all dependencies, you can run with limited features:

1. **Without FAISS**: The system will use alternative vector search or basic text search
2. **Without Hugging Face models**: Set `TEXT_GENERATION_MODEL=""` in .env
3. **Without web search**: Set `ENABLE_WEB_SEARCH=False` in .env
4. **Without spaCy**: The system will work with basic text processing
5. **Without PyTorch**: Some advanced features will be disabled

## System-Specific Solutions

### macOS
```bash
# Install Xcode command line tools
xcode-select --install

# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install swig openblas

# Then install Python packages
pip install faiss-cpu
```

### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y build-essential swig libopenblas-dev python3-dev

# Then install Python packages
pip install faiss-cpu
```

### Windows
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Install SWIG
# Download from: http://www.swig.org/download.html
# Add to PATH

# Then install Python packages
pip install faiss-cpu
```

## Getting Help

If you continue to have issues:

1. Check Python version: `python --version`
2. Check pip version: `pip --version`
3. Try creating a fresh virtual environment
4. Consider using Python 3.11 instead of 3.12
5. Check the logs in `logs/app.log` for detailed error messages
6. Try installing packages one by one to identify the problematic package

## Quick Fix Commands

```bash
# If FAISS fails, use this alternative setup:
pip install fastapi uvicorn python-multipart python-dotenv pydantic
pip install PyPDF2 python-docx requests beautifulsoup4 sqlalchemy loguru aiofiles
pip install numpy torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers transformers
pip install chromadb  # Alternative to FAISS

# Then run with vector search disabled in .env:
# VECTOR_STORE_TYPE=simple
```

## Environment Variables for Fallbacks

Add these to your `.env` file if certain packages fail:

```env
# Disable features for missing packages
ENABLE_VECTOR_SEARCH=False  # If FAISS/alternatives fail
ENABLE_WEB_SEARCH=False     # If web search packages fail
USE_SIMPLE_EMBEDDINGS=True  # If sentence-transformers fails
TEXT_GENERATION_MODEL=""    # If transformers/torch fails
```