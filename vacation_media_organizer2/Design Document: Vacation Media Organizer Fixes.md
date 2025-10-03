# Design Document: Vacation Media Organizer Fixes

This document outlines the design for addressing the identified implementation issues in the vacation media organizer solution. Each issue will be analyzed, and a proposed solution will be detailed, including technical specifications and rationale.

## 1. DIRECTORY SCANNING ISSUE

**Problem Description:** The `main.py` file currently only scans the immediate directory, failing to traverse subdirectories for media files. This limits the utility of the organizer for hierarchical file structures.

**Proposed Solution:**

To enable comprehensive scanning, the `os.walk()` function from Python's `os` module will be implemented. `os.walk()` generates the file names in a directory tree by walking the tree either top-down or bottom-up, making it ideal for recursive directory traversal [1].

**Technical Details:**

*   The `scan_directory` function in `main.py` will be refactored to use `os.walk()`. It will iterate through all directories and subdirectories, collecting paths to all files.
*   A list of all absolute file paths will be returned, which can then be processed by the metadata extraction logic.

**Rationale:** `os.walk()` is the standard and most efficient way in Python to recursively list files and directories. It handles directory traversal robustly and is well-suited for this task.

## 2. FILE TYPE HANDLING

**Problem Description:** The `metadata_extractor.py` file, specifically the `ImageMetadata()` function, omits `.heic` files, leading to these media files not being processed.

**Proposed Solution:**

The `ImageMetadata()` function will be updated to explicitly recognize and process `.heic` file extensions.

**Technical Details:**

*   Modify the `ImageMetadata()` function to include `'.heic'` in the list of recognized image extensions.
*   Ensure that the metadata extraction logic for `.heic` files is consistent with other image types, potentially leveraging a robust metadata extraction library like `ExifTool` for comprehensive support.

**Rationale:** Including `.heic` ensures that a common modern image format is properly handled, preventing data loss and improving the completeness of the media library.

## 3. USER CONFIGURATION OPTIONS

**Problem Description:** The current solution lacks clear mechanisms for user configuration, specifically for setting the scanning debug level and opting to skip already scanned files.

**Proposed Solution:**

User configuration will be managed through command-line arguments using Python's `argparse` module for immediate settings and potentially a configuration file for persistent or more complex options.

**Technical Details:**

*   **Command-Line Arguments (`argparse`):**
    *   Add an argument for `debug_level` (e.g., `--debug-level <level>`), allowing users to specify the verbosity of logging. Levels could include `INFO`, `DEBUG`, `WARNING`, `ERROR`.
    *   Add a boolean argument for `skip_scanned` (e.g., `--skip-scanned`), which, when present, instructs the program to check a record of previously scanned files and skip them.
*   **Configuration File (Optional, for future expansion):** For more advanced settings, a `config.ini` or `config.json` file could be introduced, parsed using `configparser` or `json` modules, respectively. This would allow for default values and more complex configurations.
*   **Implementation:** The `main.py` will be updated to parse these arguments and pass them to relevant functions.

**Rationale:** `argparse` provides a robust and user-friendly way to handle command-line options, making the application more flexible and controllable. Skipping already scanned files improves efficiency for subsequent runs.

## 4. GEO.LIST INTEGRATION

**Problem Description:** The program currently does not properly read and utilize the `geo.list` file to enrich photo metadata with City, Region, Subregion, CountryCode, and Country information.

**Proposed Solution:**

Implement a mechanism to read and parse the `geo.list` file. This file is assumed to contain geographical data that can be mapped to media files based on their GPS coordinates. The `ExifTool` utility, which has robust geolocation features, will be leveraged for this purpose [2].

**Technical Details:**

*   **`geo.list` Format:** Assume `geo.list` contains entries that map GPS coordinates or broader geographical areas to specific location names (City, Region, etc.). The exact format needs to be defined or inferred. For this design, we will assume a simple CSV-like format or a custom format that `ExifTool` can consume.
*   **ExifTool Integration:**
    *   The system will need `ExifTool` installed. A Python wrapper (e.g., `PyExifTool`) or direct subprocess calls will be used to interact with `ExifTool`.
    *   When processing a media file with GPS coordinates, `ExifTool` will be invoked with the `geo.list` file to determine the City, Region, Subregion, CountryCode, and Country.
    *   Example `ExifTool` command for geotagging: `exiftool -geotag geo.list -overwrite_original <media_file>` (This is for writing, for reading, we'd extract the relevant tags).
*   **Parsing Output:** The output from `ExifTool` will be parsed to extract the required geo-information.

**Rationale:** `ExifTool` is an industry-standard tool for metadata manipulation, including advanced geolocation features. Integrating it ensures accurate and comprehensive geo-tagging based on external data sources like `geo.list`.

## 5. DATABASE SCHEMA ISSUES

**Problem Description:** The SQLite database schema lacks fields for detailed geographical information (City, Region, Subregion, CountryCode, and Country), which are crucial for organizing vacation media.

**Proposed Solution:**

Update the SQLite database schema to include dedicated columns for City, Region, Subregion, CountryCode, and Country in the relevant media table (e.g., `media_files`).

**Technical Details:**

*   **Schema Modification:** Add the following columns to the `media_files` table (or equivalent):
    *   `city TEXT`
    *   `region TEXT`
    *   `subregion TEXT`
    *   `country_code TEXT`
    *   `country TEXT`
*   **Database Migration:** Implement a simple migration script or logic to add these columns if they do not exist, preserving existing data.
*   **Data Insertion/Update:** Modify the data insertion/update logic to populate these new fields with information extracted from media files and `geo.list`.

**Rationale:** A well-defined database schema is fundamental for data integrity and efficient querying. Including these geo-specific fields directly in the database allows for powerful filtering, sorting, and organization of media based on location.

## 6. METADATA SHARING

**Problem Description:** The program does not effectively share geo-information from `.heic` or other image files with associated MP4 files in the SQLite database.

**Proposed Solution:**

Implement a metadata sharing mechanism where geo-information extracted from images (especially `.heic` files) can be propagated to MP4 files that are determined to be taken at the same location and time, or are otherwise related.

**Technical Details:**

*   **Correlation Logic:** Develop a heuristic to correlate image and video files. This could involve:
    *   **Timestamp Proximity:** If an MP4 file was recorded within a certain time window (e.g., 5 minutes) of an image being taken, and they are in the same directory, they might be related.
    *   **Filename Patterns:** Look for common naming conventions (e.g., `IMG_XXXX.HEIC` and `VID_XXXX.MP4`).
    *   **GPS Proximity:** If both have GPS data, check if their coordinates are very close.
*   **Propagation:** Once a correlation is established, the detailed geo-information (City, Region, etc.) extracted from the image will be used to update the corresponding MP4 entry in the database.
*   **ExifTool for Writing (Optional but Recommended):** For consistency, consider using `ExifTool` to *write* the extracted geo-metadata directly into the MP4 file's XMP tags, in addition to updating the database. This ensures the metadata is embedded in the file itself.

**Rationale:** Sharing metadata across related media files enhances the richness of the data for all assets. It addresses cases where videos might lack detailed geo-tags but can infer them from nearby images, leading to a more complete and searchable media collection.
