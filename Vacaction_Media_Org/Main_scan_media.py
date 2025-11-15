#!python
import os
import sys
import argparse
import logging
import sqlite3
from datetime import datetime               
from metadata_extractor import MetadataExtractor
import subprocess

# Optional imports for thumbnail generation
try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Thumbnail generation will be skipped.")

# Configure logging with both console and file output
def setup_logging(debug=False):
    """Setup logging configuration for the application"""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Clear any existing handlers to avoid duplication
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler('Main_media_organizer.log', mode='a')  # File output
        ],
        force=True  # Force reconfiguration
    )
    
    # Add debug file handler for metadata extraction details when in debug mode
    if debug:
        debug_handler = logging.FileHandler('metadata_extraction_debug.log', mode='a')
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debug_handler.setFormatter(debug_formatter)
        
        # Add to metadata_extractor logger specifically
        metadata_logger = logging.getLogger('metadata_extractor')
        metadata_logger.setLevel(logging.DEBUG)  # Ensure the logger level is set
        metadata_logger.addHandler(debug_handler)

# Setup basic logging (will be enhanced by setup_logging() if needed)
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(levelname)s - %(message)s')

def parse_datetime_flexible(datetime_str):
    """
    Parse datetime string supporting multiple formats:
    - Old format: YYYY-MM-DD HH:MM:SS
    - Old timezone format: YYYY-MM-DD hh:mm:ss±##.##
    - New ISO 8601 format: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
    
    Returns datetime object (timezone-naive for consistency in calculations)
    """
    if not datetime_str:
        return None
        
    try:
        # Handle ISO 8601 format first (new format from metadata extractor)
        if 'T' in datetime_str:
            # ISO 8601: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
            # Remove timezone for consistent calculations
            if '+' in datetime_str:
                datetime_part = datetime_str.split('+')[0]
            elif datetime_str.count('-') > 2:  # Has timezone
                datetime_part = datetime_str.rsplit('-', 1)[0]
            else:
                datetime_part = datetime_str
            
            # Try with subseconds first, then without
            try:
                return datetime.strptime(datetime_part, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                return datetime.strptime(datetime_part, '%Y-%m-%dT%H:%M:%S')
        
        # Handle old timezone format: YYYY-MM-DD hh:mm:ss±##.##
        elif ('+' in datetime_str or datetime_str.count('-') >= 3):
            # Split on the last '+' or '-' to separate time from timezone
            if '+' in datetime_str:
                time_part = datetime_str.rsplit('+', 1)[0]
            else:
                time_part = datetime_str.rsplit('-', 1)[0]
            return datetime.strptime(time_part, '%Y-%m-%d %H:%M:%S')
        
        # Handle old format: YYYY-MM-DD HH:MM:SS
        else:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            
    except (ValueError, TypeError) as e:
        logging.debug(f"Error parsing datetime '{datetime_str}': {e}")
        return None

# -------------------------------------------------------------------------------
class MediaOrganizerDB:
    # Use the media_organizer.db SQLite database in the current directory
    def __init__(self, rescan=False, db_path='media_organizer.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.rescan = rescan
        self.add_media_file_count = 0

        if self.rescan and os.path.exists(self.db_path):
            logging.info(f"Rescan requested. Deleting existing database: {self.db_path}")
            os.remove(self.db_path)

        self._connect()
        self._create_table()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logging.debug(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            sys.exit(1)

    def _create_table(self):
        # if media_files table does not exist, create it with geo fields
        # Otherwise skip the creation
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    file_extension TEXT NOT NULL,
                    file_type TEXT,
                    size INTEGER,
                    creation_time TEXT,
                    latitude REAL,
                    longitude REAL,
                    city_en TEXT,
                    city_zh TEXT,
                    region_en TEXT,
                    region_zh TEXT,
                    subregion_en TEXT,
                    subregion_zh TEXT,
                    country_code TEXT,
                    country_en TEXT,
                    country_zh TEXT,
                    timezone TEXT,
                    people_count INTEGER DEFAULT 0,
                    activities TEXT,
                    scenery TEXT,
                    talking_detected BOOLEAN DEFAULT 0,
                    hasGPS BOOLEAN DEFAULT 0,
                    shareGPS BOOLEAN DEFAULT 0,
                    scanned_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create geo table for storing all geographical data from geo_chinese.list
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS geo_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_en TEXT NOT NULL,
                    city_zh TEXT NOT NULL,
                    region_en TEXT,
                    region_zh TEXT,
                    subregion_en TEXT,
                    subregion_zh TEXT,
                    country_code TEXT NOT NULL,
                    country_en TEXT NOT NULL,
                    country_zh TEXT NOT NULL,
                    timezone TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(city_en, country_en, latitude, longitude)
                )
            ''')
            
            # Create index for faster geo lookups
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_coords ON geo_data (latitude, longitude)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_geo_city_country ON geo_data (city_en, country_en)
            ''')
            
            # Create config table for storing application configuration
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster config lookups
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_config_key ON config (key)
            ''')
            
            # Insert default configuration values if they don't exist
            default_configs = [
                ('offsetTime', '+08:00', 'Web server display timezone offset for converting UTC creation_time to local display time'),
                ('displayTime', 'ASIA Time', 'Web server display timezone location name shown in views')
            ]
            
            for key, value, description in default_configs:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO config (key, value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, description))
            
            self.conn.commit()
            logging.debug("Media files, geo, and config tables ensured to exist with geo fields.")
        except sqlite3.Error as e:
            # If media_files table exists, skip creation, no need to exit
            logging.error(f"Warning creating table: {e}")
            # sys.exit(1)

    def get_relative_path(self, absolute_path, base_directory):
        """Convert absolute path to relative path from base directory."""
        try:
            # Ensure both paths are absolute
            absolute_path = os.path.abspath(absolute_path)
            base_directory = os.path.abspath(base_directory)
            
            # Get relative path
            relative_path = os.path.relpath(absolute_path, base_directory)
            
            # If the file is not under base_directory, return the original path
            if relative_path.startswith('..'):
                logging.warning(f"File {absolute_path} is not under base directory {base_directory}")
                return absolute_path
                
            return relative_path
        except Exception as e:
            logging.error(f"Error converting path to relative: {e}")
            return absolute_path

    def get_absolute_path(self, relative_path, base_directory):
        """Convert relative path to absolute path using base directory."""
        try:
            # If the path is already absolute, return it
            if os.path.isabs(relative_path):
                return relative_path
            
            # Combine base directory with relative path
            absolute_path = os.path.join(base_directory, relative_path)
            return os.path.normpath(absolute_path)
        except Exception as e:
            logging.error(f"Error converting relative path to absolute: {e}")
            return relative_path

    def file_exists(self, filepath, base_directory=None):
        """Check if file exists in database using relative path."""
        if base_directory:
            # Convert absolute path to relative for database lookup
            relative_path = self.get_relative_path(filepath, base_directory)
        else:
            relative_path = filepath
            
        self.cursor.execute(
            'SELECT 1 FROM media_files WHERE filepath = ?', (relative_path,))
        return self.cursor.fetchone() is not None

    def add_media_file(self, metadata, base_directory=None):
        # logging.info(f"Adding media file to DB: {metadata.get('filepath')}, {metadata.get('creation_time')}")
        try:
            # Convert absolute path to relative path if base_directory is provided
            original_filepath = metadata.get('filepath')
            if base_directory and original_filepath:
                relative_filepath = self.get_relative_path(original_filepath, base_directory)
                metadata_to_store = metadata.copy()
                metadata_to_store['filepath'] = relative_filepath
            else:
                metadata_to_store = metadata
                relative_filepath = original_filepath

            # Determine hasGPS based on presence of latitude and longitude
            has_gps = bool(metadata_to_store.get('latitude') and metadata_to_store.get('longitude'))
            
            # Normalize creation_time to always have 'Z' suffix for UTC times
            creation_time = metadata_to_store.get('creation_time')
            file_ext = metadata_to_store.get('file_extension', '').lower()
            
            # Define file types based on actual input directory content and their timestamp behavior
            # Files that have UTC timestamps WITH 'Z' suffix
            utc_with_z_types = {'.mp4', '.mov', '.heic'}
            # Files that have UTC timestamps WITHOUT 'Z' suffix (need Z added for consistency)
            utc_without_z_types = {'.png', '.jpg', '.jpeg'}
            
            if creation_time and not creation_time.endswith('Z'):
                # Add Z suffix for UTC times that don't have it
                if 'T' in creation_time and not ('+' in creation_time or creation_time.count('-') > 2):
                    if '.' not in creation_time:
                        creation_time += '.000Z'
                    else:
                        creation_time += 'Z'
                elif ':' in creation_time and ' ' in creation_time and 'T' not in creation_time:
                    # Convert EXIF format to ISO format with Z
                    date_part, time_part = creation_time.split(' ', 1)
                    iso_date = date_part.replace(':', '-')
                    if '.' not in time_part:
                        time_part += '.000'
                    creation_time = f"{iso_date}T{time_part}Z"
                metadata_to_store['creation_time'] = creation_time
                
                # Log info about file type and timestamp handling
                if file_ext in utc_with_z_types:
                    logging.info(f"UTC timestamp (already has Z) for {file_ext} file: {metadata_to_store.get('filepath')}")
                elif file_ext in utc_without_z_types:
                    logging.info(f"UTC timestamp (Z added for consistency) for {file_ext} file: {metadata_to_store.get('filepath')}")
                else:
                    logging.info(f"Timestamp normalized for unknown {file_ext} file: {metadata_to_store.get('filepath')}")
            
            self.cursor.execute('''
                INSERT INTO media_files (
                    filepath, filename, file_extension, file_type, size, creation_time, latitude, longitude,
                    city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone,
                    hasGPS, shareGPS
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata_to_store.get('filepath'),
                metadata_to_store.get('filename'),
                metadata_to_store.get('file_extension'),
                metadata_to_store.get('file_type'),
                metadata_to_store.get('size'),
                metadata_to_store.get('creation_time'),
                metadata_to_store.get('latitude'),
                metadata_to_store.get('longitude'),
                metadata_to_store.get('city_en'),
                metadata_to_store.get('city_zh'),
                metadata_to_store.get('region_en'),
                metadata_to_store.get('region_zh'),
                metadata_to_store.get('subregion_en'),
                metadata_to_store.get('subregion_zh'),
                metadata_to_store.get('country_code'),
                metadata_to_store.get('country_en'),
                metadata_to_store.get('country_zh'),
                metadata_to_store.get('timezone'),
                1 if has_gps else 0,  # hasGPS
                0  # shareGPS (default to False/0)
            ))
            self.conn.commit()
            self.add_media_file_count += 1
            logging.info(f"Added media file ({self.add_media_file_count}): {relative_filepath}, {metadata.get('creation_time')}")
            
            # Generate thumbnail after successfully adding to database
            # Use original absolute path for file operations
            if original_filepath and os.path.exists(original_filepath):
                # Generate thumbnail using configured directories
                generated_thumbnail_path = self.generate_thumbnail(original_filepath, base_directory=base_directory)
                if generated_thumbnail_path:
                    logging.info(f"Generated new thumbnail: {generated_thumbnail_path}")
                else:
                    logging.debug(f"Thumbnail generation skipped or failed for: {original_filepath}")
                    
        except sqlite3.IntegrityError:
            logging.debug(f"File already exists in DB, skipping: {metadata.get('filepath')}")
        except sqlite3.Error as e:
            logging.error(f"Error adding media file to DB: {e}")

    def update_city_translation(self, filepath, extractor, base_directory=None):
        try:
            # Convert to relative path for database operations
            if base_directory:
                relative_filepath = self.get_relative_path(filepath, base_directory)
            else:
                relative_filepath = filepath
                
            #logging.info(f"City translation from DB {relative_filepath}")
            city_en = None
            city_zh = None
            meta_city_zh = None
            self.cursor.execute('''
                SELECT filepath, city_en, city_zh, country_en FROM media_files
                WHERE filepath = ?
            ''', (relative_filepath,))
            result = self.cursor.fetchone()
            if result:
                city_en = result[1]
                city_zh = result[2]
                country_en = result[3]

            #logging.info(f"   From DB: city_en: {city_en}, city_zh: {city_zh}, country_en: {country_en}")

            if city_en:
                meta_city_zh = extractor._get_city_translation(city_en, country_en)

            #logging.info(f"   Retrieved translation    city_en: {city_en}, country_en: {country_en} -> meta_city_zh: {meta_city_zh}")

            if meta_city_zh and meta_city_zh != city_zh:
                #logging.info(f"   Found new city translation meta_city_zh: {meta_city_zh}, updateing database.")
                self.cursor.execute('''
                    UPDATE media_files
                    SET city_zh = ?
                    WHERE filepath = ?
                ''', (meta_city_zh, relative_filepath))
                self.conn.commit()
                logging.info(f"Updated DB file {relative_filepath}:\n > city_en: {city_en}, city_zh: {city_zh} -> meta_city_zh: {meta_city_zh}")
            #else:
            #    logging.info(f"   No update required for city translation: city_en: {city_en}, city_zh: {city_zh}, meta_city_zh: {meta_city_zh}\n")

        except sqlite3.Error as e:
            logging.error(f"Error updating city translation for {filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {filepath}")

    # TODO: update shareGPS ?
    def update_media_file_geo(self, filepath, geo_data, base_directory=None):
        try:
            # Convert to relative path for database operations
            if base_directory:
                relative_filepath = self.get_relative_path(filepath, base_directory)
            else:
                relative_filepath = filepath
                
            self.cursor.execute('''
                UPDATE media_files
                SET city_en = ?, city_zh = ?, region_en = ?, region_zh = ?, subregion_en = ?, subregion_zh = ?,
                    country_code = ?, country_en = ?, country_zh = ?, timezone = ?
                WHERE filepath = ?
            ''', (
                geo_data.get('city_en'),
                geo_data.get('city_zh'),
                geo_data.get('region_en'),
                geo_data.get('region_zh'),
                geo_data.get('subregion_en'),
                geo_data.get('subregion_zh'),
                geo_data.get('country_code'),
                geo_data.get('country_en'),
                geo_data.get('country_zh'),
                geo_data.get('timezone'),
                relative_filepath
            ))
            self.conn.commit()
            logging.debug(f"Updated geo data for {relative_filepath}")
        except sqlite3.Error as e:
            logging.error(f"Error updating geo data for {relative_filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {relative_filepath}")

    # Update media file activities and scenery
    def update_media_file_semantic(self, filepath, semantic_data, base_directory=None):
        try:
            # Convert to relative path for database operations
            if base_directory:
                relative_filepath = self.get_relative_path(filepath, base_directory)
            else:
                relative_filepath = filepath
                
            self.cursor.execute('''
                UPDATE media_files
                SET people_count = ?, activities = ?, scenery = ?, talking_detected = ?
                WHERE filepath = ?
            ''', (
                semantic_data.get('people_count', 0),
                semantic_data.get('activities', ''),
                semantic_data.get('scenery', ''),
                semantic_data.get('talking_detected', 0),
                relative_filepath
            ))
            self.conn.commit()
            logging.debug(f"Updated semantic data for {relative_filepath}")
        except sqlite3.Error as e:
            logging.error(f"Error updating semantic data for {relative_filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {relative_filepath}")

    # Get files with geo data: Must have creation_time, city_en is not NULL, and hasGPS is True.
    # creation_time is the key data for the media file.
    #   metadata_extractor.py has logic to extract creation_time from various metadata fields (from different field and priorities)
    # hasGPS (True) field added in DB schema to indicate presence of GPS data during the initial scan.
    #   hasGPS field won't be updated in the later shareGeoInfo section.
    #   hasGPS is True indicates this the key file for search the time different during shareGeoInfo logic.
    #   When hasGPS (False) and has geo info which indicates geo info is not from initial scan.
    #       This is not the key file for shareGeoInfo logic, so do not use it for calculating time difference.
    #   shareGPS (True) indicate the geo data is updated from shareGeoInfo logic.
    def get_files_with_geo(self, onlyHasGPSKeyFile = 'Yes'):
        # Get only key files with hasGPS = True
        if onlyHasGPSKeyFile == 'Yes':
            self.cursor.execute(
                'SELECT filepath, creation_time, latitude, longitude, city_en, city_zh, ' + \
                   'region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone ' + \
                   'FROM media_files WHERE creation_time IS NOT NULL and city_en IS NOT NULL and hasGPS = 1')
        # Get all files with geo data, regardless of hasGPS
        elif onlyHasGPSKeyFile == 'AllFiles':
            self.cursor.execute(
                'SELECT filepath, creation_time, latitude, longitude, city_en, city_zh, ' + \
                   'region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone ' + \
                   'FROM media_files WHERE creation_time IS NOT NULL and city_en IS NOT NULL')
        else:
            logging.error(f"get_files_with_geo: Invalid onlyHasGPSKeyFile value: {onlyHasGPSKeyFile}")
            return []
        arr = self.cursor.fetchall()
        # logging.info(f"== Found {len(arr)} image files with city_en data.")
        #for a in arr:
        #    logging.info(f"geo data: {a}")
        return arr

    def get_media_files_geo_count(self, All = False, hasGPS=False, shareGPS=False):
        """Get count of media files with geo data based on hasGPS and shareGPS flags."""
        if All:
            query = 'SELECT COUNT(*) FROM media_files WHERE creation_time IS NOT NULL'
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            return count
        
        query = 'SELECT COUNT(*) FROM media_files WHERE creation_time IS NOT NULL AND hasGPS = ? AND shareGPS = ?'
        params = []
        params.append(hasGPS)
        params.append(shareGPS)
        
        self.cursor.execute(query, tuple(params))
        count = self.cursor.fetchone()[0]
        return count
    
    # Get files without geo data: Must have creation_time, city_en is NULL, and latitude is NULL and hasGPS is False.
    # Getting files (no geo info) for updating geo data from nearby files with geo data.
    # Skip all the key files with hasGPS (True).
    def get_files_without_geo(self):
        self.cursor.execute(
            'SELECT filepath, creation_time, latitude, longitude, city_en, city_zh, ' + \
                   'region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone ' + \
                   'FROM media_files WHERE creation_time IS NOT NULL AND city_en IS NULL AND latitude IS NULL AND hasGPS = 0'
        )
        arr = self.cursor.fetchall()
        # logging.info(f"== Found {len(arr)} files without geo data (city_en is NULL and latitude is NULL).")
        return arr

    def get_media_by_time_and_location(self, timestamp, lat, lon, time_window_minutes=5, distance_threshold_km=0.2):
        # This is a simplified proximity check. A more robust solution would use spatial indexing.
        # For demonstration, we'll just return files within a time window.
        # Real implementation would need to calculate distance from lat/lon.
        self.cursor.execute(
            """SELECT filepath, file_type, latitude, longitude, creation_time FROM media_files
            WHERE ABS(strftime('%s', creation_time) - strftime('%s', ?)) < ? * 60
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            """, (timestamp, time_window_minutes)
        )
        return self.cursor.fetchall()

    def get_all_media_files(self):
        """Get all media files from database with their current analysis status."""
        self.cursor.execute(
            '''SELECT filepath, people_count, activities, scenery, talking_detected 
               FROM media_files 
               WHERE creation_time IS NOT NULL 
               ORDER BY filepath'''
        )
        return self.cursor.fetchall()

    def generate_thumbnail(self, filepath, thumbnail_size=(300, 300), base_directory=None, thumb_directory=None):
        """
        Generate thumbnail for image or video files in separate thumbnail directory.
        Returns the thumbnail file path if successful, None otherwise.
        """
        if not PIL_AVAILABLE:
            logging.debug("PIL/Pillow not available, skipping thumbnail generation")
            return None
            
        # Validate input filepath
        if not filepath:
            logging.error("generate_thumbnail: filepath is None or empty")
            return None
            
        if not isinstance(filepath, str):
            logging.error(f"generate_thumbnail: filepath is not a string, type: {type(filepath)}")
            return None
            
        # Get thumbnail directory from config if not provided
        if not thumb_directory:
            thumb_directory = self.get_config('thumb_directory')
            if not thumb_directory:
                logging.error("No thumbnail directory configured")
                return None
        
        # Get base directory from config if not provided
        if not base_directory:
            base_directory = self.get_config('base_directory')
            if not base_directory:
                logging.error("No base directory configured")
                return None
            
        try:
            # Calculate relative path from base directory
            relative_path = os.path.relpath(filepath, base_directory)
            
            # Generate thumbnail path in thumbnail directory maintaining structure
            file_name = os.path.basename(filepath)
            name_without_ext = os.path.splitext(file_name)[0]
            thumb_filename = f"{name_without_ext}_thumb.jpg"
            
            # Maintain directory structure in thumbnail directory
            thumb_dir_path = os.path.join(thumb_directory, os.path.dirname(relative_path))
            thumbnail_path = os.path.join(thumb_dir_path, thumb_filename)
            
            # Create thumbnail directory if it doesn't exist
            os.makedirs(thumb_dir_path, exist_ok=True)
            
            # Skip if thumbnail already exists
            if os.path.exists(thumbnail_path):
                logging.debug(f"Thumbnail already exists: {thumbnail_path}")
                return thumbnail_path
            
            file_ext = os.path.splitext(filepath)[1].lower()
            
            # Handle image files
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.heic', '.webp']:
                try:
                    # Debug logging to check filepath
                    logging.debug(f"Attempting to open image file: '{filepath}'")
                    logging.debug(f"File exists check: {os.path.exists(filepath)}")
                    logging.debug(f"File extension: {file_ext}")
                    
                    # Special handling for HEIC files which might need pillow-heif
                    if file_ext == '.heic':
                        try:
                            # Try importing pillow_heif for HEIC support
                            import pillow_heif
                            pillow_heif.register_heif_opener()
                        except ImportError:
                            logging.warning("pillow_heif not available, HEIC support may be limited")
                        except Exception as e:
                            logging.warning(f"Error setting up HEIC support: {e}")
                    
                    with Image.open(filepath) as img:
                        # Convert HEIC to RGB if needed
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Auto-orient the image based on EXIF data
                        img = ImageOps.exif_transpose(img)
                        
                        # Generate thumbnail
                        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                        img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                        logging.debug(f"Generated image thumbnail: {thumbnail_path}")
                        return thumbnail_path
                        
                except Exception as e:
                    logging.error(f"Error generating image thumbnail for '{filepath}': {e}")
                    logging.error(f"File exists: {os.path.exists(filepath)}")
                    logging.error(f"File size: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")
                    logging.error(f"Error type: {type(e).__name__}")
                    return None
            
            # Handle video files
            elif file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']:
                try:
                    # First, try to get video info to check if file is valid
                    info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', filepath]
                    info_result = subprocess.run(info_cmd, capture_output=True, text=True)
                    
                    if info_result.returncode != 0:
                        logging.warning(f"ffprobe failed for {filepath}, file might be corrupted")
                        return None
                    
                    # Parse ffprobe output to check for video streams
                    try:
                        import json
                        probe_data = json.loads(info_result.stdout)
                        video_streams = [s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video']
                        
                        if not video_streams:
                            logging.warning(f"No video streams found in {filepath}")
                            return None
                            
                        # Get duration to determine best timestamp for thumbnail
                        duration = video_streams[0].get('duration')
                        if duration:
                            # Use 10% of duration or 1 second, whichever is smaller
                            timestamp = min(1.0, float(duration) * 0.1)
                        else:
                            timestamp = 0.1  # Very early timestamp for problematic files
                            
                    except (json.JSONDecodeError, ValueError, KeyError):
                        logging.warning(f"Could not parse video info for {filepath}, using default timestamp")
                        timestamp = 0.1
                    
                    # Try multiple ffmpeg strategies
                    strategies = [
                        # Strategy 1: Use calculated timestamp
                        ['ffmpeg', '-v', 'quiet', '-i', filepath, '-ss', str(timestamp), '-vframes', '1',
                         '-vf', f'scale={thumbnail_size[0]}:{thumbnail_size[1]}:force_original_aspect_ratio=decrease',
                         '-y', thumbnail_path],
                        
                        # Strategy 2: Use first frame
                        ['ffmpeg', '-v', 'quiet', '-i', filepath, '-vframes', '1',
                         '-vf', f'scale={thumbnail_size[0]}:{thumbnail_size[1]}:force_original_aspect_ratio=decrease',
                         '-y', thumbnail_path],
                         
                        # Strategy 3: More aggressive approach for corrupted files
                        ['ffmpeg', '-v', 'quiet', '-err_detect', 'ignore_err', '-i', filepath, '-vframes', '1',
                         '-vf', f'scale={thumbnail_size[0]}:{thumbnail_size[1]}:force_original_aspect_ratio=decrease',
                         '-y', thumbnail_path]
                    ]
                    
                    for i, cmd in enumerate(strategies, 1):
                        logging.debug(f"Trying ffmpeg strategy {i} for {filepath}")
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0 and os.path.exists(thumbnail_path):
                            logging.debug(f"Generated video thumbnail using strategy {i}: {thumbnail_path}")
                            return thumbnail_path
                        else:
                            logging.debug(f"Strategy {i} failed: {result.stderr.strip()}")
                            # Clean up any partial file
                            if os.path.exists(thumbnail_path):
                                os.remove(thumbnail_path)
                    
                    # All strategies failed
                    logging.error(f"All ffmpeg strategies failed for {filepath}")
                    logging.error(f"Last error: {result.stderr.strip()}")
                    return None
                        
                except Exception as e:
                    logging.error(f"Error generating video thumbnail for {filepath}: {e}")
                    input("Press Enter to continue...")
                    return None
            
            else:
                logging.debug(f"Unsupported file type for thumbnail generation: {file_ext}")
                return None
                
        except Exception as e:
            logging.error(f"Unexpected error generating thumbnail for {filepath}: {e}")
            return None

    def populate_geo_table(self, geo_list_path='geo_chinese.list'):
        """
        Populate the geo_data table with data from geo_chinese.list file.
        
        Args:
            geo_list_path: Path to the geo list CSV file
            
        Returns:
            tuple: (total_records, inserted_records, skipped_records, error_records)
        """
        if not os.path.exists(geo_list_path):
            logging.error(f"Geo list file not found: {geo_list_path}")
            return (0, 0, 0, 1)
        
        total_records = 0
        inserted_records = 0
        skipped_records = 0
        error_records = 0
        
        logging.info(f"Populating geo table from: {geo_list_path}")
        
        try:
            with open(geo_list_path, 'r', encoding='utf-8') as f:
                # Skip header line
                header = next(f)
                logging.debug(f"Header: {header.strip()}")
                
                for line_num, line in enumerate(f, start=2):
                    total_records += 1
                    
                    try:
                        # Parse CSV line: City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
                        parts = line.strip().split(',')
                        if len(parts) != 12:
                            logging.warning(f"Line {line_num}: Invalid format, expected 12 fields, got {len(parts)}")
                            error_records += 1
                            continue
                        
                        city_en = parts[0].strip()
                        city_zh = parts[1].strip()
                        region_en = parts[2].strip()
                        region_zh = parts[3].strip()
                        subregion_en = parts[4].strip()
                        subregion_zh = parts[5].strip()
                        country_code = parts[6].strip()
                        country_en = parts[7].strip()
                        country_zh = parts[8].strip()
                        timezone = parts[9].strip()
                        
                        try:
                            latitude = float(parts[10].strip())
                            longitude = float(parts[11].strip())
                        except ValueError as ve:
                            logging.error(f"Line {line_num}: Invalid coordinates - {ve}")
                            error_records += 1
                            continue
                        
                        # Insert into geo table
                        try:
                            self.cursor.execute('''
                                INSERT OR IGNORE INTO geo_data (
                                    city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                                    country_code, country_en, country_zh, timezone, latitude, longitude
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh,
                                country_code, country_en, country_zh, timezone, latitude, longitude
                            ))
                            
                            if self.cursor.rowcount > 0:
                                inserted_records += 1
                            else:
                                skipped_records += 1
                                logging.debug(f"Skipped duplicate: {city_en}, {country_en} at {latitude}, {longitude}")
                                
                        except sqlite3.Error as db_error:
                            logging.error(f"Line {line_num}: Database error - {db_error}")
                            error_records += 1
                            
                    except Exception as parse_error:
                        logging.error(f"Line {line_num}: Parse error - {parse_error}")
                        error_records += 1
                        
                    # Commit every 1000 records for better performance
                    if total_records % 1000 == 0:
                        self.conn.commit()
                        logging.debug(f"Processed {total_records} records...")
                
                # Final commit
                self.conn.commit()
                
        except Exception as file_error:
            logging.error(f"Error reading geo list file: {file_error}")
            error_records += 1
            
        logging.info(f"Geo table population complete:")
        logging.info(f"  Total records processed: {total_records}")
        logging.info(f"  Records inserted: {inserted_records}")
        logging.info(f"  Records skipped (duplicates): {skipped_records}")
        logging.info(f"  Records with errors: {error_records}")
        
        return (total_records, inserted_records, skipped_records, error_records)

    def get_geo_table_count(self):
        """Get the count of records in geo_data table."""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM geo_data')
            count = self.cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logging.error(f"Error getting geo table count: {e}")
            return 0

    def clear_geo_table(self):
        """Clear all data from geo_data table."""
        try:
            self.cursor.execute('DELETE FROM geo_data')
            self.conn.commit()
            logging.info("Geo table cleared successfully")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error clearing geo table: {e}")
            return False

    def get_geo_data_sample(self, limit=10):
        """Get a sample of records from geo_data table for verification."""
        try:
            self.cursor.execute('''
                SELECT city_en, city_zh, country_en, country_zh, latitude, longitude 
                FROM geo_data 
                ORDER BY city_en 
                LIMIT ?
            ''', (limit,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting geo data sample: {e}")
            return []

    def get_config(self, key, default=None):
        """Get a configuration value by key."""
        try:
            self.cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            result = self.cursor.fetchone()
            return result[0] if result else default
        except sqlite3.Error as e:
            logging.error(f"Error getting config value for key '{key}': {e}")
            return default

    def set_config(self, key, value, description=None):
        """Set a configuration value. Updates if key exists, inserts if new."""
        try:
            # Check if key already exists
            existing_value = self.get_config(key)
            
            if existing_value is not None:
                # Update existing configuration
                self.cursor.execute('''
                    UPDATE config 
                    SET value = ?, description = COALESCE(?, description), updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                ''', (value, description, key))
                logging.debug(f"Updated config: {key} = {value}")
            else:
                # Insert new configuration
                self.cursor.execute('''
                    INSERT INTO config (key, value, description) 
                    VALUES (?, ?, ?)
                ''', (key, value, description))
                logging.debug(f"Inserted new config: {key} = {value}")
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Error setting config value for key '{key}': {e}")
            return False

    def get_all_config(self):
        """Get all configuration key-value pairs."""
        try:
            self.cursor.execute('SELECT key, value, description FROM config ORDER BY key')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting all config values: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            logging.debug("Database connection closed.")

def scan_directory_recursive(path):
    logging.info(f"Starting recursive scan of: {path}")
    all_files = []
    for root, _, files in os.walk(path):
        for file in files:
            # Skip hidden files and non-media files
            extension = os.path.splitext(file)[1].lower()
            if file.startswith('.') or extension not in [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]:
                continue
            
            # Skip thumbnail files (files ending with _thumb.jpg)
            if file.endswith('_thumb.jpg'):
                logging.debug(f"Skipping thumbnail file: {file}")
                continue
                
            all_files.append(os.path.join(root, file))
    logging.info(f"Found {len(all_files)} files in total.")
    return all_files

def get_thumbnail_path(media_filepath, base_directory, thumb_directory):
    """
    Get the thumbnail path for a given media file path.
    Maintains the same directory structure in thumbnail directory.
    """
    if not media_filepath or not base_directory or not thumb_directory:
        return None
        
    try:
        # Calculate relative path from base directory
        relative_path = os.path.relpath(media_filepath, base_directory)
        
        # Generate thumbnail path in thumbnail directory maintaining structure
        file_name = os.path.basename(media_filepath)
        name_without_ext = os.path.splitext(file_name)[0]
        thumb_filename = f"{name_without_ext}_thumb.jpg"
        
        # Maintain directory structure in thumbnail directory
        thumb_dir_path = os.path.join(thumb_directory, os.path.dirname(relative_path))
        thumbnail_path = os.path.join(thumb_dir_path, thumb_filename)
        
        return thumbnail_path
    except Exception as e:
        logging.error(f"Error calculating thumbnail path for {media_filepath}: {e}")
        return None

def cleanup_thumbnails(thumb_directory):
    """Remove all existing thumbnail files from the thumbnail directory tree"""
    if not thumb_directory or not os.path.exists(thumb_directory):
        logging.warning(f"Thumbnail directory not found or not configured: {thumb_directory}")
        return 0
        
    logging.info(f"Cleaning up existing thumbnail files in: {thumb_directory}")
    thumbnail_count = 0
    
    for root, _, files in os.walk(thumb_directory):
        for file in files:
            if file.endswith('_thumb.jpg'):
                thumbnail_path = os.path.join(root, file)
                try:
                    os.remove(thumbnail_path)
                    thumbnail_count += 1
                    logging.debug(f"Removed thumbnail: {thumbnail_path}")
                except OSError as e:
                    logging.error(f"Error removing thumbnail {thumbnail_path}: {e}")
    
    logging.info(f"Cleaned up {thumbnail_count} thumbnail files")
    return thumbnail_count

def configure_thumbnail_directory(db, base_directory):
    """Configure thumbnail directory for storing generated thumbnails."""
    print("\n" + "="*80)
    print("THUMBNAIL DIRECTORY CONFIGURATION")
    print("="*80)
    print("Configure where thumbnail files will be stored.")
    print("Thumbnails maintain the same directory structure as the original media files.")
    print(f"Base media directory: {base_directory}")
    
    # Suggest default thumbnail directory
    default_thumb_dir = os.path.join(os.path.dirname(base_directory), "Thumbnails")
    print(f"Default suggestion: {default_thumb_dir}")
    print("="*80)
    
    while True:
        user_input = input(f"\nEnter thumbnail directory path (or press Enter for default): ").strip()
        
        if user_input:
            thumb_directory = user_input
        else:
            thumb_directory = default_thumb_dir
        
        thumb_directory = os.path.abspath(thumb_directory)
        
        # Check if directory exists, create if it doesn't
        if not os.path.exists(thumb_directory):
            try:
                os.makedirs(thumb_directory, exist_ok=True)
                print(f"✓ Created thumbnail directory: {thumb_directory}")
            except Exception as e:
                print(f"ERROR: Failed to create directory: {e}")
                print("Please enter a different path.")
                continue
        
        # Confirm with user
        print(f"\nThumbnail directory: {thumb_directory}")
        print("This will be saved as your permanent thumbnail directory configuration.")
        confirm = input("Confirm and save this configuration? (y/n): ").strip().lower()
        
        if confirm == 'y':
            success = db.set_config('thumb_directory', thumb_directory, 'Thumbnail directory for storing generated thumbnails (permanent)')
            if success:
                print("✓ Thumbnail directory saved to configuration successfully.")
                return thumb_directory
            else:
                print("ERROR: Failed to save configuration. Please try again.")
                continue
        else:
            print("Configuration not saved.")
            retry = input("Do you want to try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Thumbnail directory configuration is required to run the program.")
                sys.exit(1)

def configure_timezone_settings(db):
    """Configure timezone offset and display settings for web server views."""
    print("\n" + "="*80)
    print("WEB SERVER TIMEZONE DISPLAY CONFIGURATION")
    print("="*80)
    print("Configure timezone settings for web server views display.")
    print("These settings control how creation_time is converted and displayed")
    print("in all web server views (thumbnails and lists).")
    print("="*80)
    
    # Get current values from database
    current_offset = db.get_config('offsetTime', '-04:00')
    current_display = db.get_config('displayTime', 'Toronto')
    
    print(f"\nCurrent settings:")
    print(f"  Timezone Offset: {current_offset}")
    print(f"  Display Location: {current_display}")
    print()
    
    # Ask user for offsetTime
    print("TIMEZONE OFFSET FOR WEB DISPLAY:")
    print("Enter the timezone offset for displaying media files in web views")
    print("Example: -04:00 for EDT Canada/US")
    print("         +02:00 for CEST Europe") 
    print("         +08:00 for HKT or Asia")
    print("")
    print("This converts UTC creation_time to your preferred local display time.")
    print("For example:")
    print("  If offsetTime='+08:00' and creation_time='2025-03-20T16:23:51.000+08:00'")
    print("  Then display: '2025-03-20 4:23:51 PM'")
    print("  If offsetTime='+08:00' and creation_time='2025-04-25T18:20:18.000-04:00'") 
    print("  Then display: '2025-04-26 06:20:18 AM'")
    print()
    
    while True:
        user_offset = input(f"Enter timezone offset (press Enter to keep '{current_offset}'): ").strip()
        
        if not user_offset:
            user_offset = current_offset
            break
        
        # Validate timezone offset format
        import re
        if re.match(r'^[+-]\d{2}:\d{2}$', user_offset):
            break
        else:
            print("ERROR: Invalid format. Please use format like '+08:00' or '-04:00'")
    
    # Ask user for displayTime
    print(f"\nDISPLAY LOCATION:")
    print("Enter the location name for web views display label (e.g., 'Toronto', 'Asia', 'Hong Kong')")
    print("This appears as a label on top of all web views showing the timezone context.")
    
    user_display = input(f"Enter display location (press Enter to keep '{current_display}'): ").strip()
    if not user_display:
        user_display = current_display
    
    # Save the configuration
    print(f"\nSaving web server timezone display configuration:")
    print(f"  Timezone Offset: {user_offset}")
    print(f"  Display Location: {user_display}")
    
    success1 = db.set_config('offsetTime', user_offset, 'Web server display timezone offset for converting UTC creation_time to local display time')
    success2 = db.set_config('displayTime', user_display, 'Web server display timezone location name shown in views')
    
    if success1 and success2:
        print("✓ Web server timezone display configuration saved successfully.")
        print("  These settings will be used in all web views to display local capture time.")
        print("  The offset and location will appear as labels on top of all views.")
    else:
        print("ERROR: Failed to save timezone configuration.")
        print("       The web server will continue with default values.")
        print("       The program will continue with default values.")
    
    print("="*80)

# =====================================================================================
def main():
    default_directory = '/Volumes/Extreme SSD 1/Media'

    default_zh_geo_list_file = 'geo_chinese.list'

    parser = argparse.ArgumentParser(
        description="Organize vacation media files, extract metadata, and store in SQLite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""

==============================================================================
Usage Note: Consider the parameter execution order for optimal performance.
  --cleanup_thumbnails or -c : Remove all existing thumbnail files before file system scanning process. Default: False.
  --jump2update or -j        : Skip the file scanning and processing. Just jump to next section. Default: False.
  --syncFSnDB or -f          : Sync file system changes with the database. Default: False.
  --updateCity or -u         : Update city translation in the database. Default: False.
  --shareGeoInfo or -s       : Share (Update DB) geo info to the no geo media files at the end. Default: False.
  --populateGeoTable or -g   : Populate geo table with data from geo_chinese.list file. Default: False.
  --updateMediaInfo or -m    : Update media analysis info (activities and scenery) in database. Default: False.

  The following parameters can be used together with the above options:
  --debug-level : Set the logging debug level.
  --deldb or -d : Delete database and start the re-scan process.
  --time-diff : Time difference in min for proximity search (default is 60 minutes = 1 hour).
  --geo-list : Specific path to the 'geo.list' file for enhanced geolocation (default: geo_chinese.list).

  Target Directory Configuration:
  The program stores the base directory as a permanent configuration in the database.
  - On first run, you will be prompted to enter the base directory path.
  - Once configured, the base directory cannot be changed during normal operation.
  - Use --deldb to reset the configuration and reconfigure the base directory.
"""
    )
    parser.add_argument(
        '--debug-level', type=str, default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging debug level (default: INFO).'
    )
    parser.add_argument(
        '--deldb', '-d', default=False, action='store_true',
        help='Delete database and start the re-scan process. default: False (do not delete DB)'
    )
    parser.add_argument(
        '--cleanup_thumbnails', '-c', default=False, action='store_true',
        help='Remove all existing thumbnail files before scanning. default: False'
    )
    parser.add_argument(
        '--jump2update', '-j', default=False, action='store_true',
        help='Skip the file scanning and processing. Just jump to next section. default: False'
    )
    parser.add_argument(
        '--syncFSnDB', '-f', default=False, action='store_true',
        help='Sync file system changes with the database. default: False'
    )
    parser.add_argument(
        '--updateCity', '-u', default=False, action='store_true',
        help=f"Use geo table in DB to update city_zh translation in the database. default: False"
    )
    parser.add_argument(
        '--shareGeoInfo', '-s', default=False, action='store_true',
        help='Default not to update (share) geo info to these no geo media files.  default: False.'
    )
    # Add search time_diff parameter for proximity search
    parser.add_argument(
        '--time-diff', type=int, default=60,
        help='Time difference in min for proximity search (default: 60 minutes = 1 hour) 2h=120, 3h=180, 4h=240.'
    )
    parser.add_argument(
        '--geo-list', type=str, default='geo_chinese.list',
        help='Path to the geo.list file for enhanced geolocation (default: geo_chinese.list).'
    )
    parser.add_argument(
        '--populateGeoTable', '-g', default=False, action='store_true',
        help='Populate geo table with data from geo_chinese.list file. default: False'
    )
    parser.add_argument(
        '--updateMediaInfo', '-m', default=False, action='store_true',
        help='Update media analysis info (activities and scenery) in the database. default: False'
    )
    # The geo_chinese.list file for enhanced geolocation with Chinese name translations

    args = parser.parse_args()

    print("\n\n\n\n=== Media Metadata Extraction and Organization Tool ===\n")

    # The geo_chinese.list file should be read-in for geo table population and city translation
    # Therefore, this file path only for user specified different geo list file and load into DB accordingly.
    if args.geo_list != 'geo_chinese.list':
        default_zh_geo_list_file = args.geo_list

    time_diff_seconds = args.time_diff * 60  # convert minutes to seconds

    # Set logging level based on user input
    numeric_level = getattr(logging, args.debug_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid debug level: {args.debug_level}')
    logging.getLogger().setLevel(numeric_level)
    
    # Setup enhanced logging with file output for debug mode
    setup_logging(debug=(args.debug_level.upper() == 'DEBUG'))
    logging.info(f"Logging level set to {args.debug_level}")
    if args.debug_level.upper() == 'DEBUG':
        logging.info("Debug mode enabled: detailed logs will be saved to 'metadata_extraction_debug.log'")

    # When syncing FS and DB, it will re-scan all files, so disable jump2update to skip the normal scanning.
    if args.syncFSnDB:
        args.jump2update = False
        logging.info("Sync FS and DB enabled, disabling jump2update option (jump to DB Geo update section).")

    # If the user specified --populateGeoTable, handle geo table population
    if args.populateGeoTable:
        print("""
Option 'populateGeoTable' is specified.
    The program will populate the geo_data table with data from the geo_chinese.list file.
    This will load all geographical location data into the database for faster lookups.
    After this process, the program will exit.
""")
        # ask for user confirmation to proceed
        proceed = input("Proceed with populating geo table? (y/n): ")
        if proceed.lower() != 'y':
            print("User aborted the operation.")
            sys.exit(0)

    # If the user specified --updateMediaInfo, disable jump2update to ensure DB is ready for analysis update.
    elif args.updateMediaInfo:
        print("""
Option 'updateMediaInfo' is specified.
    The program will only update media analysis info in the DB.
    This includes updating activities and scenery information.
    After this process, the program will exit.    
""")
        # ask for user confirmation to proceed
        proceed = input("Proceed with this settings? (y/n): ")
        if proceed.lower() != 'y':
            print(logging.info("User aborted the operation."))
            sys.exit(0)
    else:
        # Summary of user options
        print("\nUser options summary:")
        print(f"  1. Delete DB and rescan: {args.deldb}")
        if args.deldb:
            print("     WARNING: Existing database will be deleted!")
        print(f"  2. Cleanup thumbnails: {args.cleanup_thumbnails}")
        if args.cleanup_thumbnails:
            print("    WARNING: Existing thumbnails will be deleted!")
        print(f"  3. Jump to update (skip scanning): {args.jump2update}")
        if args.jump2update:
            print("     WARNING: File scanning will be skipped!  Do not use this option for the first run.")
        print(f"  4. Sync FS and DB: {args.syncFSnDB}")
        if not args.syncFSnDB:
            print("     WARNING: File system changes will not be synced with the database!")
        print(f"  5. Update city translations: {args.updateCity}")
        if args.updateCity:
            print(f"     WARNING: Use geo table in DB to update city_zh (Chinese name only) in the database.")
            print( "              Search city_en entry and translate city_zh column accordingly.")
        print(f"  6. Share geo info to no-geo media files: {args.shareGeoInfo}")
        if args.shareGeoInfo:
            print("     WARNING: Geo info will be shared to media files without geo data!")
            print("              This may overwrite existing geo data in those files in DB.")
            print(f"              Use proximity search: '{args.time_diff}' minutes (see below).")
        print(f"  7. Populate geo table: {args.populateGeoTable}")
        if args.populateGeoTable:
            print("     WARNING: Geo table will be populated with data from geo_chinese.list file!")
            print("              This will load all geographical data for faster lookups.")
        print(f"  8. Update media analysis info: {args.updateMediaInfo}")
        if args.updateMediaInfo:
            print("     WARNING: Media analysis (activities and scenery) will be updated!")
            print("              This process analyzes all media files and may take significant time.")
        print(f"\n  I. Time difference for proximity search: '{args.time_diff}' minutes")
        print(f"  II. Geo list path: '{args.geo_list}'    User can specify different geolocation file.")
        print(f"  III. Target directory: Will be determined from database configuration.\n")
        # ask for user confirmation to proceed
        proceed = input("Proceed with these settings? (y/n): ")
        if proceed.lower() != 'y':
            print(logging.info("User aborted the operation."))
            # logging.info("User aborted the operation.")
            sys.exit(0)

# ==================================================================================

    # Main processing starts here
    # If user specified --deldb, delete the existing database file inside MediaOrganizerDB class.
    db = MediaOrganizerDB(rescan=args.deldb)

    if args.deldb:
        logging.info("Database deleted as per user request. Starting fresh scan.")
        args.populateGeoTable = True  # Need to populate geo table if DB is deleted.
    
    # Handle base directory configuration
    base_directory = None
    
    # Try to get base directory and thumbnail directory from config first
    base_directory = db.get_config('base_directory')
    thumb_directory = db.get_config('thumb_directory')
    logging.info(f"Retrieved base_directory from config: {base_directory}")
    logging.info(f"Retrieved thumb_directory from config: {thumb_directory}")
    
    if base_directory:
        # Validate the configured directory
        if not os.path.exists(base_directory):
            print(f"ERROR: Configured base directory does not exist: {base_directory}")
            print("The configured directory appears to have been moved or deleted.")
            print("Please use --deldb to reset the configuration and reconfigure the base directory.")
            sys.exit(1)

        if not os.path.isdir(base_directory):
            print(f"ERROR: Configured base directory is not a directory: {base_directory}")
            print("The configured path is no longer a valid directory.")
            print("Please use --deldb to reset the configuration and reconfigure the base directory.")
            sys.exit(1)
        
        print(f"Using configured base directory: {base_directory}")
        
        # Check if thumbnail directory is configured
        if not thumb_directory:
            print(f"Thumbnail directory not configured. Prompting for configuration...")
            thumb_directory = configure_thumbnail_directory(db, base_directory)
        else:
            # Validate the configured thumbnail directory
            if not os.path.exists(thumb_directory):
                print(f"WARNING: Configured thumbnail directory does not exist: {thumb_directory}")
                print("Creating thumbnail directory...")
                try:
                    os.makedirs(thumb_directory, exist_ok=True)
                    print(f"✓ Created thumbnail directory: {thumb_directory}")
                except Exception as e:
                    print(f"ERROR: Failed to create thumbnail directory: {e}")
                    print("Please use --deldb to reset the configuration.")
                    sys.exit(1)
            print(f"Using configured thumbnail directory: {thumb_directory}")
    else:
        # No base directory configured, prompt user (first-time setup only)
        print("\n" + "="*80)
        print("FIRST-TIME SETUP: DIRECTORIES CONFIGURATION")
        print("="*80)
        print("This is your first time running the program.")
        print("You need to configure the base directory for media file scanning")
        print("and thumbnail directory for storing generated thumbnails.")
        print(f"Default media directory suggestion: {default_directory}")
        print("\nIMPORTANT: Once configured, these directories cannot be changed during normal operation.")
        print("           Use --deldb option to reset the configuration if needed.")
        print("="*80)
        
        while True:
            user_input = input("\nPlease enter the base directory path to scan (or press Enter to use default): ").strip()
            
            if user_input:
                base_directory = user_input
            else:
                base_directory = default_directory
            
            # Validate the entered directory
            if not os.path.exists(base_directory):
                print(f"ERROR: Directory does not exist: {base_directory}")
                print("Please enter a valid directory path.")
                continue
            if not os.path.isdir(base_directory):
                print(f"ERROR: Path is not a directory: {base_directory}")
                print("Please enter a valid directory path.")
                continue
            
            base_directory = os.path.abspath(base_directory)
            
            # Confirm with user before saving permanently
            print(f"\nYou entered: {base_directory}")
            print("This will be saved as your permanent base directory configuration.")
            confirm = input("Confirm and save this configuration? (y/n): ").strip().lower()
            
            if confirm == 'y':
                success = db.set_config('base_directory', base_directory, 'Base directory for media file scanning (permanent)')
                if success:
                    print("✓ Base directory saved to configuration successfully.")
                    print("  This configuration is now permanent and cannot be changed during normal operation.")
                    print("  Use --deldb option if you need to reconfigure in the future.")
                    
                    # Configure thumbnail directory
                    thumb_directory = configure_thumbnail_directory(db, base_directory)
                    
                    # Configure timezone settings
                    configure_timezone_settings(db)
                    
                    break
                else:
                    print("ERROR: Failed to save configuration. Please try again.")
                    continue
            else:
                print("Configuration not saved.")
                retry = input("Do you want to try again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("Base directory configuration is required to run the program.")
                    sys.exit(1)
    
    # Set target_directory to the resolved base_directory
    target_directory = base_directory
    
    # Ensure thumbnail directory is available
    if not thumb_directory:
        thumb_directory = db.get_config('thumb_directory')
        if not thumb_directory:
            print("ERROR: No thumbnail directory configured. Please use --deldb to reset configuration.")
            sys.exit(1)
    
    logging.info(f"Using base directory: {target_directory}")
    logging.info(f"Using thumbnail directory: {thumb_directory}")

    # ==================================================================================
    # Populate geo table if requested
    if args.populateGeoTable:
        logging.info("Starting geo table population process...")
        
        # Check current geo table status
        current_count = db.get_geo_table_count()
        logging.info(f"Current geo table contains {current_count} records")
        
        if current_count > 0:
            print(f"Geo table already contains {current_count} records.")
            overwrite = input("Do you want to clear existing data and repopulate? (y/n): ")
            if overwrite.lower() == 'y':
                if db.clear_geo_table():
                    logging.info("Existing geo data cleared")
                else:
                    logging.error("Failed to clear geo table")
                    sys.exit(1)
            else:
                print("Geo table population cancelled.")
                sys.exit(0)
        
        # Populate the geo table
        total, inserted, skipped, errors = db.populate_geo_table(args.geo_list)
        
        # Show summary
        logging.info("=" * 80)
        logging.info("GEO TABLE POPULATION SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Geo list file: {args.geo_list}")
        logging.info(f"Total records processed: {total}")
        logging.info(f"Records successfully inserted: {inserted}")
        logging.info(f"Records skipped (duplicates): {skipped}")
        logging.info(f"Records with errors: {errors}")
        
        # Show sample data
        sample_data = db.get_geo_data_sample(10)
        if sample_data:
            logging.info("\nSample geo data (first 10 records):")
            for i, (city_en, city_zh, country_en, country_zh, lat, lon) in enumerate(sample_data, 1):
                logging.info(f"  {i:2d}. {city_en} ({city_zh}) in {country_en} ({country_zh}) at {lat}, {lon}")
        
        final_count = db.get_geo_table_count()
        logging.info(f"\nFinal geo table count: {final_count} records")
        logging.info("=" * 80)
        
        print(f"\nGeo Table Population Complete!")
        print(f"✓ Processed {total} records from {args.geo_list}")
        print(f"✓ Inserted {inserted} new geo locations")
        print(f"✓ Final database contains {final_count} geo records")
        if errors > 0:
            print(f"⚠ {errors} records had errors during processing")
        
        db.close()
        sys.exit(0)


    # Initialize metadata extractor with database path (geo data loaded from DB instead of file)
    extractor = MetadataExtractor(db_path=db.db_path)
    
    # Clean up existing thumbnails if requested
    if args.cleanup_thumbnails:
        logging.info("Cleaning up existing thumbnails...")
        cleanup_thumbnails(thumb_directory)
        logging.info("Cleaned up existing thumbnails: completed.")
    else:
        logging.info("Skipping thumbnail cleanup as per user request.")

    all_files = scan_directory_recursive(target_directory)

    # ==================================================================================
    # Update media analysis information if requested
    if args.updateMediaInfo:
        logging.info("Starting media analysis update process...")
        
        # Get all media files from database
        db_media_files = db.get_all_media_files()
        logging.info(f"Found {len(db_media_files)} media files in database")
        
        # Track statistics
        stats = {
            'total_files': len(db_media_files),
            'files_deleted': 0,
            'files_updated': 0,
            'files_skipped': 0,
            'files_error': 0
        }
        
        for i, (relative_filepath, people_count, activities, scenery, talking_detected) in enumerate(db_media_files, 1):
            # Convert relative path to absolute path for file operations
            filepath = db.get_absolute_path(relative_filepath, target_directory)
            
            logging.debug(f"Processing {i}/{len(db_media_files)}: {os.path.basename(filepath)}")
            
            # Debug: Log the actual database values
            logging.debug(f"DB values - people_count: {people_count} (type: {type(people_count)}), "
                         f"activities: '{activities}' (type: {type(activities)}), "
                         f"scenery: '{scenery}' (type: {type(scenery)}), "
                         f"talking_detected: {talking_detected} (type: {type(talking_detected)})")
            
            # Check if physical file exists using absolute path
            if not os.path.exists(filepath):
                logging.info(f"File no longer exists, deleting DB entry: {relative_filepath}")
                try:
                    db.cursor.execute('DELETE FROM media_files WHERE filepath = ?', (relative_filepath,))
                    db.conn.commit()
                    stats['files_deleted'] += 1
                    logging.info(f"Deleted DB entry for missing file: {relative_filepath}")
                except Exception as e:
                    logging.error(f"Error deleting DB entry for {relative_filepath}: {e}")
                    stats['files_error'] += 1
                continue
            
            # Check if media analysis info already exists
            # Only skip if the file has meaningful analysis data
            # Note: people_count and talking_detected checks are disabled since these features are disabled
            # Files with 'NotFound' values are considered as having meaningful analysis data from the previous run.
            has_meaningful_analysis = (
                (activities is not None and activities.strip() != '') or 
                (scenery is not None and scenery.strip() != '')
            )
            
            # Debug: Log the condition evaluation
            logging.debug(f"Analysis check - people: disabled, "
                         f"activities: {activities is not None and (activities.strip() != '' if activities else False)}, "
                         f"scenery: {scenery is not None and (scenery.strip() != '' if scenery else False)}, "
                         f"talking: disabled, "
                         f"has_meaningful_analysis: {has_meaningful_analysis}")
            
            if has_meaningful_analysis:
                logging.debug(f"Skipping file with existing analysis: {filepath}")
                stats['files_skipped'] += 1
                continue
            
            # Perform media analysis (people counting and talking detection disabled)
            try:
                logging.info(f"> Analyzing media file: {os.path.basename(filepath)}")
                analysis_result = extractor._analysis_mediafile(filepath)
                
                # Convert activities list to string for database storage
                activities_list = analysis_result.get('activities', [])
                activities_str = ','.join(activities_list)
                
                # Enhanced logic: assign 'NotFound' if activities is empty
                if not activities_list or not activities_str.strip():
                    activities_str = 'NotFound'
                
                # Enhanced logic: assign 'NotFound' if scenery is empty
                scenery = analysis_result.get('scenery', '')
                if not scenery or not scenery.strip():
                    scenery = 'NotFound'
                
                # Update database with analysis results
                # Note: people_count and talking_detected are disabled (set to 0/False) 
                # but database columns are kept for future use
                semantic_data = {
                    'people_count': 0,  # Disabled: always set to 0
                    'activities': activities_str,
                    'scenery': scenery,
                    'talking_detected': 0  # Disabled: always set to False (0)
                }
                
                db.update_media_file_semantic(filepath, semantic_data, base_directory=target_directory)
                stats['files_updated'] += 1
                
                # Log the analysis results
                logging.info(f"> Updated analysis for {os.path.basename(filepath)}: "
                           # f"people=0 (disabled), "
                           f"activities={activities_str}, "
                           f"scenery={scenery}")
                           # f"talking=False (disabled)")
                
            except Exception as e:
                logging.error(f"Error analyzing media file {filepath}: {e}")
                stats['files_error'] += 1
        
        # Print summary and exit
        logging.info("=" * 80)
        logging.info("MEDIA ANALYSIS UPDATE SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Total files processed: {stats['total_files']}")
        logging.info(f"Files updated with analysis: {stats['files_updated']}")
        logging.info(f"Files skipped (already analyzed): {stats['files_skipped']}")
        logging.info(f"DB entries deleted (missing files): {stats['files_deleted']}")
        logging.info(f"Files with errors: {stats['files_error']}")
        logging.info("=" * 80)
        
        print("\nMedia Analysis Update Complete!")
        print(f"✓ Updated {stats['files_updated']} files with new analysis")
        print(f"✓ Skipped {stats['files_skipped']} files (already analyzed)")
        print(f"✓ Deleted {stats['files_deleted']} orphaned DB entries")
        if stats['files_error'] > 0:
            print(f"⚠ {stats['files_error']} files had errors during analysis")
        
        db.close()
        sys.exit(0)

    # ==================================================================================
    # After the first run, DB is created.  For the rest of the runs, we can skip already scanned files.
    if not args.jump2update:
        logging.info("Starting to process files and update database...")
        for filepath in all_files:

            # Skip the hidden files and non-media files, already done in scanning.
            #extension = os.path.splitext(filepath)[1].lower()
            #if os.path.basename(filepath).startswith('.') or extension not in [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]:
            #    continue
            
            if db.file_exists(filepath, base_directory=target_directory):
                logging.debug(f"Skipping already scanned and existing file: {filepath}")
                continue

            logging.debug(f"Processing file: {filepath}")
            metadata = extractor.extract_metadata(filepath)

            if metadata:
                # Attempt to get geo data from geo.list if GPS coords are present
                if metadata.get('latitude') is not None and metadata.get('longitude') is not None:
                    geo_data = extractor.get_geo_from_coordinates(metadata['latitude'], metadata['longitude'])
                    if geo_data:
                        metadata.update(geo_data)

                #if 'creation_time' not in metadata or metadata['creation_time'] is None or metadata['creation_time'] == 'N/A':
                #    logging.error(f"Missing creation_time, target_directory: {target_directory}, file {filepath}:\n{metadata}")
                #    input("Paused for debugging. Press Enter to continue...")

                # Encounter run time error, debug what is db object here.
                #logging.error(f"Database object state: {db}")
                #logging.error(f"Database connection state: {db.conn}")
                #logging.error(f"Database cursor state: {db.cursor}")
                #logging.error(f"Database file path: {db.db_path}")

                db.add_media_file(metadata, base_directory=target_directory)
            else:
                logging.warning(f"Could not extract metadata for: {filepath}")
    else:
        logging.info("Skipping file scanning as per user request (--jump2update or -j), go to next step.")

    # ==================================================================================
    if args.syncFSnDB:
        logging.info("Sync FS and DB: Syncing file system changes with the database...")
        
        # Generate thumbnails for all existing files if they don't exist
        logging.info("Sync FS and DB: Generating missing thumbnails for existing files...")
        current_files_set = set(all_files)
        thumbnail_count = 0
        for filepath in current_files_set:
            if os.path.exists(filepath):
                # Generate thumbnail using the new structure
                generated_thumbnail_path = db.generate_thumbnail(filepath, base_directory=target_directory, thumb_directory=thumb_directory)
                if generated_thumbnail_path:
                    thumbnail_count += 1
                    logging.debug(f"Generated new thumbnail: {generated_thumbnail_path}")
        logging.info(f"Sync FS and DB: Generated {thumbnail_count} new thumbnails")
        
        db.cursor.execute('SELECT filepath FROM media_files')
        db_relative_paths = set(row[0] for row in db.cursor.fetchall())
        
        # Convert relative paths from database to absolute paths for comparison
        db_absolute_paths = set(db.get_absolute_path(rel_path, target_directory) for rel_path in db_relative_paths)
        
        # Convert current files to relative paths for database operations
        current_relative_paths = set(db.get_relative_path(abs_path, target_directory) for abs_path in current_files_set)

        # Files to remove from DB (relative paths in DB that don't correspond to existing files)
        relative_files_to_remove = db_relative_paths - current_relative_paths
        for relative_filepath in relative_files_to_remove:
            try:
                db.cursor.execute('DELETE FROM media_files WHERE filepath = ?', (relative_filepath,))
                absolute_filepath = db.get_absolute_path(relative_filepath, target_directory)
                logging.info(f"Sync FS and DB: Removed from DB (file no longer exists): {absolute_filepath}")
            except sqlite3.Error as e:
                logging.error(f"Sync FS and DB: Error removing {relative_filepath} from DB: {e}")
        db.conn.commit()

        # This section is repeated here to ensure new files are added above.
        # Files to add to DB (new files) - use absolute paths for processing
        files_to_add = current_files_set - db_absolute_paths
        for filepath in files_to_add:
            # No need to check again for hidden files and non-media files here since already checked in scanning.
            #extension = os.path.splitext(filepath)[1].lower()
            #if os.path.basename(filepath).startswith('.') or extension not in [".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov"]:
            #    continue

            logging.debug(f"Sync FS and DB: New file detected, processing: {filepath}")
            metadata = extractor.extract_metadata(filepath)

            if metadata:
                # Attempt to get geo data from geo.list if GPS coords are present
                if metadata.get('latitude') is not None and metadata.get('longitude') is not None:
                    geo_data = extractor.get_geo_from_coordinates(metadata['latitude'], metadata['longitude'])
                    if geo_data:
                        metadata.update(geo_data)

                # This file is new and not in DB, so no need to check for existing.
                db.add_media_file(metadata, base_directory=target_directory)
            else:
                logging.warning(f"Sync FS and DB: Could not extract metadata for new file: {filepath}")
    else:
        logging.info("Do not Sync File System and DB, go to next step.")

    # ==================================================================================
    # Update city translation (city_en -> city_zh) if requested
    if args.updateCity:
        # Get all image files having geo data, including hasGPS = True key file.
        image_files_with_geo = db.get_files_with_geo( onlyHasGPSKeyFile = 'AllFiles' )
        for image_file in image_files_with_geo:
            # image_file[0] now contains relative path from database
            # Convert to absolute path for the method call
            absolute_filepath = db.get_absolute_path(image_file[0], target_directory)
            db.update_city_translation(absolute_filepath, extractor, base_directory=target_directory)
        logging.info("City translation updated for all relevant image files.")
    else:
        logging.info("Skipping city translation update as per user request.")

    # Parameter shareGeoInfo is default: False.
    # The user does not specify this option, then no sharing geo info to these no-geo media files in DB.
    if args.shareGeoInfo:
        # ---------------------------------------------------------------------------------
        # Iterate through all files in DB, if media file (such as MP4) lacks geo but an other media file nearby has it, share.

        # A robust approach for metadata sharing would involve:
        # 1. Querying all media files with geo data.
        # 2. For each media file (e.g., an image) with geo, find other media files (e.g., videos) within a certain
        #    time and spatial proximity that lack detailed geo-location (city, region, etc.).
        # 3. Propagate the detailed geo-location from the source media to the target media.
        # -----------------------------------------------------------------------------

        # Post-processing for metadata sharing (MP4 from HEIC/Images)
        logging.info("Attempting to share geo metadata between related files...")

        # All iPhone images are HEIC, some other images may have geo data.
        # Once we have more media files (Image and Video) with geo data, we can use them to find nearby videos.
        # Get all image key files (hasGPS = True) with geo data
        image_files_with_geo = db.get_files_with_geo( onlyHasGPSKeyFile = 'Yes')
        logging.info(f">> Found {len(image_files_with_geo)} media files with geo data.")

        #for a in image_files_with_geo:
        #    logging.info(f"geo data: {a}")
        #input("Paused for debugging. Press Enter to continue...")
        
        # The video files are from DJI Pocket 3 which MP4 do not have geo data.
        # As long as the file has creation_time, we can try to find nearby images with geo data.
        all_files_without_geo = db.get_files_without_geo()
        logging.info(f">> Found {len(all_files_without_geo)} media files (mainly MP4) without geo data.")

        #for a in all_files_without_geo:
        #    logging.info(f"no geo data: {a}")
        #input("Paused for debugging. Press Enter to continue...")
       
        # Pre-calculate image_time for all image files for efficiency
        updated_image_files_with_geo = []
        for image_file in image_files_with_geo:
            # convert image_file[1] (creation_time) to datetime object  
            # Support multiple datetime formats including new ISO 8601
            creation_time_str = image_file[1]
            
            image_datetime = parse_datetime_flexible(creation_time_str)
            if image_datetime is None:
                logging.debug(f"Skipping image {image_file[0]} - invalid creation time format: {creation_time_str}")
                continue
                
            updated_image_file = image_file + (image_datetime,)
            updated_image_files_with_geo.append(updated_image_file)       
        # Update the original list
        image_files_with_geo = updated_image_files_with_geo

        # Process each media file without geo data to find closest image file (hasGPS = True)
        # Since all_files_without_geo has only key file, so the search and update no geo data is bounded by key file only.
        update_counter = 0
        for media_file in all_files_without_geo:
            media_filepath = media_file[0]
            media_creation_time = media_file[1]

            media_time = parse_datetime_flexible(media_creation_time)
            if media_time is None:
                logging.debug(f"Skipping {media_filepath} - invalid creation time format: {media_creation_time}")
                continue

            # Find the closest image file by creation time
            closest_image = None
            min_time_diff = float('inf')
            
            for image_file in image_files_with_geo:
                image_filepath = image_file[0]
                image_time = image_file[-1]

                try:
                    # Calculate time difference in seconds
                    time_diff = abs((media_time - image_time).total_seconds())

                    if time_diff > time_diff_seconds:
                        continue  # Skip images that are more than 4 hours apart

                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_image = image_file
                        
                except (ValueError, TypeError) as e:
                    logging.debug(f"Error parsing timestamps for {media_filepath} or {image_filepath}: {e}")
                    continue

            # If we found a close image (within reasonable time window, e.g., default 60 minutes = 1 hr)
            if closest_image and min_time_diff <= time_diff_seconds:
                # Extract geo data from closest image
                geo_data = {
                    'latitude': closest_image[2],
                    'longitude': closest_image[3], 
                    'city_en': closest_image[4],
                    'city_zh': closest_image[5],
                    'region_en': closest_image[6],
                    'region_zh': closest_image[7],
                    'subregion_en': closest_image[8],
                    'subregion_zh': closest_image[9],
                    'country_code': closest_image[10],
                    'country_en': closest_image[11],
                    'country_zh': closest_image[12],
                    'timezone': closest_image[13]
                }
                
                # Update the media file with geo data from closest image
                # set hasGPS = False, shareGPS = True to indicate geo data is shared
                try:
                    db.cursor.execute('''
                        UPDATE media_files
                        SET latitude = ?, longitude = ?, city_en = ?, city_zh = ?, 
                            region_en = ?, region_zh = ?, subregion_en = ?, subregion_zh = ?,
                            country_code = ?, country_en = ?, country_zh = ?, timezone = ?,
                            hasGPS = ?, shareGPS = ?
                        WHERE filepath = ?
                    ''', (
                        geo_data['latitude'], geo_data['longitude'],
                        geo_data['city_en'], geo_data['city_zh'],
                        geo_data['region_en'], geo_data['region_zh'],
                        geo_data['subregion_en'], geo_data['subregion_zh'],
                        geo_data['country_code'], geo_data['country_en'],
                        geo_data['country_zh'], geo_data['timezone'],
                        False,  # Set hasGPS to False. This indicates geo data is not the key file.
                        True,   # Set shareGPS to True. This indicates geo data is shared from another file.
                        media_filepath
                    ))
                    db.conn.commit()

                    update_counter += 1
                    logging.info(f"({update_counter}) Updated geo data for {media_filepath} from {closest_image[0]} "
                            f"(time diff: {min_time_diff:.0f} seconds)")
                            
                except sqlite3.Error as e:
                    logging.error(f"Error updating geo data for {media_filepath}: {e}")
            else:
                if closest_image:
                    logging.debug(f"Closest image for {media_filepath} is too far in time "
                                f"({min_time_diff:.0f} seconds)")
                else:
                    logging.debug(f"No suitable image found for {media_filepath}")
    else:
        logging.info("Skipping geo metadata sharing as per user request.")

    # ==================================================================================

    # Add a media_files table statistic summary at the end of the run
    logging.info("=" * 80)
    logging.info("MEDIA FILES TABLE SUMMARY")
    logging.info("=" * 80)

    # There are three possible scenarios for media files table:
    # 1. Both hasGPS and shareGPS are False: media file has no geo data
    # 2. hasGPS is True, shareGPS is False: media file is the key file with original geo data from metadata
    # 3. hasGPS is False, shareGPS is True: media file has geo data shared from another file.

    no_geo_count = db.get_media_files_geo_count( hasGPS = False, shareGPS = False )
    key_geo_count = db.get_media_files_geo_count( hasGPS = True, shareGPS = False )
    shared_geo_count = db.get_media_files_geo_count( hasGPS = False, shareGPS = True )
    sub_total = no_geo_count + key_geo_count + shared_geo_count

    logging.info(f"Media files without geo data: {no_geo_count}")
    logging.info(f"Media files with key geo data (hasGPS=True): {key_geo_count}")
    logging.info(f"Media files with shared geo data (shareGPS=True): {shared_geo_count}")
    logging.info("-" * 60)
    logging.info(f"Subtotal (should match total below): {sub_total}")
    logging.info("=" * 80)

    total_media_files = db.get_media_files_geo_count( All = True )
    logging.info(f"Total media files in database: {total_media_files}")
    logging.info("=" * 80)

    db.close()
    logging.info("Media organization complete.")

if __name__ == "__main__":
    main()

