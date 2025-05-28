#!/usr/bin/env python3
"""
Setup script for Cat Saver application.
This script creates a virtual environment and installs all required dependencies.
"""

import os
import sys
import subprocess
import platform

def main():
    print("🐱 Setting up Cat Saver - Balcony Cat Detection System 🐱")
    
    # Determine the Python executable to use
    python_executable = sys.executable
    print(f"Using Python: {python_executable}")
    
    # Create virtual environment
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.run([python_executable, "-m", "venv", venv_dir], check=True)
        print("✅ Virtual environment created successfully")
    else:
        print(f"⚠️ Virtual environment already exists in {venv_dir}")
    
    # Determine the pip executable in the virtual environment
    if platform.system() == "Windows":
        pip_executable = os.path.join(venv_dir, "Scripts", "pip")
        activate_script = os.path.join(venv_dir, "Scripts", "activate")
    else:
        pip_executable = os.path.join(venv_dir, "bin", "pip")
        activate_script = os.path.join(venv_dir, "bin", "activate")
    
    # Upgrade pip in the virtual environment
    print("Upgrading pip in virtual environment...")
    try:
        if platform.system() == "Windows":
            python_venv = os.path.join(venv_dir, "Scripts", "python")
        else:
            python_venv = os.path.join(venv_dir, "bin", "python")
        subprocess.run([python_venv, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    except Exception as e:
        print(f"Warning: Failed to upgrade pip: {e}")
        print("Continuing with installation...")

    
    # Install dependencies from requirements.txt
    if os.path.exists("requirements.txt"):
        print("Installing dependencies from requirements.txt...")
        subprocess.run([pip_executable, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    else:
        print("❌ requirements.txt not found")
        return
    
    print("\n🎉 Setup completed successfully!")
    print(f"\nTo activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"    {venv_dir}\\Scripts\\activate")
    else:
        print(f"    source {venv_dir}/bin/activate")
    
    print("\nTo run Cat Saver:")
    if platform.system() == "Windows":
        print(f"    {venv_dir}\\Scripts\\python cat_saver.py")
    else:
        print(f"    {venv_dir}/bin/python cat_saver.py")
    
    print("\nMake sure to update the config.yaml with your Telegram username before running!")

if __name__ == "__main__":
    main()
