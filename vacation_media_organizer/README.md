# Vacation Media Organizer: Smart Photo & Video Management

## Introduction

This solution provides a comprehensive, cross-platform system for organizing your vacation photos and videos from devices like iPhone and DJI Pocket 3. It automates the process of extracting metadata, performing semantic video analysis, organizing files by creation date, and creating intelligent links for location and scenery-based browsing. A local web-based interface allows for intuitive exploration, filtering, and playback of your media.

## Features

*   **Cross-Platform Compatibility:** Designed to run on both Windows and macOS/Linux.
*   **Automated Ingestion:** Downloads and organizes media files from source directories.
*   **Rich Metadata Extraction:** Extracts creation date, time, and geographic location (latitude, longitude, city, country) from photos and videos.
*   **Semantic Video Analysis:**
    *   **People Detection:** Counts the number of people present in video frames.
    *   **Activity Recognition:** Identifies activities like walking in videos.
    *   **Voice Activity Detection:** Detects segments where talking occurs.
    *   **Scenery Classification:** Categorizes video scenery (e.g., city walk, hiking).
*   **Intelligent File Organization:**
    *   Primary organization by creation date into `YYYY/MM/DD` subdirectories.
    *   Secondary organization using symbolic links by city/country and semantic categories (e.g., `OrganizedBy/Location/Paris_France`, `OrganizedBy/Scenery/Hiking`).
*   **Local Database:** Stores all extracted metadata and analysis results in a SQLite database for efficient querying.
*   **Interactive Web Interface:**
    *   Displays media locations on an interactive map (Google Maps or AMap compatible).
    *   Allows filtering and sorting media by date, date range, location, people count, and semantic categories.
    *   Provides in-browser preview and playback of media files.

## System Requirements

*   **Operating System:** Windows 10/11, macOS, or Linux.
*   **Python:** Python 3.8 or higher.
*   **ExifTool:** The `exiftool` command-line application must be installed and accessible in your system's PATH. This is crucial for robust metadata extraction, especially from video files.
    *   [Install ExifTool](https://exiftool.org/install.html)
*   **Internet Connection:** Required for initial setup (downloading Python packages, YOLO model, Silero VAD model) and for reverse geocoding (using Nominatim).

## Installation

Follow these steps to set up the media organizer on your system.

### 1. Install ExifTool

Ensure ExifTool is installed on your system. Refer to the [official ExifTool website](https://exiftool.org/install.html) for detailed instructions specific to your operating system.

### 2. Clone the Repository (or download files)

Assuming you have Git installed, clone the project:

```bash
git clone <repository_url> # Replace with actual repository URL if available
cd vacation-media-organizer # Or the directory where you downloaded the files
```

### 3. Set up Python Environment

It's highly recommended to use a virtual environment to manage dependencies.

**For macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**For Windows (Command Prompt):**

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Note:** The `requirements.txt` file will be generated during the packaging phase. For now, you will need to manually install the dependencies used in the backend development phase:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Ingest and Organize Media Files

First, you need to process your raw media files. Copy all your photos and videos from your iPhone and DJI Pocket 3 into a single source directory.

**For macOS/Linux:**

```bash
source venv/bin/activate
python organize_media.py /path/to/your/raw_media_folder /path/to/your/media_library_destination
```

**For Windows (Command Prompt):**

```cmd
venv\Scripts\activate
python organize_media.py C:\path\to\your\raw_media_folder C:\path\to\your\media_library_destination
```

*   Replace `/path/to/your/raw_media_folder` with the actual path to your unorganized media files.
*   Replace `/path/to/your/media_library_destination` with the desired root directory for your organized media library.

This script will:
*   Extract metadata and perform semantic analysis.
*   Move files into a date-based directory structure.
*   Create symbolic links for location and scenery-based browsing.
*   Populate the `media_library.db` SQLite database with all media information.

### 2. Run the Web Interface

After organizing your media, you can start the local web server to browse your library.

**For macOS/Linux:**

```bash
./run_backend.sh
```

**For Windows (Command Prompt):**

```cmd
run_backend.bat
```

Once the server is running, open your web browser and navigate to `http://127.0.0.1:5000` (or the address displayed in the console).

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

