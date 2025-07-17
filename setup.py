#!/usr/bin/env python3
"""
Setup script for TimescaleDB Scan Data Viewer
"""
import os
import shutil

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from .env.example")
            print("  Please edit .env with your database credentials")
        else:
            print("✗ .env.example file not found")
    else:
        print("✓ .env file already exists")

def check_requirements():
    """Check if required files exist"""
    required_files = [
        'requirements.txt',
        'package.json',
        'backend/main.py',
        'backend/database.py',
        'backend/models.py',
        'src/App.js',
        'src/components/ScanDataTable.js',
        'src/components/FilterPanel.js',
        'src/services/api.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("✗ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("✓ All required files are present")
        return True

def main():
    print("TimescaleDB Scan Data Viewer Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\nSetup cannot continue due to missing files.")
        return
    
    # Create .env file
    create_env_file()
    
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Install Python dependencies: pip install -r requirements.txt")
    print("3. Install Node.js dependencies: npm install")
    print("4. Start backend: python start-backend.py")
    print("5. Start frontend: npm start")
    print("\nOr use Docker: docker-compose up")

if __name__ == "__main__":
    main()