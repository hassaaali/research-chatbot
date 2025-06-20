#!/usr/bin/env python3
"""
Install compatible versions that work together
"""
import subprocess
import sys

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

def main():
    print("Installing Compatible Versions")
    print("=" * 40)
    
    # Step 1: Uninstall problematic packages
    print("\n[INFO] Removing problematic packages...")
    packages_to_remove = [
        "sentence-transformers",
        "transformers", 
        "huggingface-hub",
        "tokenizers",
        "datasets"
    ]
    
    for package in packages_to_remove:
        run_command(f"pip uninstall {package} -y", f"Removing {package}")
    
    # Step 2: Install compatible huggingface-hub first
    print("\n[INFO] Installing compatible huggingface-hub...")
    if not run_command("pip install 'huggingface-hub>=0.16.0,<0.20.0'", "Installing huggingface-hub"):
        print("[ERROR] Failed to install compatible huggingface-hub")
        return False
    
    # Step 3: Install tokenizers
    print("\n[INFO] Installing tokenizers...")
    run_command("pip install 'tokenizers>=0.13.0,<0.16.0'", "Installing tokenizers")
    
    # Step 4: Install transformers with compatible version
    print("\n[INFO] Installing transformers...")
    if not run_command("pip install 'transformers>=4.30.0,<4.36.0'", "Installing transformers"):
        print("[ERROR] Failed to install transformers")
        return False
    
    # Step 5: Install sentence-transformers
    print("\n[INFO] Installing sentence-transformers...")
    if not run_command("pip install 'sentence-transformers>=2.2.0,<2.3.0'", "Installing sentence-transformers"):
        print("[ERROR] Failed to install sentence-transformers")
        return False
    
    # Step 6: Test the installation
    print("\n[INFO] Testing Hugging Face compatibility...")
    test_code = """
try:
    from huggingface_hub import hf_hub_download
    print("SUCCESS: huggingface_hub working correctly")
    
    import transformers
    print("SUCCESS: transformers version:", transformers.__version__)
    
    import sentence_transformers
    print("SUCCESS: sentence_transformers version:", sentence_transformers.__version__)
    
    print("SUCCESS: All Hugging Face packages compatible")
    
except Exception as e:
    print("ERROR:", str(e))
"""
    
    success = run_command(f"python -c \"{test_code}\"", "Testing compatibility")
    
    if success:
        print("\n[SUCCESS] Compatible versions installed successfully!")
    else:
        print("\n[WARNING] Some issues remain, trying alternative approach...")
        
        # Alternative: Install minimal versions
        print("\n[INFO] Installing minimal working versions...")
        minimal_packages = [
            "transformers==4.21.0",
            "sentence-transformers==2.1.0"
        ]
        
        for package in minimal_packages:
            run_command(f"pip install {package}", f"Installing {package}")
    
    print("\n[INFO] Next steps:")
    print("1. Run: python main.py")
    print("2. If you still get import errors, try the minimal installation")

if __name__ == "__main__":
    main()