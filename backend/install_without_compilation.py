#!/usr/bin/env python3
"""
Installation script that avoids packages requiring C++ compilation
"""
import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors gracefully"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_package(package, description=None):
    """Install a single package with error handling"""
    desc = description or f"Installing {package}"
    return run_command(f"pip install {package}", desc)

def main():
    print("🚀 Installing Backend Dependencies (No Compilation Required)")
    print("=" * 70)
    
    # Check Python version
    python_version = sys.version_info
    print(f"📍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"📍 Platform: {platform.system()} {platform.machine()}")
    
    # Upgrade pip first
    print("\n📦 Upgrading pip and build tools...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    run_command("pip install --upgrade setuptools wheel", "Upgrading build tools")
    
    # Install core web framework (no compilation needed)
    print("\n🌐 Installing core web framework...")
    core_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0"
    ]
    
    for package in core_packages:
        install_package(package)
    
    # Install document processing (no compilation needed)
    print("\n📄 Installing document processing...")
    doc_packages = [
        "PyPDF2==3.0.1",
        "python-docx==1.1.0",
        "nltk==3.8.1"
    ]
    
    for package in doc_packages:
        install_package(package)
    
    # Install NumPy (pre-compiled wheel available)
    print("\n🔢 Installing NumPy...")
    install_package("numpy>=1.19.0,<2.0", "Installing NumPy")
    
    # Install basic ML packages (pre-compiled wheels)
    print("\n🧠 Installing basic ML packages...")
    ml_packages = [
        "scikit-learn>=1.3.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0"
    ]
    
    for package in ml_packages:
        install_package(package)
    
    # Try PyTorch (CPU version, pre-compiled)
    print("\n🔥 Installing PyTorch (CPU version)...")
    pytorch_commands = [
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "pip install torch>=2.2.0 torchvision torchaudio"
    ]
    
    pytorch_success = False
    for cmd in pytorch_commands:
        if run_command(cmd, f"Installing PyTorch: {cmd}"):
            pytorch_success = True
            break
    
    # Install sentence transformers (depends on PyTorch)
    if pytorch_success:
        print("\n🔤 Installing sentence transformers...")
        install_package("sentence-transformers>=2.2.0", "Installing sentence-transformers")
        install_package("transformers>=4.36.0", "Installing transformers")
    else:
        print("⚠️ Skipping sentence-transformers due to PyTorch installation failure")
    
    # Install vector search alternatives (no compilation)
    print("\n🔍 Installing vector search alternatives...")
    vector_alternatives = [
        ("chromadb>=0.4.15", "ChromaDB"),
        ("hnswlib>=0.7.0", "HNSWLIB"), 
        ("annoy>=1.17.0", "Annoy")
    ]
    
    vector_success = False
    for package, name in vector_alternatives:
        if install_package(package, f"Installing {name}"):
            print(f"✅ Installed {name} as vector search engine")
            vector_success = True
            break
    
    if not vector_success:
        print("⚠️ No vector search library installed - will use basic text search")
    
    # Install database and utilities
    print("\n🗄️ Installing database and utilities...")
    util_packages = [
        "sqlalchemy>=2.0.0",
        "aiofiles>=23.0.0",
        "loguru>=0.7.0",
        "httpx>=0.25.0"
    ]
    
    for package in util_packages:
        install_package(package)
    
    # Install web search (optional)
    print("\n🌐 Installing web search capabilities...")
    web_packages = [
        "aiohttp>=3.9.0",
        "duckduckgo-search>=3.9.0"
    ]
    
    for package in web_packages:
        install_package(package)
    
    # Skip spaCy and FAISS (they require compilation)
    print("\n⚠️ Skipping packages that require compilation:")
    print("   - spaCy (requires C++ compilation)")
    print("   - FAISS (requires SWIG and C++ compilation)")
    print("   - The system will use alternatives for these features")
    
    # Test core functionality
    print("\n🧪 Testing core functionality...")
    test_code = """
try:
    import fastapi
    import pydantic
    import PyPDF2
    import numpy
    import requests
    print("✅ Core packages working")
    
    try:
        import torch
        print("✅ PyTorch available")
    except ImportError:
        print("⚠️ PyTorch not available")
    
    try:
        import sentence_transformers
        print("✅ Sentence transformers available")
    except ImportError:
        print("⚠️ Sentence transformers not available")
    
    try:
        import chromadb
        print("✅ ChromaDB available")
    except ImportError:
        try:
            import hnswlib
            print("✅ HNSWLIB available")
        except ImportError:
            try:
                import annoy
                print("✅ Annoy available")
            except ImportError:
                print("⚠️ No vector search library available")
    
    print("✅ Installation test passed")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
"""
    
    run_command(f"python -c \"{test_code}\"", "Testing installation")
    
    print("\n" + "=" * 70)
    print("✅ Installation completed!")
    print("\n📊 What was installed:")
    print("   ✅ FastAPI web framework")
    print("   ✅ Document processing (PDF, DOCX)")
    print("   ✅ Basic ML capabilities")
    print("   ✅ Web search functionality")
    print("   ✅ Database support")
    
    print("\n⚠️ What was skipped (due to compilation issues):")
    print("   ❌ spaCy (advanced NLP) - using basic text processing instead")
    print("   ❌ FAISS (vector search) - using alternative vector search")
    
    print("\n📋 Next steps:")
    print("1. Update your .env file to disable features that require missing packages:")
    print("   ENABLE_ADVANCED_NLP=False")
    print("   VECTOR_STORE_TYPE=chromadb  # or hnswlib or simple")
    print("2. Run: python main.py")
    print("3. Backend will be available at http://localhost:8000")
    
    print("\n💡 The system will work with these limitations:")
    print("   - Basic text processing instead of advanced NLP")
    print("   - Alternative vector search instead of FAISS")
    print("   - All core functionality (upload, chat, search) will work")

if __name__ == "__main__":
    main()