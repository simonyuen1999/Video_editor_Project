# Vacation Media Organizer - Utility Scripts

This directory contains utility Python scripts for media file processing and organization. These tools are designed to work with various media formats and help with file management tasks.

## Scripts Overview

### 1. `extractHEIF.py` - HEIC/HEIF Image Processor

**Purpose**: Extracts metadata from HEIC (High Efficiency Image Container) files and converts them to JPEG format.

**Usage**:
```bash
python extractHEIF.py <heic_file_path>
```

**Features**:
- ✅ Loads HEIC files using `pillow-heif` integration
- ✅ Extracts EXIF metadata including creation date
- ✅ Converts HEIC images to RGB format
- ✅ Saves converted images as high-quality JPEG files
- ✅ Robust error handling for unsupported files
- ✅ Displays image information (size, mode, format)

**Dependencies**:
- `pillow-heif` - For HEIC file support
- `PIL (Pillow)` - For image processing

**Example Output**:
```
Reading IMG_1234.HEIC file
Date taken: 2023:10:15 14:30:22
Image size: (4032, 3024)
Image mode: RGB
Image format: HEIF
Converted and saved as: IMG_1234.jpg
```

**Recent Fixes**:
- Fixed import issues (`pyheif` → `pillow-heif`)
- Removed dependency on `piexif`
- Added proper HEIF opener registration
- Enhanced error handling and metadata extraction

---

### 2. `dji_rename.py` - DJI Video File Organizer

**Purpose**: Cleans up and renames DJI drone video files, removing unwanted files and organizing filenames.

**Usage**:
```bash
cd /path/to/video/directory
python dji_rename.py
```

**Features**:
- ✅ Removes `.LRF` files (DJI metadata files)
- ✅ Deletes duplicate files containing "- Copy" in filename
- ✅ Renames DJI video files to standardized format
- ✅ Processes files in current directory
- ✅ Uses regex pattern matching for DJI filename format

**File Processing**:
- **Deletes**: `.LRF` files, duplicate copies
- **Renames**: DJI format files (`DJI_YYYYMMDDHHMMSS_XXX_D.MP4`)
- **Target Format**: Standardized naming convention

**DJI Filename Pattern**:
```
Original: DJI_20231015143022_001_D.MP4
Pattern:  DJI_YYYYMMDDHHMMSS_XXX_D.MP4
```

**Safety Features**:
- Only processes files matching DJI patterns
- Provides console output for all operations
- Case-insensitive file extension matching

---

### 3. `exif_Tool.py` - EXIF Metadata Tool

**Purpose**: Advanced EXIF metadata extraction and processing for various media file formats with timezone handling.

**Usage**:
```bash
python exif_Tool.py <media_file_path>
```

**Features**:
- ✅ Extracts creation dates from multiple file formats
- ✅ Handles timezone adjustments for different cameras
- ✅ Supports multiple filename patterns
- ✅ Uses ExifTool for robust metadata extraction
- ✅ JSON output parsing for structured data

**Supported File Patterns**:
1. `YYYY-MM-DD_HH-MM-SS.MP4` (Standard format)
2. `YYYY-MM-DD_HH:MM:SS.MP4` (Colon separator)
3. `YYYY-MM-DD_HH:MM:SS.HEIC` (HEIC images)
4. `IMG_XXXXX.MOV` (iPhone/Apple format)

**Camera-Specific Handling**:
- **DJI Pocket 3**: Adjusts for Toronto timezone (+12 hours to match Asia time)
- **iPhone**: Uses local time (no adjustment needed)

**Dependencies**:
- `exiftool` (external command-line tool)
- Standard Python libraries (`subprocess`, `json`, `datetime`, `re`)

**Technical Details**:
- Uses regex patterns for strict filename validation
- Handles multiple datetime formats
- Provides timezone offset calculations
- JSON parsing for structured metadata extraction

---

## Installation & Dependencies

### Install Required Python Packages:
```bash
pip install pillow pillow-heif
```

### Install External Tools:
```bash
# macOS (using Homebrew)
brew install exiftool

# Or download from: https://exiftool.org/
```

### Verify Installation:
```bash
# Test HEIC support
python -c "import pillow_heif; print('✓ HEIC support ready')"

# Test ExifTool
exiftool -ver
```

---

## Common Use Cases

### 1. **Process iPhone HEIC Photos**:
```bash
# Convert HEIC to JPEG with metadata extraction
python extractHEIF.py IMG_1234.HEIC
```

### 2. **Clean DJI Video Directory**:
```bash
# Navigate to video folder and clean up
cd /Volumes/SD_Card/DCIM/100MEDIA/
python /path/to/dji_rename.py
```

### 3. **Extract Metadata from Media Files**:
```bash
# Get creation date and camera info
python exif_Tool.py DJI_20231015143022_001_D.MP4
python exif_Tool.py IMG_1234.HEIC
```

---

## Error Handling & Troubleshooting

### Common Issues:

1. **HEIC Import Errors**:
   - Ensure `pillow-heif` is installed
   - Check HEIC file is not corrupted

2. **ExifTool Not Found**:
   - Install ExifTool system-wide
   - Add to PATH environment variable

3. **Permission Errors**:
   - Check file permissions
   - Run with appropriate user privileges

### Debug Mode:
Add error checking and verbose output by modifying the scripts or running with Python's `-v` flag.

---

## Integration with Main System

These utility scripts complement the main vacation media organizer system:

- **extractHEIF.py**: Preprocesses HEIC files for the main database
- **dji_rename.py**: Cleans video directories before scanning
- **exif_Tool.py**: Provides metadata extraction capabilities

They can be used standalone or integrated into automated workflows for media processing pipelines.