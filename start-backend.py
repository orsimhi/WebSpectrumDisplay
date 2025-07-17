#!/usr/bin/env python3
"""
Script to start the FastAPI backend server
"""
import os
import sys
import subprocess

def main():
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Please create one based on .env.example")
        print("Make sure to configure your database connection settings.")
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8000', 
            '--reload'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBackend server stopped.")

if __name__ == "__main__":
    main()