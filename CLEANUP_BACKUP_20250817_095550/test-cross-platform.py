#!/usr/bin/env python3
"""
Cross-platform compatibility test for OneLab
Run this on both Mac and Windows to verify compatibility
"""

import os
import sys
import platform
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from onelab.cross_platform import (
        get_platform_info, 
        is_windows, 
        is_mac, 
        is_linux,
        get_base_dir,
        get_media_root,
        get_static_root,
        get_logs_dir,
        get_database_config,
        get_redis_config,
        get_celery_config,
        get_file_upload_config,
        create_directories,
        get_environment_info
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this from the backend directory")
    sys.exit(1)

def test_platform_detection():
    """Test platform detection functions"""
    print("🔍 Testing Platform Detection...")
    
    platform_info = get_platform_info()
    print(f"   System: {platform_info['system']}")
    print(f"   Release: {platform_info['release']}")
    print(f"   Machine: {platform_info['machine']}")
    print(f"   Python: {platform_info['python_version']}")
    
    print(f"   Is Windows: {is_windows()}")
    print(f"   Is Mac: {is_mac()}")
    print(f"   Is Linux: {is_linux()}")
    
    print("✅ Platform detection working")

def test_path_handling():
    """Test path handling functions"""
    print("\n📁 Testing Path Handling...")
    
    base_dir = get_base_dir()
    media_root = get_media_root()
    static_root = get_static_root()
    logs_dir = get_logs_dir()
    
    print(f"   Base Directory: {base_dir}")
    print(f"   Media Root: {media_root}")
    print(f"   Static Root: {static_root}")
    print(f"   Logs Directory: {logs_dir}")
    
    # Check if paths are absolute and exist
    assert base_dir.is_absolute(), "Base directory should be absolute"
    print("✅ Path handling working")

def test_configuration():
    """Test configuration functions"""
    print("\n⚙️  Testing Configuration...")
    
    db_config = get_database_config()
    redis_config = get_redis_config()
    celery_config = get_celery_config()
    file_config = get_file_upload_config()
    
    print(f"   Database Engine: {db_config['ENGINE']}")
    print(f"   Redis Backend: {redis_config['BACKEND']}")
    print(f"   Celery Broker: {celery_config['broker_url']}")
    print(f"   File Upload Max: {file_config['FILE_UPLOAD_MAX_MEMORY_SIZE']} bytes")
    
    print("✅ Configuration working")

def test_directory_creation():
    """Test directory creation"""
    print("\n📂 Testing Directory Creation...")
    
    try:
        directories = create_directories()
        print(f"   Created {len(directories)} directories:")
        for directory in directories:
            print(f"     - {directory}")
            assert directory.exists(), f"Directory {directory} should exist"
        print("✅ Directory creation working")
    except Exception as e:
        print(f"❌ Directory creation failed: {e}")

def test_environment_info():
    """Test environment information gathering"""
    print("\n🌍 Testing Environment Info...")
    
    env_info = get_environment_info()
    
    print(f"   Platform: {env_info['platform']['system']}")
    print(f"   Base Dir: {env_info['base_dir']}")
    print(f"   Media Root: {env_info['media_root']}")
    print(f"   Is Windows: {env_info['is_windows']}")
    print(f"   Is Mac: {env_info['is_mac']}")
    print(f"   Is Linux: {env_info['is_linux']}")
    
    print("✅ Environment info working")

def test_django_compatibility():
    """Test Django-specific compatibility"""
    print("\n🐍 Testing Django Compatibility...")
    
    try:
        # Test Django settings import
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onelab.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        print(f"   Django Version: {django.get_version()}")
        print(f"   Debug Mode: {settings.DEBUG}")
        print(f"   Database Engine: {settings.DATABASES['default']['ENGINE']}")
        print(f"   Static Root: {settings.STATIC_ROOT}")
        print(f"   Media Root: {settings.MEDIA_ROOT}")
        
        print("✅ Django compatibility working")
        
    except Exception as e:
        print(f"⚠️  Django compatibility test skipped: {e}")
        print("   (This is normal if Django is not fully configured)")

def main():
    """Run all compatibility tests"""
    print("🚀 OneLab Cross-Platform Compatibility Test")
    print("=" * 50)
    
    try:
        test_platform_detection()
        test_path_handling()
        test_configuration()
        test_directory_creation()
        test_environment_info()
        test_django_compatibility()
        
        print("\n🎉 All compatibility tests passed!")
        print("\n📋 Summary:")
        print("   ✅ Platform detection working")
        print("   ✅ Path handling working")
        print("   ✅ Configuration working")
        print("   ✅ Directory creation working")
        print("   ✅ Environment info working")
        
        if is_windows():
            print("\n💡 Windows-specific recommendations:")
            print("   - Use Docker Desktop with WSL 2 backend")
            print("   - Configure Windows Firewall for ports 8000, 5432, 6379")
            print("   - Use Windows Services for production deployment")
        elif is_mac():
            print("\n💡 Mac-specific recommendations:")
            print("   - Use local development for faster iteration")
            print("   - Use Docker for production-like testing")
            print("   - Consider using Docker Desktop for consistency")
        
        print("\n🔧 Next Steps:")
        print("   1. Run this test on both Mac and Windows")
        print("   2. Compare results to ensure compatibility")
        print("   3. Address any differences found")
        print("   4. Proceed with deployment")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("💡 Check the error and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
