import pandas as pd
from googletrans import Translator
import argparse
import time
import sys

def translate_cities(input_file, output_file):
    print(f"📖 Reading CSV file: {input_file}")
    # Read CSV file - keep original data
    original_df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(original_df)} rows with columns: {list(original_df.columns)}")
    
    # Initialize translator
    print("🌐 Initializing Google Translator...")
    translator = Translator()
    
    # Initialize translation cache to avoid re-translation
    translation_cache = {}
    
    # Test translator connection
    try:
        test_translation = translator.translate("test", src='en', dest='zh-cn')
        print(f"✅ Translator test successful: 'test' → '{test_translation.text}'")
    except Exception as e:
        print(f"❌ Translator test failed: {e}")
        print("🚨 Cannot connect to Google Translate. Check your internet connection.")
        return
    
    # Translate city names with rate limiting and progress tracking
    def translate_city_safe(city_name, column_name, row_index):
        if pd.isna(city_name) or str(city_name).strip() == '':
            return city_name
            
        try:
            # Add small delay to avoid rate limiting
            time.sleep(0.1)  # 100ms delay between requests
            
            # Check if already translated to avoid duplicates
            cache_key = f"{column_name}_{row_index}_{city_name}"
            if cache_key in translation_cache:
                return translation_cache[cache_key]

            translation = translator.translate(str(city_name), src='en', dest='zh-cn')
            result = translation.text

            # Save the result to avoid re-translation
            translation_cache[cache_key] = result

            # Print progress every 10 translations
            if (row_index + 1) % 10 == 0:
                print(f"  Progress: {row_index + 1} translations completed...")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Translation failed for '{city_name}' in {column_name}: {e}")
            return city_name  # Return original if translation fails

    # Create merged DataFrame with original and translated columns side by side
    print(f"\n🔗 Creating merged structure...")
    merged_df = pd.DataFrame()
    
    # Process each column that contains string data
    for col in original_df.columns:
        # Add original column first
        merged_df[f"{col}_original"] = original_df[col]
        
        if original_df[col].dtype == 'object':  # String columns
            print(f"\n🔄 Translating column: '{col}'")
            
            # Apply translation with progress tracking
            translated_values = []
            for idx, value in enumerate(original_df[col]):
                translated = translate_city_safe(value, col, idx)
                translated_values.append(translated)
                
                # Update progress every 25 items
                if (idx + 1) % 25 == 0:
                    progress = (idx + 1) / len(original_df) * 100
                    print(f"  📊 {col}: {idx + 1}/{len(original_df)} ({progress:.1f}%)")
            
            # Add translated column right next to original
            merged_df[f"{col}_chinese"] = translated_values
            print(f"✅ Completed column '{col}': Sample translations: {translated_values[:3]}")
        else:
            # For non-string columns, just copy the original data
            merged_df[f"{col}_chinese"] = original_df[col]
    
    # Print column structure
    print(f"\n📋 Output structure: {len(merged_df.columns)} columns")
    for i, col_name in enumerate(merged_df.columns):
        print(f"  Column {i+1}: {col_name}")

    # Save merged data to new CSV file
    print(f"\n💾 Saving merged data to {output_file}...")
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"🎉 Translation completed! File saved as {output_file}")
    print(f"📊 Final stats: {len(merged_df)} rows, {len(merged_df.columns)} columns (original + translated)")
    
    # Show sample of merged data
    print(f"\n📄 Sample of merged data:")
    print(merged_df.head(3).to_string())

# Use arguments or hardcode input file names here
parser = argparse.ArgumentParser(
    description="Translate geographic data from English to Chinese and merge with original data."
)
parser.add_argument(
    '--debug-level', type=str, default='INFO',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    help='Set the logging debug level (default: INFO).'
)
parser.add_argument(
    '--geo-list', type=str, default='Chinese_City_en.csv',
    help='Path to the Chinese CSV file for input parameter (default: Chinese_City_en.csv).'
)

if __name__ == "__main__":
    args = parser.parse_args()
    fname = args.geo_list
    output_file = fname.replace('.csv', '_translated.csv')
    translate_cities(fname, output_file)