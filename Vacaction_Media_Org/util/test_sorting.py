#!/usr/bin/env python3
"""
Test the sorting functionality for country filtering
"""

import sys
import os
import tkinter as tk

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sorting_logic():
    """Test the sorting logic without GUI"""
    
    # Sample data to test with
    test_data = [
        {'city_en': 'Tokyo', 'city_zh': '东京', 'country_en': 'Japan', 'country_zh': '日本'},
        {'city_en': 'Osaka', 'city_zh': '大阪', 'country_en': 'Japan', 'country_zh': '日本'},
        {'city_en': 'Beijing', 'city_zh': '北京', 'country_en': 'China', 'country_zh': '中国'},
        {'city_en': 'Shanghai', 'city_zh': '上海', 'country_en': 'China', 'country_zh': '中国'},
        {'city_en': 'Kyoto', 'city_zh': '京都', 'country_en': 'Japan', 'country_zh': '日本'},
        {'city_en': 'Guangzhou', 'city_zh': '广州', 'country_en': 'China', 'country_zh': '中国'},
    ]
    
    print("Original data order:")
    for i, item in enumerate(test_data, 1):
        print(f"{i}. {item['city_en']}, {item['country_en']}")
    
    print("\n" + "="*50)
    
    # Test "All Countries" case (no sorting)
    print("\nCase 1: All Countries selected (no sorting)")
    filtered_data = test_data.copy()
    for i, item in enumerate(filtered_data, 1):
        print(f"{i}. {item['city_en']}, {item['country_en']}")
    
    print("\n" + "="*50)
    
    # Test specific country case (with sorting)
    print("\nCase 2: Japan selected (sorted by city name)")
    filtered_data = [item for item in test_data if item['country_en'] == 'Japan']
    filtered_data.sort(key=lambda x: x['city_en'].lower())
    for i, item in enumerate(filtered_data, 1):
        print(f"{i}. {item['city_en']}, {item['country_en']}")
    
    print("\n" + "="*50)
    
    print("\nCase 3: China selected (sorted by city name)")
    filtered_data = [item for item in test_data if item['country_en'] == 'China']
    filtered_data.sort(key=lambda x: x['city_en'].lower())
    for i, item in enumerate(filtered_data, 1):
        print(f"{i}. {item['city_en']}, {item['country_en']}")
    
    print("\n✅ Sorting logic test completed!")
    print("Expected behavior:")
    print("- All Countries: Keep original order (Tokyo, Osaka, Beijing, Shanghai, Kyoto, Guangzhou)")
    print("- Japan: Sorted alphabetically (Kyoto, Osaka, Tokyo)")
    print("- China: Sorted alphabetically (Beijing, Guangzhou, Shanghai)")

if __name__ == "__main__":
    test_sorting_logic()