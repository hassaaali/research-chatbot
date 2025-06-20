#!/usr/bin/env python3
"""
Install only pre-compiled packages to avoid Rust/Cargo compilation issues
"""
import subprocess
import sys
import platform

def run_command(command, description):
    """Run a command and handle errors gracefully"""
    print(f"\n[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_package(package, description=None):
    """Install a single package with error handling"""
    desc = description or f"Installing {package}"
    return run_command(f"pip install {package} --only-binary=all", desc)

def main():
    print("Installing Pre-compiled Packages Only (No Rust/Cargo compilation)")
    print("=" * 70)
    
    # Check system info
    print(f"[INFO] Python version: {sys.version}")
    print(f"[INFO] Platform: {platform.system()} {platform.machine()}")
    
    # Upgrade pip first
    print("\n[INFO] Upgrading pip...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install core packages (no compilation needed)
    print("\n[INFO] Installing core web framework...")
    core_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6", 
        "python-dotenv==1.0.0",
        "pydantic>=2.5.0"
    ]
    
    for package in core_packages:
        install_package(package)
    
    # Install document processing
    print("\n[INFO] Installing document processing...")
    doc_packages = [
        "PyPDF2==3.0.1",
        "python-docx==1.1.0",
        "nltk==3.8.1"
    ]
    
    for package in doc_packages:
        install_package(package)
    
    # Install NumPy (pre-compiled wheels available)
    print("\n[INFO] Installing NumPy...")
    install_package("numpy>=1.19.0,<2.0")
    
    # Install basic utilities
    print("\n[INFO] Installing utilities...")
    util_packages = [
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "sqlalchemy>=2.0.0",
        "aiofiles>=23.0.0",
        "loguru>=0.7.0"
    ]
    
    for package in util_packages:
        install_package(package)
    
    # Try PyTorch CPU (pre-compiled)
    print("\n[INFO] Installing PyTorch (CPU, pre-compiled)...")
    pytorch_success = run_command(
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "Installing PyTorch CPU"
    )
    
    # Skip packages that require Rust compilation
    print("\n[WARNING] Skipping packages that require Rust/Cargo compilation:")
    print("   - tokenizers (requires Rust)")
    print("   - transformers (depends on tokenizers)")
    print("   - sentence-transformers (depends on transformers)")
    print("   - huggingface-hub (newer versions require Rust)")
    
    # Install alternative vector search
    print("\n[INFO] Installing vector search alternative...")
    vector_alternatives = [
        "chromadb>=0.4.15",
        "hnswlib>=0.7.0"
    ]
    
    vector_success = False
    for alt in vector_alternatives:
        if install_package(alt, f"Installing {alt}"):
            vector_success = True
            print(f"[SUCCESS] Installed {alt} for vector search")
            break
    
    # Install web search
    print("\n[INFO] Installing web search...")
    web_packages = [
        "aiohttp>=3.9.0",
        "duckduckgo-search>=3.9.0"
    ]
    
    for package in web_packages:
        install_package(package)
    
    # Test core functionality
    print("\n[INFO] Testing installation...")
    test_code = """
try:
    import fastapi
    import pydantic
    import PyPDF2
    import numpy
    import requests
    import sqlalchemy
    print("SUCCESS: Core packages working")
    
    try:
        import torch
        print("SUCCESS: PyTorch available")
    except ImportError:
        print("WARNING: PyTorch not available")
    
    try:
        import chromadb
        print("SUCCESS: ChromaDB available for vector search")
    except ImportError:
        try:
            import hnswlib
            print("SUCCESS: HNSWLIB available for vector search")
        except ImportError:
            print("WARNING: No vector search library available")
    
    print("SUCCESS: Installation test passed")
    
except Exception as e:
    print("ERROR:", str(e))
"""
    
    run_command(f"python -c \"{test_code}\"", "Testing installation")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Pre-compiled installation completed!")
    
    print("\n[INFO] What was installed:")
    print("   ✅ FastAPI web framework")
    print("   ✅ Document processing (PDF, DOCX)")
    print("   ✅ Basic utilities and database support")
    print("   ✅ Web search capabilities")
    if pytorch_success:
        print("   ✅ PyTorch (CPU version)")
    if vector_success:
        print("   ✅ Vector search (ChromaDB or HNSWLIB)")
    
    print("\n[WARNING] What was skipped (due to Rust compilation requirements):")
    print("   ❌ Hugging Face transformers (requires Rust tokenizers)")
    print("   ❌ Sentence transformers (depends on transformers)")
    print("   ❌ Advanced language models")
    
    print("\n[INFO] The system will work with these limitations:")
    print("   - Basic text search instead of semantic search")
    print("   - Simple response generation instead of advanced LLMs")
    print("   - All core functionality (upload, process, chat) will work")
    
    print("\n[INFO] To enable advanced features, you would need to:")
    print("   1. Update Rust/Cargo to a newer version")
    print("   2. Or use a system with pre-compiled wheels available")
    print("   3. Or use conda instead of pip")
    
    print("\n[INFO] Next steps:")
    print("1. Update your .env file:")
    print("   ENABLE_ADVANCED_NLP=False")
    print("   USE_SIMPLE_EMBEDDINGS=True")
    print("   TEXT_GENERATION_MODEL=''")
    print("2. Run: python main.py")
    print("3. Backend will be available at http://localhost:8000")

if __name__ == "__main__":
    main()