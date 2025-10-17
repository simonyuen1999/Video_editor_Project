#!/usr/bin/env python3
"""
Test script to debug the country_zh issue
"""

import csv

def test_data_loading():
    """Test the data loading logic from the main application"""
    
    csv_file_path = "geo_chinese_bkup.list"
    data = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Read first line to detect delimiter and headers
            first_line = file.readline().strip()
            
            # Reset file position
            file.seek(0)
            
            # Try different delimiters
            delimiter = ',' if ',' in first_line else '\t'
            
            reader = csv.DictReader(file, delimiter=delimiter)
            
            # Process first 5 rows for testing
            for i, row in enumerate(reader):
                if i >= 5:
                    break
                    
                # Map various possible column names to standardized names
                city_en = row.get('City_en', row.get('city_en', row.get('City', '')))
                city_zh = row.get('City_zn', row.get('city_zh', row.get('City_zh', '')))
                country_en = row.get('Country_en', row.get('country_en', row.get('Country', '')))
                country_zh = row.get('Country_zn', row.get('country_zh', row.get('Country_zh', '')))
                
                data_item = {
                    'city_en': city_en.strip(),
                    'city_zh': city_zh.strip(),
                    'country_en': country_en.strip(),
                    'country_zh': country_zh.strip(),
                    'original_row': row
                }
                
                data.append(data_item)
                
                print(f"Row {i+1}:")
                print(f"  city_en: {repr(data_item['city_en'])}")
                print(f"  city_zh: {repr(data_item['city_zh'])}")
                print(f"  country_en: {repr(data_item['country_en'])}")
                print(f"  country_zh: {repr(data_item['country_zh'])}")
                print()
                
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    return data

if __name__ == "__main__":
    print("Testing data loading logic...")
    print("=" * 50)
    data = test_data_loading()
    
    if data:
        print(f"Successfully loaded {len(data)} test records")
        print(f"First record country_zh: {repr(data[0]['country_zh'])}")
    else:
        print("Failed to load data")