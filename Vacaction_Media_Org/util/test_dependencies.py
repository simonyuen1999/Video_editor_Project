#!/usr/bin/env python3
"""
Test script to verify all required dependencies are properly installed
for the Google_translate_to_chinese.py module.
"""

def test_imports():
    """Test all required imports for the translation module."""
    
    print("🔧 Testing Python module dependencies...")
    print("=" * 50)
    
    # Test pandas
    try:
        import pandas as pd
        print(f"✅ pandas: {pd.__version__}")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False
    
    # Test googletrans
    try:
        from googletrans import Translator
        print("✅ googletrans: imported successfully")
        
        # Test basic translator functionality
        translator = Translator()
        print("✅ googletrans: Translator instance created")
    except ImportError as e:
        print(f"❌ googletrans: {e}")
        return False
    except Exception as e:
        print(f"⚠️  googletrans: Import successful but initialization failed: {e}")
        print("   This might be a network connectivity issue.")
    
    # Test argparse (built-in module)
    try:
        import argparse
        print("✅ argparse: available (built-in)")
    except ImportError as e:
        print(f"❌ argparse: {e}")
        return False
    
    print("=" * 50)
    print("✅ All required dependencies are available!")
    return True

def test_file_access():
    """Test if the expected input file exists."""
    
    print("\n📁 Testing file access...")
    print("=" * 50)
    
    import os
    
    expected_file = "Chinese_City_en.csv"
    if os.path.exists(expected_file):
        print(f"✅ {expected_file}: File exists")
        
        # Check if we can read it
        try:
            import pandas as pd
            df = pd.read_csv(expected_file)
            print(f"✅ {expected_file}: Readable with pandas ({len(df)} rows)")
        except Exception as e:
            print(f"⚠️  {expected_file}: Exists but read failed: {e}")
    else:
        print(f"⚠️  {expected_file}: File not found in current directory")
        print(f"   Current directory: {os.getcwd()}")

if __name__ == "__main__":
    print("🧪 Dependency Test for Google_translate_to_chinese.py")
    print("=" * 60)
    
    success = test_imports()
    test_file_access()
    
    if success:
        print("\n🎉 Ready to run Google_translate_to_chinese.py!")
    else:
        print("\n🚨 Please install missing dependencies before running the script.")