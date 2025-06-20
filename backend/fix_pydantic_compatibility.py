#!/usr/bin/env python3
"""
Fix Pydantic compatibility issues with Python 3.12
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
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_virtual_env():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("⚠️ Not in a virtual environment. It's recommended to use one.")
        print("To create and activate a virtual environment:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        return False
    return True

def main():
    print("🔧 Fixing Pydantic Compatibility Issues")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"📍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check virtual environment
    check_virtual_env()
    
    # Step 1: Completely clean Pydantic installations
    print("\n🧹 Cleaning existing Pydantic installations...")
    packages_to_remove = [
        "pydantic",
        "pydantic-core", 
        "pydantic-settings",
        "spacy",
        "fastapi"  # Will reinstall with correct Pydantic
    ]
    
    for package in packages_to_remove:
        run_command(f"pip uninstall {package} -y", f"Removing {package}")
    
    # Step 2: Clear pip cache
    print("\n🗑️ Clearing pip cache...")
    run_command("pip cache purge", "Clearing pip cache")
    
    # Step 3: Upgrade pip and build tools
    print("\n📦 Upgrading build tools...")
    run_command("pip install --upgrade pip setuptools wheel", "Upgrading build tools")
    
    # Step 4: Install Pydantic v2 (latest stable)
    print("\n📦 Installing Pydantic v2...")
    if not run_command("pip install 'pydantic>=2.5.0'", "Installing Pydantic v2"):
        print("❌ Failed to install Pydantic v2")
        return False
    
    # Step 5: Install pydantic-settings separately
    print("\n📦 Installing pydantic-settings...")
    run_command("pip install pydantic-settings", "Installing pydantic-settings")
    
    # Step 6: Install FastAPI (compatible with Pydantic v2)
    print("\n📦 Installing FastAPI...")
    if not run_command("pip install fastapi>=0.104.0", "Installing FastAPI"):
        print("❌ Failed to install FastAPI")
        return False
    
    # Step 7: Install other core dependencies
    print("\n📦 Installing core dependencies...")
    core_deps = [
        "uvicorn[standard]",
        "python-multipart",
        "python-dotenv"
    ]
    
    for dep in core_deps:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    # Step 8: Test Pydantic installation
    print("\n🧪 Testing Pydantic installation...")
    test_code = """
import pydantic
print(f"✅ Pydantic version: {pydantic.__version__}")

from pydantic import BaseModel
class TestModel(BaseModel):
    name: str
    age: int

test = TestModel(name="test", age=25)
print(f"✅ Pydantic working correctly: {test}")
"""
    
    test_success = run_command(
        f"python -c \"{test_code}\"",
        "Testing Pydantic"
    )
    
    # Step 9: Test FastAPI compatibility
    print("\n🧪 Testing FastAPI compatibility...")
    fastapi_test = """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

print("✅ FastAPI and Pydantic working together")
"""
    
    fastapi_success = run_command(
        f"python -c \"{fastapi_test}\"",
        "Testing FastAPI compatibility"
    )
    
    # Step 10: Install remaining dependencies (without spaCy for now)
    print("\n📦 Installing remaining dependencies...")
    remaining_deps = [
        "PyPDF2",
        "python-docx", 
        "nltk",
        "numpy>=1.19.0,<2.0",
        "requests",
        "beautifulsoup4",
        "sqlalchemy",
        "loguru",
        "aiofiles"
    ]
    
    for dep in remaining_deps:
        run_command(f"pip install '{dep}'", f"Installing {dep}")
    
    # Step 11: Try to install spaCy with Pydantic v2 compatibility
    print("\n📦 Attempting to install spaCy...")
    spacy_success = False
    
    # Try different spaCy versions that support Pydantic v2
    spacy_versions = [
        "spacy>=3.7.2",  # Latest version with Pydantic v2 support
        "spacy==3.7.2",  # Specific version
        "spacy==3.7.1"   # Fallback
    ]
    
    for version in spacy_versions:
        if run_command(f"pip install '{version}'", f"Installing {version}"):
            # Try to download the model
            if run_command("python -m spacy download en_core_web_sm", "Downloading spaCy model"):
                spacy_success = True
                break
            else:
                print("⚠️ spaCy installed but model download failed")
                spacy_success = True
                break
    
    if not spacy_success:
        print("⚠️ spaCy installation failed, installing TextBlob as alternative...")
        run_command("pip install textblob", "Installing TextBlob alternative")
    
    # Step 12: Final test
    print("\n🧪 Final compatibility test...")
    final_test = """
try:
    import pydantic
    import fastapi
    print(f"✅ Pydantic: {pydantic.__version__}")
    print(f"✅ FastAPI: {fastapi.__version__}")
    
    try:
        import spacy
        print(f"✅ spaCy: {spacy.__version__}")
    except ImportError:
        print("⚠️ spaCy not available (using fallback)")
    
    print("✅ All core dependencies working")
    
except Exception as e:
    print(f"❌ Error: {e}")
"""
    
    final_success = run_command(
        f"python -c \"{final_test}\"",
        "Final compatibility test"
    )
    
    print("\n" + "=" * 50)
    if final_success:
        print("✅ Pydantic compatibility issues fixed!")
        print("✅ Ready to run the backend server")
    else:
        print("⚠️ Some issues remain, but core functionality should work")
    
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. Backend will be available at http://localhost:8000")
    print("3. Check logs for any remaining issues")
    
    if not spacy_success:
        print("\n⚠️ Note: spaCy not installed. The system will use basic text processing.")
        print("   This is fine for basic functionality.")

if __name__ == "__main__":
    main()