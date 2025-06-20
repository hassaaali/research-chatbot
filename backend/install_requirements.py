#!/usr/bin/env python3
"""
Installation script for Python dependencies with fallback options
"""
import subprocess
import sys
import os

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
    print("🚀 Installing Research Paper RAG Backend Dependencies")
    print("=" * 60)
    
    # Upgrade pip first
    print("\n📦 Upgrading pip...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install setuptools and wheel first
    print("\n🔧 Installing build tools...")
    install_package("setuptools>=65.0.0", "Installing setuptools")
    install_package("wheel", "Installing wheel")
    
    # Core dependencies first
    core_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0"
    ]
    
    print("\n📋 Installing core FastAPI dependencies...")
    for package in core_packages:
        install_package(package)
    
    # Document processing
    doc_packages = [
        "PyPDF2==3.0.1",
        "python-docx==1.1.0",
        "nltk==3.8.1"
    ]
    
    print("\n📄 Installing document processing dependencies...")
    for package in doc_packages:
        install_package(package)
    
    # Install numpy first with compatible version
    print("\n🔢 Installing NumPy with compatible version...")
    install_package("'numpy>=1.19.0,<2.0'", "Installing NumPy")
    
    # Install PyTorch (CPU version for compatibility) - Updated version
    print("\n🔥 Installing PyTorch...")
    torch_success = False
    
    # Try different PyTorch installation methods
    torch_commands = [
        "pip install torch>=2.2.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        "pip install torch torchvision torchaudio"
    ]
    
    for cmd in torch_commands:
        if run_command(cmd, "Installing PyTorch"):
            torch_success = True
            break
    
    if not torch_success:
        print("⚠️ PyTorch installation failed, continuing with other packages...")
    
    # Install other ML packages
    ml_packages = [
        "scikit-learn==1.3.2",
        "sentence-transformers==2.2.2",
        "transformers==4.36.2",
        "accelerate==0.25.0",
        "faiss-cpu==1.7.4"
    ]
    
    print("\n🧠 Installing ML dependencies...")
    for package in ml_packages:
        install_package(package)
    
    # Try to install spaCy
    print("\n🔤 Installing spaCy...")
    if install_package("spacy==3.7.2"):
        print("📥 Downloading spaCy English model...")
        run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model")
    
    # Web and utility dependencies
    util_packages = [
        "requests==2.31.0",
        "aiohttp==3.9.1",
        "beautifulsoup4==4.12.2",
        "duckduckgo-search==3.9.6",
        "sqlalchemy==2.0.23",
        "httpx==0.25.2",
        "aiofiles==23.2.1",
        "loguru==0.7.2"
    ]
    
    print("\n🌐 Installing web and utility dependencies...")
    for package in util_packages:
        install_package(package)
    
    # Optional packages
    optional_packages = [
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4"
    ]
    
    print("\n🔐 Installing optional security packages...")
    for package in optional_packages:
        install_package(package)
    
    print("\n✅ Installation completed!")
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. The backend will be available at http://localhost:8000")
    print("3. Check the logs for any remaining issues")
    
    if not torch_success:
        print("\n⚠️ PyTorch installation failed. You can try installing it manually:")
        print("   pip install torch torchvision torchaudio")
        print("   or visit: https://pytorch.org/get-started/locally/")

if __name__ == "__main__":
    main()