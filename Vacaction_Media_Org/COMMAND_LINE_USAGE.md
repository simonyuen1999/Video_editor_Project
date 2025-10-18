# Geographic Translation Editor - Command Line Options

## Overview
The Geographic Translation Editor is a comprehensive GUI application for managing city translations with advanced features including batch editing, conditional sorting, and robust CSV validation.

## Usage Examples

### Default Usage (uses HK_City_en_translated.csv)
```bash
python geo_translation_editor.py
```

### Custom CSV File
```bash
python geo_translation_editor.py --city-csv my_custom_cities.csv
```

### Help
```bash
python geo_translation_editor.py --help
```

## Command Line Parameters

### --city-csv
Specify a custom CSV file containing additional city translations.

**Default**: `HK_City_en_translated.csv` (322 Hong Kong locations)

**Examples:**
```bash
# Use custom translation file
python geo_translation_editor.py --city-csv custom_cities.csv

# Use backup HK file
python geo_translation_editor.py --city-csv HK_City_en_translated_backup.csv
```

## CSV File Requirements

The CSV file must contain exactly three columns with these headers:
- `City` - City names (Chinese or other languages)
- `Country` - Country names
- `English` - English translations

### Valid CSV Format:
```csv
City,Country,English
香港,香港,Hong Kong
北京,中国,Beijing
上海,中国,Shanghai
台北,台湾,Taipei
```

### Header Validation:
- **Exact match required**: Headers must be `City,Country,English`
- **Case sensitive**: Capitalization must match exactly
- **No extra columns**: Only these three columns allowed
- **BOM handling**: UTF-8 BOM automatically stripped if present

## Error Handling & Validation

### File Validation:
- **File not found**: Program exits with error code 1
- **File not readable**: Program exits with permission details
- **Empty file**: Program exits with "file is empty" message

### CSV Structure Validation:
- **Wrong headers**: Program exits showing required format
- **Missing columns**: Program exits with column requirements
- **Invalid format**: Program exits with format specifications

### Error Exit Behavior:
All validation errors use `sys.exit(1)` to prevent data corruption and ensure clean program termination.

## Application Features

### Built-in Translation Database
- **100+ international cities** with pre-loaded translations
- **322 Hong Kong locations** from default CSV file
- Seamless integration of custom CSV data

### Advanced Filtering & Sorting
- **Country Filter**: "All Countries" or specific country selection
- **Conditional Sorting**:
  - "All Countries": Maintains original order
  - Specific country: Alphabetical sorting by English translation
- **Real-time Search**: Filter cities by name as you type

### Batch Editing ("Edit All" Button)
- **Availability**: Enabled when country filter is selected
- **Functionality**: Updates all visible cities with fallback translations
- **Progress Dialog**: Shows real-time update progress
- **Confirmation**: Requires user confirmation before applying changes
- **Memory Updates**: Changes stored in memory, not automatically saved

### Individual Editing
- **Direct Translation**: Edit translations for individual cities
- **Immediate Feedback**: Changes reflected instantly in interface
- **Memory Storage**: All edits maintained in application memory

## Technical Implementation

### Method Names (Current Version):
- `load_city_translations()` - CSV loading with comprehensive validation
- `edit_all_cities()` - Batch editing with progress tracking
- `filter_cities()` - Search and country-based filtering
- `update_display()` - UI refresh with conditional sorting logic

### Memory Management:
- All changes stored in `city_translations` dictionary
- No automatic file writing
- User controls when/if to save changes to file

### Dependencies:
- Python 3.8+ required
- `tkinter` - GUI framework (included with Python)
- `argparse` - Command-line argument parsing
- `csv` - CSV file processing
- `sys` - System exit functionality

## Troubleshooting

### Common Error Messages:
1. **"Required columns (City, Country, English) not found"**
   - Solution: Check CSV headers match exactly

2. **"File 'filename' not found"**
   - Solution: Verify file path and file existence

3. **"Expected exactly 3 columns, found X"**
   - Solution: Ensure CSV has only City, Country, English columns

4. **"CSV file is empty or has no data rows"**
   - Solution: Add data rows beyond the header

### Best Practices:
- Use UTF-8 encoding for files with Chinese characters
- Test CSV files with small datasets first
- Include proper headers as the first row
- Avoid extra spaces in column names
- Check file permissions if getting read errors

## Features Summary:
- ✅ Command-line parameter support with validation
- ✅ Comprehensive CSV header and structure validation
- ✅ UTF-8 BOM (Byte Order Mark) automatic handling
- ✅ Strict error handling with program exit on critical errors
- ✅ Built-in translation database (100+ international cities)
- ✅ Hong Kong location database (322 locations)
- ✅ Conditional sorting based on country selection
- ✅ Batch editing functionality with progress tracking
- ✅ Real-time search and filtering capabilities
- ✅ Memory-based editing with user-controlled saving