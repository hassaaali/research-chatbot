#!/usr/bin/env python3
"""
Specific script to fix spaCy installation issues with Python 3.12
"""
import subprocess
import sys

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

def main():
    print("🔧 Fixing spaCy Installation for Python 3.12")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"📍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Step 1: Uninstall conflicting packages
    print("\n🗑️ Removing conflicting packages...")
    packages_to_remove = ["spacy", "pydantic", "pydantic-core"]
    for package in packages_to_remove:
        run_command(f"pip uninstall {package} -y", f"Removing {package}")
    
    # Step 2: Install compatible Pydantic version
    print("\n📦 Installing compatible Pydantic...")
    if not run_command("pip install 'pydantic>=1.10.0,<2.0.0'", "Installing Pydantic v1"):
        print("❌ Failed to install compatible Pydantic")
        return False
    
    # Step 3: Install spaCy with compatible version
    print("\n📦 Installing spaCy...")
    spacy_versions = [
        "spacy==3.6.1",  # Older, more stable version
        "spacy==3.7.0",  # Try specific version
        "spacy>=3.6.0,<3.7.0"  # Range that should work
    ]
    
    spacy_installed = False
    for version in spacy_versions:
        if run_command(f"pip install {version}", f"Installing {version}"):
            spacy_installed = True
            break
    
    if not spacy_installed:
        print("❌ All spaCy versions failed to install")
        print("💡 Trying alternative approach...")
        
        # Alternative: Install without spaCy
        print("📦 Installing basic NLP alternative...")
        if run_command("pip install textblob", "Installing TextBlob as alternative"):
            print("✅ Installed TextBlob as spaCy alternative")
        
        return False
    
    # Step 4: Download spaCy model
    print("\n📥 Downloading spaCy English model...")
    model_commands = [
        "python -m spacy download en_core_web_sm",
        "pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0-py3-none-any.whl"
    ]
    
    model_installed = False
    for cmd in model_commands:
        if run_command(cmd, f"Downloading model: {cmd}"):
            model_installed = True
            break
    
    # Step 5: Test installation
    print("\n🧪 Testing spaCy installation...")
    test_success = run_command(
        "python -c \"import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ spaCy working correctly')\"",
        "Testing spaCy"
    )
    
    print("\n" + "=" * 50)
    if test_success:
        print("✅ spaCy installation fixed successfully!")
    else:
        print("⚠️ spaCy installation completed but may have issues")
        print("💡 The system can still work with basic text processing")
    
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. If spaCy still has issues, the system will use fallback text processing")

if __name__ == "__main__":
    main()