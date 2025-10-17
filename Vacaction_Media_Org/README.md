# Vacation Media Organizer: Smart Photo & Video Management System

## Overview

A comprehensive, Flask-based web application for organizing and exploring vacation photos and videos with intelligent metadata extraction, semantic analysis, and dual-view interfaces for enhanced media browsing.

## Latest Implementation (October 2025)

### **Dual-Interface Web Application**
- **Map View**: Interactive map-based media exploration with clustering and filtering
- **Daily View**: Chronological day-by-day media browsing with flexible display modes

### **Smart Media Organization**
- **Automated Metadata Extraction**: Creation time, GPS coordinates, file size, and technical details
- **Semantic Analysis**: People detection, activity recognition, talking detection, and scenery classification
- **Location Intelligence**: Bilingual city/country support (English + Chinese) with geographic clustering
- **Database-Driven**: SQLite backend with comprehensive media indexing and relationship management

### **Advanced User Experience**
- **Responsive Design**: Mobile-friendly interface with gradient themes and modern UI components
- **Interactive Features**: Clickable thumbnails, detailed modal views, and system file integration
- **Flexible Filtering**: Date ranges, location dropdowns, people count, and talking detection filters
- **Sorting Controls**: Chronological ordering with user-toggleable newest/oldest first options

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

### **1. Initial Media Scanning**

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
- Extracts creation dates, GPS coordinates, and technical metadata
- Performs semantic analysis (people counting, activity recognition)
- Assigns GPS coordinates from HEIC files to DJI MP4 files from same day
- Identifies cities/countries using geo.list database
- Creates organized directory structure with symbolic links
- Populates SQLite database with all metadata

### **2. Launch Web Application**

Start the Flask web server to access both viewing interfaces:

```bash
# Start the application
python main.py

# Application will be available at:
# http://localhost:5000 - Map View interface
# http://localhost:5000/daily - Daily View interface
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

#### **Daily View (Chronological Interface)**
- **Day Navigation**: Previous/Next buttons for chronological browsing
- **Display Modes**: Toggle between thumbnail grid and detailed list views
- **Thumbnail Sizing**: Adjustable small/medium/large thumbnail controls
- **Smart Defaults**: Automatically loads earliest media creation date
- **Sorting Options**: Toggle between newest-first and oldest-first ordering

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
├── main.py                    # Flask application entry point
├── database_manager.py        # Database schema and operations
├── metadata_extractor.py      # ExifTool and metadata processing
├── semantic_analyzer.py       # YOLOv8 and audio analysis
├── organize_media.py          # Media scanning and organization
├── geo.list                   # Geographic location database
├── media_organizer.db         # SQLite database (created at runtime)
├── requirements.txt           # Python dependencies
├── static/
│   ├── index.html            # Map View interface
│   └── daily.html            # Daily View interface
└── media/                    # Organized media files (created at runtime)
```

## Configuration

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

## Author

Manus AI

