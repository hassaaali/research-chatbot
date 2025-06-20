#!/usr/bin/env python3
"""
Quick fix for the huggingface_hub import error
"""
import subprocess
import sys

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"SUCCESS: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("Quick Fix for Hugging Face Import Error")
    print("=" * 40)
    
    # Method 1: Uninstall and reinstall with compatible versions
    print("\nStep 1: Removing problematic packages...")
    run_command("pip uninstall sentence-transformers transformers huggingface-hub tokenizers -y")
    
    print("\nStep 2: Installing compatible versions...")
    run_command("pip install 'huggingface-hub==0.16.4'")
    run_command("pip install 'tokenizers==0.13.3'") 
    run_command("pip install 'transformers==4.21.0'")
    run_command("pip install 'sentence-transformers==2.1.0'")
    
    # Test the fix
    print("\nStep 3: Testing the fix...")
    test_code = '''
try:
    import huggingface_hub
    print("huggingface_hub imported successfully")
    
    from sentence_transformers import SentenceTransformer
    print("sentence_transformers imported successfully")
    
    print("SUCCESS: Import error fixed!")
except Exception as e:
    print("ERROR:", str(e))
'''
    
    if run_command(f"python -c \"{test_code}\""):
        print("\nSUCCESS: Import error fixed!")
        print("You can now run: python main.py")
    else:
        print("\nIf the above failed, try this alternative:")
        print("pip install --no-deps sentence-transformers==2.1.0")
        print("pip install --no-deps transformers==4.21.0")

if __name__ == "__main__":
    main()