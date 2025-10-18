#!/usr/bin/env python3
"""
Test the improved Google search functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geo_translation_editor import GeoTranslationEditor

def main():
    print("Testing improved Google search functionality...")
    
    # Create a dummy tkinter root for the editor
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create editor instance
    editor = GeoTranslationEditor(root)
    
    # Test with Tokyo, Japan
    city = "Tokyo"
    country = "Japan"
    
    print(f"\n{'='*60}")
    print(f"TESTING: {city}, {country}")
    print(f"{'='*60}")
    
    try:
        # Search for Chinese candidates
        candidates = editor.search_chinese_city_candidates(city, country)
        
        print(f"\n🎯 FINAL RESULTS:")
        print(f"Number of candidates found: {len(candidates)}")
        
        if candidates:
            print(f"Candidates:")
            for i, candidate in enumerate(candidates, 1):
                print(f"  {i}. {candidate}")
        else:
            print("No candidates found")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()