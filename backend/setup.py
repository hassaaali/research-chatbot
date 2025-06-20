#!/usr/bin/env python3
"""
Setup script for Research Paper RAG Backend
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

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

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"📍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    
    if version.major == 3 and version.minor >= 12:
        print("⚠️  Python 3.12 detected - some packages may have compatibility issues")
    
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        if run_command("python3 -m venv venv", "Creating virtual environment"):
            print("✅ Virtual environment created")
        else:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("📦 Virtual environment already exists")
    
    return True

def activate_virtual_environment():
    """Instructions for activating virtual environment"""
    print("\n🔄 To activate virtual environment, run:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

def upgrade_pip():
    """Upgrade pip"""
    print("\n📦 Upgrading pip...")
    return run_command("pip install --upgrade pip", "Upgrading pip")

def install_dependencies():
    """Install dependencies using different methods"""
    print("\n🔧 Installing dependencies...")
    
    # Method 1: Try the custom installer
    if Path("install_requirements.py").exists():
        print("🚀 Using custom installer...")
        if run_command("python install_requirements.py", "Running custom installer"):
            print("✅ Installation completed successfully!")
            return True
    
    print("⚠️  Custom installer not available or failed, trying minimal requirements...")
    
    # Method 2: Try minimal requirements
    if Path("requirements-minimal.txt").exists():
        if run_command("pip install -r requirements-minimal.txt", "Installing minimal requirements"):
            print("✅ Minimal installation completed!")
            print("⚠️  Some advanced features may not be available")
            return True
    
    # Method 3: Install core packages manually
    print("❌ Automated installation failed. Installing core packages manually...")
    core_packages = [
        "fastapi",
        "uvicorn",
        "python-multipart",
        "python-dotenv",
        "pydantic"
    ]
    
    success = True
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            success = False
    
    return success

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data/vectors",
        "data/documents", 
        "data/faiss_index",
        "uploads",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment_file():
    """Copy environment file if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n📝 Creating environment file...")
        shutil.copy(env_example, env_file)
        print("✅ Environment file created")
        print("✏️  Please edit .env file with your configuration")
    elif env_file.exists():
        print("\n📝 Environment file already exists")
    else:
        print("\n⚠️  No .env.example file found")

def main():
    """Main setup function"""
    print("🚀 Setting up Research Paper RAG Backend")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Setup failed at virtual environment creation")
        sys.exit(1)
    
    # Show activation instructions
    activate_virtual_environment()
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
        
        # Upgrade pip
        upgrade_pip()
        
        # Install dependencies
        if not install_dependencies():
            print("⚠️  Some dependencies failed to install")
    else:
        print("⚠️  Virtual environment not activated. Please activate it and run:")
        print("   python setup.py")
        print("   or")
        print("   pip install -r requirements.txt")
    
    # Create directories
    create_directories()
    
    # Setup environment file
    setup_environment_file()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment (if not already active)")
    print("2. Edit .env file with your settings")
    print("3. Run: python main.py")
    print("4. Backend will be available at http://localhost:8000")
    print("\n🔍 If you encounter issues, check troubleshoot.md")

if __name__ == "__main__":
    main()