#!/usr/bin/env python3
"""
Test script to verify AgriTech Assistant setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✅ Pydantic imported successfully")
    except ImportError as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    try:
        from app.core.config import settings
        print("✅ App configuration imported successfully")
    except ImportError as e:
        print(f"❌ App configuration import failed: {e}")
        return False
    
    try:
        from app.core.database import Base, User
        print("✅ Database models imported successfully")
    except ImportError as e:
        print(f"❌ Database models import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database creation"""
    print("\n🗄️ Testing database setup...")
    
    try:
        from app.core.database import create_tables, engine
        create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    print("\n📁 Testing directory structure...")
    
    required_dirs = ['uploads', 'models', 'logs']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from app.core.config import settings
        print(f"✅ App name: {settings.APP_NAME}")
        print(f"✅ Version: {settings.VERSION}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        print(f"✅ Host: {settings.HOST}")
        print(f"✅ Port: {settings.PORT}")
        print(f"✅ Database URL: {settings.DATABASE_URL}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🌱 AgriTech Assistant Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_directories,
        test_config,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"\n❌ Test failed: {test.__name__}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AgriTech Assistant is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   python run.py")
        print("\n📚 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)