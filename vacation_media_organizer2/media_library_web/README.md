# 📸 Vacation Media Library - Web Interface

A Flask-based web application for browsing and managing your vacation media files with advanced filtering, interactive mapping, and system integration.

## 🎯 Features

### 📱 **Interactive Web Interface**
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Filtering**: Filter by city, country, date range, people count, talking detection
- **Statistics Dashboard**: Live counts of total media, location-tagged files, etc.

### 🗺️ **Interactive Map**
- **Leaflet.js Integration**: Interactive world map with media locations
- **Clustered Markers**: Group nearby media files with counts
- **Popup Details**: Hover over markers to see file information
- **Click to Open**: Direct system integration to open files with default applications

### 🔍 **Advanced Search & Filtering**
- **Location-based**: Search by city names (English/Chinese)
- **Time-based**: Date and time range filtering with datetime-local inputs
- **Content-based**: Filter by people count and talking detection
- **Real-time Updates**: Map and gallery update instantly with filters

### 💻 **System Integration**
- **Native File Opening**: Click map markers or modal buttons to open files with system default apps
- **Cross-platform Support**: macOS (open), Windows (startfile), Linux (xdg-open)
- **Media Preview**: In-browser image and video preview with full controls

## 🏗️ Architecture

### **Database Schema** (from `scan_main.py`)
```sql
CREATE TABLE media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    file_type TEXT,
    size INTEGER,
    creation_time TEXT,
    latitude REAL,
    longitude REAL,
    city_en TEXT,           -- English city name
    city_zh TEXT,           -- Chinese city name  
    region_en TEXT,
    region_zh TEXT,
    subregion_en TEXT,
    subregion_zh TEXT,
    country_code TEXT,
    country_en TEXT,
    country_zh TEXT,
    timezone TEXT,
    people_count INTEGER DEFAULT 0,
    activities TEXT,        -- JSON string
    scenery TEXT,          -- JSON string
    talking_detected BOOLEAN DEFAULT 0,
    scanned_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### **API Endpoints**
```
GET  /api/media              → All media with filtering
GET  /api/media/{id}         → Individual media details
GET  /api/media/{id}/file    → Serve media file
POST /api/media/{id}/open    → Open file with system app
GET  /api/media/stats        → Summary statistics
GET  /api/media/locations    → Unique locations with counts
```

## 🚀 Quick Start

### **1. Prerequisites**
```bash
# Make sure you have Python 3.7+ installed
python3 --version

# Ensure you have media data in the database
cd /path/to/vacation_media_organizer2
python scan_main.py /path/to/your/media/directory
```

### **2. Start the Web Server**
```bash
cd vacation_media_organizer2/media_library_web
./start_server.sh
```

### **3. Open in Browser**
```
http://localhost:5001
```

## 📋 Manual Setup

### **1. Install Dependencies**
```bash
cd vacation_media_organizer2/media_library_web
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-SQLAlchemy
```

### **2. Verify Database**
```bash
# Check database exists
ls -la ../media_organizer.db

# If not, scan your media first
cd ..
python scan_main.py /path/to/media/directory
```

### **3. Start Flask App**
```bash
cd media_library_web
python src/main.py
```

## 🎨 Web Interface Guide

### **🗺️ Map Interaction**
1. **View Locations**: Media locations appear as markers on the world map
2. **Hover for Details**: Mouse over markers to see popup with file information
3. **Open Files**: Click "Open File" buttons in popups to launch system media apps
4. **Filter by Location**: Click "Show all media from this location" to filter gallery

### **🔍 Filtering Options**
- **City/Country**: Type partial names (supports English and Chinese)
- **Date Range**: Use datetime-local inputs for precise time filtering
- **People Detection**: Show only media with/without detected people
- **Talking Detection**: Filter by detected speech in videos

### **📱 Gallery Features**
- **Media Cards**: Thumbnail previews with metadata tags
- **Click to View**: Open detailed modal with full-size preview
- **System Integration**: "Open with System App" button in modals
- **Real-time Updates**: Gallery refreshes instantly with filter changes

## 🛠️ Debugging & Development

### **VS Code Debugging**
The project includes VS Code debug configuration in `.vscode/launch.json`:
```json
{
    "name": "Python: Flask Media Library",
    "type": "debugpy",
    "request": "launch",
    "program": "vacation_media_organizer2/media_library_web/src/main.py",
    "cwd": "vacation_media_organizer2/media_library_web"
}
```

**To debug:**
1. Open `main.py` in VS Code
2. Press `F5`
3. Select "Python: Flask Media Library"
4. Set breakpoints and debug interactively

### **Common Issues**

#### **Database Not Found**
```bash
# Error: Database file doesn't exist
# Solution: Run scan_main.py first
python scan_main.py /path/to/media
```

#### **No Media Displayed**
```bash
# Check database has data
sqlite3 media_organizer.db "SELECT COUNT(*) FROM media_files;"
```

#### **Files Won't Open**
- **macOS**: Requires `open` command (built-in)
- **Windows**: Uses `os.startfile()` (built-in)
- **Linux**: Requires `xdg-open` (usually pre-installed)

#### **Port Already in Use**
```bash
# Change port in main.py line 43
app.run(host='0.0.0.0', port=5002, debug=True)  # Change 5001 to 5002
```

## 📊 Data Flow

```
1. scan_main.py → SQLite Database (media_organizer.db)
                       ↓
2. Flask App (main.py) → SQLAlchemy Models (media.py)
                       ↓
3. API Routes (media.py) → JSON Responses
                       ↓
4. HTML/JavaScript → Interactive Web Interface
                       ↓
5. System Integration → Native Media Apps
```

## 🎯 Key Features in Detail

### **Smart Filtering**
- **Multilingual Support**: Searches both English and Chinese location names
- **Flexible Date Handling**: Supports various datetime formats from metadata
- **Real-time Results**: No page refresh needed, instant visual feedback

### **Map Integration**
- **Clustering**: Multiple files at same location show combined marker
- **Rich Popups**: File details, thumbnails, and action buttons
- **Auto-fit**: Map automatically zooms to show all available media locations

### **System Integration**
- **Cross-platform**: Works on macOS, Windows, and Linux
- **Native Apps**: Opens files with default system applications (Photos, QuickTime, etc.)
- **Error Handling**: Graceful fallbacks when system integration fails

This web interface provides a comprehensive solution for browsing and managing vacation media with professional-grade features and seamless system integration.