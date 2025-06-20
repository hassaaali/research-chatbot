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
pip install PyPDF2 python-docx numpy sentence-transformers faiss-cpu
```

### 2. Wheel Building Errors
If you get wheel building errors:

```bash
# Upgrade build tools first
pip install --upgrade pip setuptools wheel

# Install packages one by one
pip install fastapi
pip install uvicorn[standard]
pip install sentence-transformers
```

### 3. PyTorch Installation Issues
For PyTorch compatibility:

```bash
# CPU version (recommended for most users)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Or use conda
conda install pytorch torchvision torchaudio cpuonly -c pytorch
```

### 4. FAISS Installation Issues
If FAISS fails to install:

```bash
# Try conda instead
conda install -c conda-forge faiss-cpu

# Or use alternative
pip install faiss-cpu==1.7.4 --no-cache-dir
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

### Method 1: Conda Environment
```bash
# Create conda environment
conda create -n rag-backend python=3.11
conda activate rag-backend

# Install packages via conda
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

### Method 3: Minimal Setup
For basic functionality only:

```bash
pip install fastapi uvicorn python-multipart python-dotenv
pip install PyPDF2 requests sqlalchemy loguru
```

## Running Without Advanced Features

If you can't install all dependencies, you can run with limited features:

1. **Without Hugging Face models**: Set `TEXT_GENERATION_MODEL=""` in .env
2. **Without web search**: Set `ENABLE_WEB_SEARCH=False` in .env
3. **Without spaCy**: The system will work with basic text processing

## Getting Help

If you continue to have issues:

1. Check Python version: `python --version`
2. Check pip version: `pip --version`
3. Try creating a fresh virtual environment
4. Consider using Python 3.11 instead of 3.12
5. Check the logs in `logs/app.log` for detailed error messages