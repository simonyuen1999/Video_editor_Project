# EXIF File Processor

A comprehensive Python script for processing media files with EXIF metadata analysis, file cleanup, and intelligent timestamp calculation.

## Features

### 🧹 File Cleanup
- **Deletes dot files**: Removes all hidden files (starting with `.`)
- **Deletes LRF files**: Removes camera raw/metadata LRF files
- **Recursive processing**: Traverses all subdirectories

### 🔧 File Extension Correction
- **EXIF-based correction**: Compares file extensions with EXIF FileType
- **Automatic renaming**: Corrects mismatched extensions
- **Collision handling**: Prevents overwriting existing files

### 📅 Intelligent Timestamp Calculation
- **Multiple date sources**: Uses EXIF CreateDate and FileInodeChangeDate
- **Smart logic**: Applies sophisticated rules for creation time calculation:
  - **Case 2.0**: If CreateDate is `0000:00:00` → Creation_time = 'N/A'
  - **Case 2.1**: If FileInodeChangeDate is few days newer → Apply time offset from inode to CreateDate
  - **Case 2.2**: If dates are same/1-day different → Use FileInodeChangeDate

### 🌍 GPS Data Extraction
- **GPS coordinates**: Extracts GPSLatitude and GPSAltitude
- **Missing data handling**: Uses 'N/A' for undefined GPS values

### 📊 Comprehensive Reporting
- **CSV output**: Detailed file inventory with all metadata
- **Log file**: Complete audit trail of all operations
- **Summary report**: Processing statistics and results

## Requirements

### Software Dependencies
```bash
# ExifTool (required)
# macOS
brew install exiftool

# Ubuntu/Debian  
sudo apt-get install libimage-exiftool-perl

# Windows
# Download from https://exiftool.org/
```

### Python Requirements
- Python 3.6+
- Standard library only (no additional pip packages needed)

## Usage

### Basic Usage
```bash
python exif_file_processor.py /path/to/directory
```

### Example
```bash
# Process vacation photos directory
python exif_file_processor.py /Users/john/Photos/VacationTrip2024

# Process camera card contents
python exif_file_processor.py /Volumes/SDCARD/DCIM
```

## Output Files

### CSV Report (`exif_report.csv`)
Contains the following columns:
- **FileType**: EXIF FileType (JPEG, MP4, etc.)
- **filename**: Final filename after any renames
- **CreateDate**: Original EXIF CreateDate
- **FileInodeChangeDate**: File system change date
- **Creation_time**: Calculated creation time using intelligent logic
- **GPSAltitude**: GPS altitude or 'N/A'
- **GPSLatitude**: GPS latitude or 'N/A'

### Log File (`exif_processor_log_YYYYMMDD_HHMMSS.log`)
Detailed audit trail including:
- All file operations (delete, rename)
- EXIF extraction results
- Date calculation decisions
- Error messages and warnings
- Processing statistics

## Supported File Types

### Image Formats
- JPEG, TIFF, PNG, GIF, BMP, WebP
- HEIC, HEIF (Apple formats)
- RAW formats: CR2, NEF, ARW, DNG, ORF, RAF, RW2, PEF

### Video Formats  
- MOV, MP4, AVI, MKV, WMV, FLV
- M4V, MPG, MPEG

## Processing Logic

### Date Calculation Algorithm
```
IF CreateDate is '0000:00:00' or invalid:
    Creation_time = 'N/A'
    
ELSE IF FileInodeChangeDate is few days newer than CreateDate:
    # Extract time from inode date, apply to create date
    Creation_time = CreateDate.date + FileInodeChangeDate.time
    
ELSE IF CreateDate and FileInodeChangeDate are same/1-day different:
    Creation_time = FileInodeChangeDate
    
ELSE:
    Creation_time = CreateDate (fallback)
```

### Extension Correction
1. Extract EXIF FileType using ExifTool
2. Compare with current file extension (case-sensitive)
3. **Always rename to UPPERCASE extensions** (e.g., `.jpeg` → `.JPG`, `.heic` → `.HEIC`)
4. Rename even if extension matches FileType but wrong case (e.g., `.jpg` → `.JPG`)
5. Skip if target filename already exists

## Safety Features

- **Non-destructive by default**: Extensive logging before any operations
- **Collision avoidance**: Won't overwrite existing files during renames
- **Error handling**: Continues processing even if individual files fail
- **Backup recommendations**: Always backup important data before processing

## Example Output

### Console Output
```
🚀 Starting EXIF File Processor
📁 Processing directory: /Users/john/Photos/Trip2024
📝 Log file: exif_processor_log_20241116_143022.log
✅ ExifTool version 12.57 available
🗑️  Deleted 15 unwanted files (dot files + LRF files)
🔍 Processing files with EXIF analysis...
📊 Processed 100 files...
📊 Processed 200 files...
✅ Processed 247 files successfully
📊 Generating reports...
📄 CSV report: /Users/john/Photos/exif_report.csv

EXIF File Processor Summary Report
Generated: 2024-11-16 14:30:45

Directory Processed: /Users/john/Photos/Trip2024

Files Processed:
- Successfully processed: 247
- Files deleted: 15
- Files renamed: 3
- Errors encountered: 2
```

### Sample CSV Output
```csv
FileType,filename,CreateDate,FileInodeChangeDate,Creation_time,GPSAltitude,GPSLatitude
JPEG,IMG_001.JPG,2024:03:15 14:23:45,2024:03:15 14:23:47,2024:03:15 14:23:47,N/A,N/A
MP4,VID_002.MP4,2024:03:15 15:30:12,2024:03:18 09:15:33,2024:03:15 09:15:33,125.5 m,40.7589 N
HEIC,IMG_003.HEIC,0000:00:00 00:00:00,2024:03:16 11:45:22,N/A,N/A,N/A
```

## Troubleshooting

### Common Issues

1. **ExifTool not found**
   ```
   ❌ ExifTool not found. Please install ExifTool and ensure it's in your PATH
   ```
   Solution: Install ExifTool using package manager or from official website

2. **Permission denied errors**
   - Ensure read/write permissions on target directory
   - Run with appropriate privileges if needed

3. **Large directory processing**
   - Script processes files in batches
   - Monitor log file for progress on large datasets
   - Consider processing subdirectories separately for huge collections

### Performance Tips
- **SSD storage**: Faster processing on solid-state drives
- **Local processing**: Process local files rather than network drives
- **Batch processing**: For huge collections, consider splitting into subdirectories

## License

This script is provided as-is for personal and educational use.