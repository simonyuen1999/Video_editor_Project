# Vacation Media Organizer: Smart Photo & Video Management System

## Overview

A comprehensive, Flask-based web application for organizing and exploring vacation photos and videos with intelligent metadata extraction, semantic analysis, and dual-view interfaces for enhanced media browsing.

## Latest Implementation (November 2025)

### **Advanced File Processing Pipeline**
- **PreImport EXIF Processing**: Automated file preparation with `PreImport_exif_file_processor.py`
  - Removes hidden dot files (.DS_Store, .thumbnails, etc.) and LRF sidecar files
  - Validates real media file types against file extensions
  - Automatically renames mismatched extensions and converts to uppercase
  - Calculates precise creation_time in UTC Zulu format
  - Embeds standardized timestamps in EXIF UserComment field
- **UTC Zulu Time Management**: Consistent UTC-based creation time handling throughout the system

### **Dual-Interface Web Application**
- **Map View**: Interactive map-based media exploration with clustering and filtering
- **Daily View**: Chronological day-by-day media browsing with flexible display modes
- **City View**: Location-focused media organization with unknown location highlighting
- **Special View**: Activity and scenery-based media browsing
- **FixInfo View**: Advanced metadata editing interface with bulk operations

### **Smart Media Organization**
- **Automated Metadata Extraction**: UTC Zulu creation time from EXIF UserComment, GPS coordinates, file size, and technical details
- **Semantic Analysis**: People detection, activity recognition, talking detection, and scenery classification
- **Location Intelligence**: Bilingual city/country support (English + Chinese) with geographic clustering
- **Database-Driven**: SQLite backend with comprehensive media indexing and relationship management
- **Time Zone Display**: Configurable display timezone (OffsetTime) for consistent local time presentation

### **Advanced User Experience**
- **Responsive Design**: Mobile-friendly interface with gradient themes and modern UI components
- **Interactive Features**: Clickable thumbnails, detailed modal views, and system file integration
- **Flexible Filtering**: Date ranges, location dropdowns, people count, and talking detection filters
- **Sorting Controls**: Chronological ordering with user-toggleable newest/oldest first options

### **Geographic Translation Editor** 
- **Comprehensive Database**: 100+ major cities worldwide with Chinese translations
- **Smart Sorting**: Conditional alphabetical sorting by city name when filtering by country
- **Reliable Translation**: Local fallback database eliminates Google search dependencies
- **City Name Variations**: Handles prefixes, suffixes, and alternate spellings automatically

## Architecture

### **Backend (Flask 3.1.1)**
```
src/
├── main.py                 # Application entry point
├── models/
│   └── media.py           # SQLAlchemy media model
├── routes/
│   └── media.py           # API endpoints for media operations
└── database/
    └── media_organizer.db # SQLite database with media metadata
```

### **Frontend (HTML5/JavaScript/CSS3)**
```
static/
├── index.html             # Map View - Interactive mapping interface
└── daily.html             # Daily View - Chronological browsing interface
```

### **Key Features Implemented**
1. **Bilingual Location Support**: City and country names in both English and Chinese
2. **Smart Default Date Selection**: Automatically loads earliest media date in Daily View
3. **Responsive Media Gallery**: Thumbnail and list view modes with adjustable sizing
4. **Modal Media Viewer**: Full-resolution media display with comprehensive metadata
5. **System Integration**: Direct file opening in default applications
6. **Saved Location Workflow**: Click-to-save GPS coordinates from reference files, then bulk apply to selected media
7. **Unknown Location Highlighting**: Visual indicators (darker yellow background) for media missing GPS data
6. **Advanced Filtering**: Dropdown-based city/country selection with live search
7. **Chronological Navigation**: Day-by-day browsing with previous/next controls

## Introduction

This solution provides a comprehensive, cross-platform system for organizing your vacation photos and videos from devices like iPhone and DJI Pocket 3. It automates the process of extracting metadata, performing semantic video analysis, organizing files by creation date, and creating intelligent links for location and scenery-based browsing. A local web-based interface allows for intuitive exploration, filtering, and playback of your media.

## Core Features

### **Intelligent Media Processing**
- **Multi-Format Support**: HEIC, JPG, PNG, MP4, MOV with comprehensive metadata extraction
- **Recursive Directory Scanning**: Complete subdirectory traversal with incremental update support
- **GPS Intelligence**: Smart coordinate assignment from HEIC files to GPS-less DJI MP4 files
- **Semantic Analysis Engine**: 
  - People detection and counting using YOLOv8
  - Activity classification (hiking, gathering, dining, touring)
  - Talking detection in video content
  - Scenery type identification

### **Geographic Intelligence System**
- **Bilingual Location Database**: English and Chinese city/country names from geo.list
- **Smart Location Assignment**: Automatic city/region identification from GPS coordinates
- **Interactive Map Clustering**: Geographic grouping with zoom-level awareness
- **Location-Based Filtering**: Dropdown selection with bilingual display format

### **Dual-View Web Interface**
- **Map View (index.html)**:
  - Interactive Leaflet map with media markers
  - Real-time clustering and marker management
  - Geographic filtering with location dropdowns
  - 60/40 layout ratio (map/filters)
  
- **Daily View (daily.html)**:
  - Day-by-day chronological navigation
  - Thumbnail and list display modes
  - Adjustable thumbnail sizing (small/medium/large)
  - Smart date initialization from earliest media

### **Advanced User Experience**
- **Modal Media Viewer**: Full-resolution display with complete metadata overlay
- **System File Integration**: Direct opening in default applications (Preview, QuickTime)
- **Responsive Design**: Mobile-optimized with gradient styling and modern UI
- **Live Statistics**: Real-time media counts and filtering feedback
- **Smart Defaults**: Automatic population of earliest creation dates

## Technology Stack

### **Backend Architecture**
- **Flask 3.1.1**: Modern Python web framework with SQLAlchemy ORM
- **SQLite Database**: Lightweight, file-based storage for media metadata
- **Computer Vision**: 
  - YOLOv8 for object and people detection
  - OpenCV for video frame analysis
  - PIL/Pillow for image processing
- **Audio Processing**: librosa for talking detection in videos

### **Frontend Technologies**
- **Leaflet.js**: Interactive mapping with clustering and marker management
- **Vanilla JavaScript ES6**: Modern client-side functionality without heavy frameworks
- **CSS3 Grid/Flexbox**: Responsive layout with gradient styling
- **HTML5**: Semantic markup with accessibility considerations

### **Development Environment**
- **Cross-Platform**: Native support for Windows, macOS, and Linux
- **Modern Python**: 3.8+ with type hints and async-ready architecture
- **Extensible Design**: Modular codebase for easy feature additions

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **Python**: Python 3.8 or higher with pip package manager
- **ExifTool**: Command-line metadata extraction tool ([Installation Guide](https://exiftool.org/install.html))
- **Memory**: Minimum 4GB RAM (8GB+ recommended for large media collections)
- **Storage**: SSD recommended for database performance
- **Internet**: Required for geocoding services and initial model downloads

## Quick Start Installation

### **1. ExifTool Setup**
```bash
# macOS (using Homebrew)
brew install exiftool

# Ubuntu/Debian
sudo apt-get install libimage-exiftool-perl

# Windows: Download from https://exiftool.org/install.html
```

### **2. Environment Setup**
```bash
# Clone and navigate to project
cd vacation_media_organizer2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Geographic Database**
Ensure `geo.list` file is present in the project directory with city/country data in CSV format:
```
City,Region,Subregion,CountryCode,Country,TimeZone,FeatureCode,Population,Latitude,Longitude
```

## Usage Guide

### **1. PreImport File Processing (Recommended First Step)**

Before scanning your media files, use the PreImport processor to prepare and standardize your files:

```bash
# Activate environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Process and prepare media files
python PreImport_exif_file_processor.py /path/to/your/raw/media/directory

# Interactive mode - prompts for directory path if not provided
python PreImport_exif_file_processor.py
```

**PreImport Processing Features:**
- **File Cleanup**: Automatically removes hidden dot files (.DS_Store, .thumbnails, ._metadata) and LRF sidecar files
- **File Type Validation**: Checks actual file content against file extension using magic bytes
- **Extension Standardization**: Renames mismatched extensions and converts all extensions to uppercase
- **UTC Zulu Time Calculation**: Determines precise creation_time in UTC Zulu format (YYYY-MM-DDTHH:MM:SS.sssZ)
- **EXIF Embedding**: Saves standardized UTC timestamps in EXIF UserComment field for consistent database import
- **File Structure Preservation**: Maintains original directory structure while standardizing files

**Example PreImport Output:**
```
Processing /path/to/media...
✅ Removed hidden file: .DS_Store
✅ Removed LRF file: IMG_1234.LRF  
✅ Renamed IMG_1234.jpeg → IMG_1234.JPEG (extension mismatch)
✅ Updated EXIF UserComment: 2025-03-15T14:30:25.123Z
✅ Processed 245 files successfully
```

### **2. Initial Media Scanning**

Process your vacation photos and videos from iPhone, DJI Pocket 3, and other devices:

```bash
# Activate environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Scan and analyze media files
python organize_media.py /path/to/your/vacation/photos

# Alternative: Scan with debug information
python organize_media.py /path/to/media --debug-level 2

# Skip already processed files for incremental updates
python organize_media.py /path/to/media --skip-existing
```

**What happens during scanning:**
- **Reads UTC creation_time** from EXIF UserComment field (set by PreImport processor)
- **Fallback metadata extraction**: Creation dates, GPS coordinates, and technical metadata from standard EXIF fields
- **Semantic analysis**: People counting, activity recognition, talking detection
- **GPS intelligence**: Assigns GPS coordinates from HEIC files to GPS-less DJI MP4 files from same day
- **Location identification**: Maps coordinates to cities/countries using geo.list database
- **File organization**: Creates organized directory structure with symbolic links
- **Database population**: Stores all metadata in SQLite database with UTC Zulu timestamps

### **2. Launch Web Application**

Start the Flask web server to access both viewing interfaces:

```bash
# Start the modern web application (recommended)
cd media_library_web/src
python main.py

# Application will be available at:
# http://localhost:5001 - Main Dashboard (index.html)
# http://localhost:5001/daily.html - Daily chronological view
# http://localhost:5001/city.html - City-based organization
# http://localhost:5001/special.html - Activity/scenery browsing
# http://localhost:5001/fixinfo.html - Advanced metadata editor with saved location feature

# Legacy application (older interface)
# python main.py  # http://localhost:5000
```

### **3. Web Interface Usage**

#### **Map View (Primary Interface)**
- **Interactive Map**: Click on markers to view media details
- **Geographic Clustering**: Markers group by location at different zoom levels
- **Advanced Filtering**: 
  - Date range selection with calendar pickers
  - City and country dropdowns (bilingual English/Chinese)
  - People count and talking detection filters
- **Modal Media Viewer**: Click thumbnails for full-resolution viewing
- **System Integration**: Open files directly in Preview, QuickTime, etc.
- **Unknown Location Highlighting**: Media items without GPS data display with darker yellow background for easy identification

#### **Daily View (Chronological Interface)**
- **Day Navigation**: Previous/Next buttons for chronological browsing
- **Display Modes**: Toggle between thumbnail grid and detailed list views
- **Thumbnail Sizing**: Adjustable small/medium/large thumbnail controls
- **Smart Defaults**: Automatically loads earliest media creation date
- **Sorting Options**: Toggle between newest-first and oldest-first ordering
- **UTC Zulu Display**: Shows creation times in YYYY-MM-DD hh:mm:ss AM/PM format using OffsetTime from config table

#### **Time Zone Management**
- **UTC Zulu Storage**: All creation times stored as standardized UTC Zulu format in database
- **Configurable Display**: Web interface converts UTC to local display time using OffsetTime config setting
- **Consistent Presentation**: All web pages display times in YYYY-MM-DD hh:mm:ss AM/PM format
- **TimeZone Labels**: Display shows configured timezone name (e.g., "Asia/Hong_Kong") for user reference
- **Mixed Timezone Support**: Handles media files from different original timezones consistently

#### **FixInfo View (Metadata Editor)**
- **Bulk Operations**: Select multiple media files for batch editing
- **Location Correction**: Update GPS coordinates and city/country information
- **Date/Time Modification**: Adjust creation timestamps while maintaining UTC consistency
- **Unknown Location Management**: Special tools for identifying and correcting files without location data
- **Auto-Unselect**: Automatically clears selections after successful bulk operations
- **Visual Indicators**: Darker yellow highlighting for items needing location data
- **Saved Location Workflow**: 
  - Click any media file to extract and save its GPS coordinates and location data
  - Saved location information persists in the interface for reuse
  - Apply saved location to multiple selected files with bulk operations
  - Enables efficient correction of media files missing GPS data using reference files
  - Modify button activates when either saved location values exist OR country/city selections are made

#### **FixInfo Saved Location Usage Example**

**Scenario**: You have some photos with GPS data and others from the same location without GPS data.

```
Step-by-step workflow:

1. Navigate to FixInfo page: http://localhost:5001/fixinfo.html
2. Select a date containing your media files
3. Click on a media file that HAS GPS coordinates (reference file)
   → System automatically saves the location data from this file
   → Location fields populate with: latitude, longitude, city, country
   
4. Select multiple media files that NEED location data (checkbox selection)
   → Files without GPS data show with darker yellow background for easy identification
   
5. Click "Modify Selected Files" button
   → Button is enabled because saved location values exist
   → Bulk applies the saved GPS coordinates and location to all selected files
   
6. After "Successfully updated X files" message:
   → All checkboxes automatically unselect for clean workflow
   → Updated files now display proper location information
```

**Benefits of Saved Location Feature:**
- **Efficiency**: One-click location extraction from reference files
- **Consistency**: Ensures accurate location data for grouped photos/videos
- **GPS Recovery**: Corrects media files that lost GPS data during transfer or processing
- **Batch Processing**: Apply location to multiple files simultaneously
- **Visual Feedback**: Unknown locations highlighted for easy identification

### **4. Incremental Updates**

Add new media files without reprocessing existing ones:

```bash
# Copy new photos to your media directory
# Then run incremental scan
python organize_media.py /path/to/media --skip-existing --debug-level 1
```

## API Endpoints

### **Media Data APIs**
- `GET /api/media` - Retrieve media with filtering parameters
- `GET /api/media/<id>` - Get specific media item details
- `GET /api/media/cities` - List all available cities (bilingual)
- `GET /api/media/countries` - List all available countries (bilingual)
- `GET /api/media/stats` - Get media collection statistics

### **Query Parameters**
- `start_date`, `end_date` - Date range filtering
- `city`, `country` - Location-based filtering
- `min_people`, `max_people` - People count filtering
- `has_talking` - Audio content filtering
- `limit`, `offset` - Pagination support

## Project Structure

```
vacation_media_organizer2/
├── PreImport_exif_file_processor.py  # File preparation and EXIF standardization
├── Main_scan_media.py         # Main scanning engine with timezone configuration
├── main.py                    # Flask application entry point (legacy - use media_library_web/)
├── database_manager.py        # Database operations and schema management
├── metadata_extractor.py      # ExifTool integration and metadata processing
├── semantic_analyzer.py       # YOLOv8 and audio analysis
├── organize_media.py          # Media scanning and organization (legacy)
├── geo_table_manager.py       # Geographic location database management
├── Tk_geo_translation_editor.py # GUI editor for geographic translations
├── geo.list                   # Geographic location database
├── *.csv                      # Translation databases (Chinese_City_en_translated.csv, etc.)
├── media_organizer.db         # SQLite database (created at runtime)
├── requirements.txt           # Python dependencies
├── media_library_web/         # Modern Flask web application
│   ├── src/
│   │   ├── main.py           # Flask application entry point
│   │   ├── models/           # SQLAlchemy data models
│   │   ├── routes/           # API route handlers
│   │   └── static/           # Web interface files
│   │       ├── index.html    # Main dashboard interface
│   │       ├── daily.html    # Daily chronological view
│   │       ├── city.html     # City-based organization view
│   │       ├── special.html  # Activity/scenery view
│   │       └── fixinfo.html  # Advanced metadata editing interface
│   └── requirements.txt      # Web application dependencies
├── bin/                      # Utility scripts
│   ├── dji_rename.py        # DJI file renaming utility
│   └── extractHEIF.py       # HEIF extraction tool
└── util/                     # Testing and development utilities
```

## Configuration

### **Database Configuration (config table)**
The system uses a `config` table to manage timezone and display settings:

```sql
-- Key configuration settings
OffsetTime: '+08:00'           -- Display timezone offset for web interface
TimeZone: 'Asia/Hong_Kong'     -- Display timezone name/location
base_directory: '/path/to/media'     -- Base media directory path
thumb_directory: '/path/to/thumbs'   -- Thumbnail cache directory
```

**Configuration Management:**
```bash
# Run Main_scan_media.py to configure timezone settings interactively
python Main_scan_media.py
# Prompts for:
# - Timezone offset for web display (e.g., '+08:00' for UTC+8)
# - Display location name (e.g., 'Asia/Hong_Kong', 'Toronto', 'ASIA Time')
```

### **Time Zone Display Format**
- **Database Storage**: UTC Zulu format (2025-03-15T14:30:25.123Z)
- **Web Display**: Local format using OffsetTime conversion
- **Example Conversion**:
  - Database: `2025-03-15T14:30:25.123Z` (UTC)
  - OffsetTime: `+08:00`
  - Web Display: `2025-03-15 10:30:25 PM` (converted to UTC+8)

### **Debug Levels**
- `--debug-level 0` - Silent operation
- `--debug-level 1` - Basic progress information
- `--debug-level 2` - Detailed processing information
- `--debug-level 3` - Verbose analysis details
- `--debug-level 4` - Complete debug output

### **Processing Options**
- `--skip-existing` - Skip already processed files
- `--force-update` - Reprocess existing files
- `--no-semantic` - Skip semantic analysis for faster processing

## Troubleshooting

### **Common Issues**
1. **ExifTool not found**: Ensure ExifTool is installed and in system PATH
2. **Database locked**: Close web interface before running organize_media.py
3. **Missing geo.list**: Download geographic database from provided source
4. **Slow processing**: Use `--skip-existing` for incremental updates
5. **Memory issues**: Process large collections in smaller batches

### **Performance Tips**
- Use SSD storage for better database performance
- Increase available RAM for large media collections
- Enable `--skip-existing` for regular updates
- Consider lower debug levels for production use

## License

This project is open-source and available under the MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository and create a feature branch
2. Ensure all tests pass and maintain code quality
3. Update documentation for new features
4. Submit pull request with detailed description

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing issues in the project repository
3. Create a new issue with detailed description and system information

### 3. Interacting with the Web Interface

*   **Map View:** Click on markers on the map to see media from specific locations. You can also click the button in the popup to filter the media gallery by that location.
*   **Media Gallery:** Browse your media files. Click on any media card to open a detailed preview modal.
*   **Filters:** Use the filter options (City, Country, Date Range, Has People, Talking Detected) to narrow down your media selection. Changes are applied automatically.

## File Structure of the Organized Library

Your media library will have a structure similar to this:

```
/media_library_destination
├── YYYY
│   ├── MM
│   │   ├── DD
│   │   │   ├── photo_001.jpg
│   │   │   ├── video_001.mp4
│   │   │   └── ...
├── OrganizedBy
│   ├── Location
│   │   ├── CityName_CountryName
│   │   │   ├── photo_001.jpg (symbolic link)
│   │   │   └── video_001.mp4 (symbolic link)
│   ├── Scenery
│   │   ├── Hiking
│   │   │   ├── photo_003.jpg (symbolic link)
│   │   │   └── video_002.mp4 (symbolic link)
│   │   └── CityWalk
│   │       └── ...
├── media_library.db
└── (other project files like `metadata_extractor.py`, `semantic_analyzer.py`, `main.py`, `media_library_web/` etc.)
```

## Troubleshooting

*   **ExifTool not found:** Ensure ExifTool is installed and its executable is in your system's PATH. Restart your terminal after installation.
*   **`ModuleNotFoundError`:** Make sure your Python virtual environment is activated and all dependencies are installed (`pip install -r requirements.txt`).
*   **Symlink errors on Windows:** On Windows, creating symbolic links might require administrator privileges. Run your terminal or command prompt as an administrator.
*   **Map not loading:** Check your internet connection. The map tiles are loaded from OpenStreetMap.
*   **Media files not playing/displaying:** Ensure the `new_path` entries in your `media_library.db` correctly point to the media files. Check browser console for errors.
*   **Slow video analysis:** Semantic video analysis can be computationally intensive. Performance will depend on your system's hardware (especially GPU if available and configured for `ultralytics`).

For further assistance, please refer to the project's source code or open an issue on the project's GitHub page.

## Keep journal table

* `sqlite3 media_organizer.db ".dump journal" > journal_backup.sql`
* `sqlite3 media_organizer.db < journal_backup.sql`

