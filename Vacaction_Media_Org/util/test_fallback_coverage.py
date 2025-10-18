#!/usr/bin/env python3
"""
Test different cities with the current fallback system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geo_translation_editor import GeoTranslationEditor
import tkinter as tk

def test_cities():
    """Test various cities to see coverage of our fallback database"""
    # Create a dummy tkinter root for the editor
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create editor instance
    editor = GeoTranslationEditor(root)
    
    test_cases = [
        ("Tokyo", "Japan"),
        ("Seoul", "South Korea"),
        ("Beijing", "China"),
        ("Bangkok", "Thailand"),
        ("Paris", "France"),
        ("New York", "United States"),
        ("Sydney", "Australia"),
        ("Mumbai", "India"),
        ("Singapore", "Singapore"),
        ("London", "United Kingdom"),
        ("Berlin", "Germany"),
        ("Rome", "Italy"),
        # Test some that might not be in database
        ("Portland", "United States"),
        ("Lyon", "France"),
        ("Nagoya", "Japan"),
        ("Busan", "South Korea"),
    ]
    
    print("Testing fallback database coverage...")
    print("=" * 60)
    
    for city, country in test_cases:
        result = editor.get_fallback_translation(city, country)
        status = "✅ Found" if result else "❌ Missing"
        print(f"{status}: {city}, {country} -> {result if result else 'N/A'}")
    
    print("\n" + "=" * 60)
    print("Testing search method with variations...")
    
    # Test the full search method
    test_city = "Portland"
    test_country = "United States"
    candidates = editor.search_chinese_city_candidates(test_city, test_country)
    print(f"\nTest result for {test_city}, {test_country}: {candidates}")

if __name__ == "__main__":
    test_cities()