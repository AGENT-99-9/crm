import os
import sys
import subprocess
import platform
import shutil

def build_executable():
    print("🚀 Starting Nexus CRM Build Process...")
    
    # Forcefully kill the background executable if it's already running (Windows)
    if platform.system() == 'Windows':
        print("Checking for existing NexusCRM instances...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "NexusCRM.exe"], capture_output=True)
        except Exception:
            pass

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Determine OS-specific path separator for PyInstaller --add-data
    sep = ';' if platform.system() == 'Windows' else ':'
    
    frontend_path = f"../frontend{sep}frontend"
    schema_path = f"database/schema.sql{sep}database"
    
    command = [
        "pyinstaller",
        "--name", "NexusCRM",
        "--noconsole",
        "--onefile",
        "--add-data", frontend_path,
        "--add-data", schema_path,
        "--clean",
        "-y",
        "launcher.py"
    ]
    
    print(f"📦 Building for {platform.system()}...")
    print(f"Running command: {' '.join(command)}")
    
    # Run PyInstaller
    subprocess.check_call(command)
    
    print("\n✅ Build complete!")
    print(f"Your executable is ready in the 'dist' folder.")
    if platform.system() == 'Windows':
        print("Look for: dist\\NexusCRM.exe")
    elif platform.system() == 'Darwin':
        print("Look for: dist/NexusCRM.app or dist/NexusCRM")
    else:
        print("Look for: dist/NexusCRM")

if __name__ == '__main__':
    build_executable()
