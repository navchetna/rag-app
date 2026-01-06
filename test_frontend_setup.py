#!/usr/bin/env python3
"""
Simple test script to verify the Streamlit frontend configuration
"""

import sys
import subprocess

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'requests',
        'fastapi',
        'uvicorn',
    ]
    
    print("📦 Checking dependencies...\n")
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True


def check_file_structure():
    """Check if necessary files exist"""
    print("\n📁 Checking file structure...\n")
    
    required_files = [
        'streamlit_app.py',
        'main.py',
        'requirements.txt',
        'config.py',
    ]
    
    import os
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (not found)")
            return False
    
    print("\n✅ All required files are present!")
    return True


def main():
    print("=" * 60)
    print("🤖 RAG Streamlit Frontend - Pre-launch Check")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies and try again.")
        sys.exit(1)
    
    # Check files
    if not check_file_structure():
        print("\n⚠️  Some required files are missing.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All checks passed! Ready to launch.")
    print("=" * 60)
    print("\n📋 Next steps:\n")
    print("1. Start the backend (in a separate terminal):")
    print("   $ python setup.py run --debug")
    print("\n2. Start the frontend (in another terminal):")
    print("   $ streamlit run streamlit_app.py")
    print("\n3. Open your browser to:")
    print("   http://localhost:8501")
    print("\nOr run both with:")
    print("   $ ./run_all.sh")
    print()


if __name__ == "__main__":
    main()
