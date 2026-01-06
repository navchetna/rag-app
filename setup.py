"""
Setup and development utilities
"""
import sys
import os
import subprocess

def setup_environment():
    """Setup Python environment and install dependencies"""
    print("🔧 Setting up RAG Backend environment...")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        with open(".env.example", "r") as f:
            content = f.read()
        with open(".env", "w") as f:
            f.write(content)
        print("✅ .env file created. Please update it with your configuration.")
    
    # Install requirements with uv
    print("📦 Installing dependencies with uv...")
    # Try uv first, fall back to pip if uv is not available
    try:
        result = subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=False)
        if result.returncode != 0:
            print("⚠️  uv install failed, trying with pip...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False)
    except FileNotFoundError:
        print("⚠️  uv not found, using pip...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=False)
    
    if result.returncode != 0:
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Environment setup complete")
    return True


def run_server(debug=False):
    """Run the FastAPI server"""
    print("🚀 Starting RAG Backend server...")
    
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8080"
    ]
    
    if debug:
        cmd.append("--reload")
        print("🔍 Running in debug mode with auto-reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error running server: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Backend utilities")
    parser.add_argument("command", choices=["setup", "run"], help="Command to execute")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        success = setup_environment()
        sys.exit(0 if success else 1)
    
    elif args.command == "run":
        success = run_server(debug=args.debug)
        sys.exit(0 if success else 1)
