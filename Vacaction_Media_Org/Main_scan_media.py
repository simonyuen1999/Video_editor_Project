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
            logging.FileHandler('media_organizer.log', mode='a')  # File output
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

class MediaOrganizerDB:
    def __init__(self, rescan=False, db_path='media_organizer.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.rescan = rescan

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
                    scanned_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
            logging.debug("Media files table ensured to exist with geo fields.")
        except sqlite3.Error as e:
            # If media_files table exists, skip creation, no need to exit
            logging.error(f"Warning creating table: {e}")
            # sys.exit(1)

    def file_exists(self, filepath):
        self.cursor.execute(
            'SELECT 1 FROM media_files WHERE filepath = ?', (filepath,))
        return self.cursor.fetchone() is not None

    def add_media_file(self, metadata):
        # logging.info(f"Adding media file to DB: {metadata.get('filepath')}, {metadata.get('creation_time')}")
        try:
            self.cursor.execute('''
                INSERT INTO media_files (
                    filepath, filename, file_extension, file_type, size, creation_time, latitude, longitude,
                    city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get('filepath'),
                metadata.get('filename'),
                metadata.get('file_extension'),
                metadata.get('file_type'),
                metadata.get('size'),
                metadata.get('creation_time'),
                metadata.get('latitude'),
                metadata.get('longitude'),
                metadata.get('city_en'),
                metadata.get('city_zh'),
                metadata.get('region_en'),
                metadata.get('region_zh'),
                metadata.get('subregion_en'),
                metadata.get('subregion_zh'),
                metadata.get('country_code'),
                metadata.get('country_en'),
                metadata.get('country_zh'),
                metadata.get('timezone'),
            ))
            self.conn.commit()
            logging.debug(f"Added media file: {metadata.get('filepath')}, {metadata.get('creation_time')}")
            
            # Generate thumbnail after successfully adding to database
            filepath = metadata.get('filepath')
            if filepath and os.path.exists(filepath):
                # Check if thumbnail already exists before generating
                file_dir = os.path.dirname(filepath)
                file_name = os.path.basename(filepath)
                name_without_ext = os.path.splitext(file_name)[0]
                thumbnail_path = os.path.join(file_dir, f"{name_without_ext}_thumb.jpg")
                
                if not os.path.exists(thumbnail_path):
                    # Only generate thumbnail if it doesn't exist
                    generated_thumbnail_path = self.generate_thumbnail(filepath)
                    if generated_thumbnail_path:
                        logging.info(f"Generated new thumbnail: {generated_thumbnail_path}")
                else:
                    logging.debug(f"Thumbnail already exists, skipping: {thumbnail_path}")
                    
        except sqlite3.IntegrityError:
            logging.debug(f"File already exists in DB, skipping: {metadata.get('filepath')}")
        except sqlite3.Error as e:
            logging.error(f"Error adding media file to DB: {e}")

    def update_city_translation(self, filepath, extractor):
        try:
            #logging.info(f"City translation from DB {filepath}")
            city_en = None
            city_zh = None
            meta_city_zh = None
            self.cursor.execute('''
                SELECT filepath, city_en, city_zh, country_en FROM media_files
                WHERE filepath = ?
            ''', (filepath,))
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
                ''', (meta_city_zh, filepath))
                self.conn.commit()
                logging.info(f"Updated DB file {filepath}:\n > city_en: {city_en}, city_zh: {city_zh} -> meta_city_zh: {meta_city_zh}")
            #else:
            #    logging.info(f"   No update required for city translation: city_en: {city_en}, city_zh: {city_zh}, meta_city_zh: {meta_city_zh}\n")

        except sqlite3.Error as e:
            logging.error(f"Error updating city translation for {filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {filepath}")

    def update_media_file_geo(self, filepath, geo_data):
        try:
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
                filepath
            ))
            self.conn.commit()
            logging.debug(f"Updated geo data for {filepath}")
        except sqlite3.Error as e:
            logging.error(f"Error updating geo data for {filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {filepath}")

    def update_media_file_semantic(self, filepath, semantic_data):
        try:
            self.cursor.execute('''
                UPDATE media_files
                SET people_count = ?, activities = ?, scenery = ?, talking_detected = ?
                WHERE filepath = ?
            ''', (
                semantic_data.get('people_count', 0),
                semantic_data.get('activities', ''),
                semantic_data.get('scenery', ''),
                semantic_data.get('talking_detected', 0),
                filepath
            ))
            self.conn.commit()
            logging.debug(f"Updated semantic data for {filepath}")
        except sqlite3.Error as e:
            logging.error(f"Error updating semantic data for {filepath}: {e}")
            self.conn.rollback()
            logging.debug(f"Rolled back changes for {filepath}")

    def get_files_with_geo(self):
        self.cursor.execute(
            'SELECT filepath, creation_time, latitude, longitude, city_en, city_zh, ' + \
                   'region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone ' + \
                   'FROM media_files WHERE creation_time IS NOT NULL and city_en IS NOT NULL')
        arr = self.cursor.fetchall()
        # logging.info(f"== Found {len(arr)} image files with city_en data.")
        #for a in arr:
        #    logging.info(f"geo data: {a}")
        return arr

    def get_files_without_geo(self):
        self.cursor.execute(
            'SELECT filepath, creation_time, latitude, longitude, city_en, city_zh, ' + \
                   'region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone ' + \
                   'FROM media_files WHERE creation_time IS NOT NULL AND city_en IS NULL AND latitude IS NULL'
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

    def generate_thumbnail(self, filepath, thumbnail_size=(300, 300)):
        """
        Generate thumbnail for image or video files.
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
            
        try:
            # Generate thumbnail filename
            file_dir = os.path.dirname(filepath)
            file_name = os.path.basename(filepath)
            name_without_ext = os.path.splitext(file_name)[0]
            thumbnail_path = os.path.join(file_dir, f"{name_without_ext}_thumb.jpg")
            
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

def cleanup_thumbnails(path):
    """Remove all existing thumbnail files from the directory tree"""
    logging.info(f"Cleaning up existing thumbnail files in: {path}")
    thumbnail_count = 0
    
    for root, _, files in os.walk(path):
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

def main():
    default_directory = '/Volumes/Extreme SSD 1/Media'

    default_zh_geo_list_file = 'geo_chinese_.list'

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
  --updateMediaInfo or -m    : Update media analysis info (activities and scenery) in database. Default: False.

  The following parameters can be used together with the above options:
  --debug-level : Set the logging debug level.
  --deldb or -d : Delete database and start the re-scan process.
  --time-diff : Time difference in min for proximity search (default is 60 minutes = 1 hour).
  --geo-list : Specific path to the 'geo.list' file for enhanced geolocation (default: geo_chinese_.list).

  Finally, specify the target directory to scan (required). If not provided, you will be prompted to enter one.
"""
    )
    parser.add_argument(
        'directory', type=str, nargs='?', default=None,
        help='The target directory to scan (required).'
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
        help=f"Use '{default_zh_geo_list_file}' to update city_zh translation in the database. default: False"
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
        '--geo-list', type=str, default='geo_chinese_.list',
        help='Path to the geo.list file for enhanced geolocation (default: geo_chinese_.list).'
    )
    parser.add_argument(
        '--updateMediaInfo', '-m', default=False, action='store_true',
        help='Update media analysis info (activities and scenery) in the database. default: False'
    )
    # The geo_chinese_.list file for enhanced geolocation with Chinese name translations

    args = parser.parse_args()

    if args.geo_list != 'geo_chinese_.list':
        default_zh_geo_list_file = args.geo_list

    # Prompt for directory if not provided
    if args.directory is None:
        print(f"\nNo scan directory specified. Default directory suggestion: {default_directory}")
        user_input = input("Please enter the directory path to scan (or press Enter to use default): ").strip()
        
        if user_input:
            args.directory = user_input
        else:
            args.directory = default_directory
        
        print(f"Using directory: {args.directory}")

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

    # If the user specified --updateMediaInfo, disable jump2update to ensure DB is ready for analysis update.
    if args.updateMediaInfo:
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
            print(f"     WARNING: Use '{default_zh_geo_list_file}' file to update city_zh (Chinese name only) in the database.")
            print( "              Search city_en entry and translate city_zh column accordingly.")
        print(f"  6. Share geo info to no-geo media files: {args.shareGeoInfo}")
        if args.shareGeoInfo:
            print("     WARNING: Geo info will be shared to media files without geo data!")
            print("              This may overwrite existing geo data in those files in DB.")
            print(f"              Use proximity search: '{args.time_diff}' minutes (see below).")
        print(f"  7. Update media analysis info: {args.updateMediaInfo}")
        if args.updateMediaInfo:
            print("     WARNING: Media analysis (activities and scenery) will be updated!")
            print("              This process analyzes all media files and may take significant time.")
        print(f"\n  I. Time difference for proximity search: '{args.time_diff}' minutes")
        print(f"  II. Geo list path: '{args.geo_list}'    User can specify different geolocation file.")
        print(f"  III. Target directory: '{args.directory}'    The directory to scan for media files.\n")
        # ask for user confirmation to proceed
        proceed = input("Proceed with these settings? (y/n): ")
        if proceed.lower() != 'y':
            print(logging.info("User aborted the operation."))
            # logging.info("User aborted the operation.")
            sys.exit(0)

    # If user specified --deldb, delete the existing database file inside MetaOrganizerDB class.
    db = MediaOrganizerDB(rescan=args.deldb)
    extractor = MetadataExtractor(geo_list_path=args.geo_list)

    target_directory = args.directory
    
    # Clean up existing thumbnails if requested
    if args.cleanup_thumbnails:
        logging.info("Cleaning up existing thumbnails...")
        cleanup_thumbnails(target_directory)
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
        
        for i, (filepath, people_count, activities, scenery, talking_detected) in enumerate(db_media_files, 1):
            logging.debug(f"Processing {i}/{len(db_media_files)}: {os.path.basename(filepath)}")
            
            # Debug: Log the actual database values
            logging.debug(f"DB values - people_count: {people_count} (type: {type(people_count)}), "
                         f"activities: '{activities}' (type: {type(activities)}), "
                         f"scenery: '{scenery}' (type: {type(scenery)}), "
                         f"talking_detected: {talking_detected} (type: {type(talking_detected)})")
            
            # Check if physical file exists
            if not os.path.exists(filepath):
                logging.info(f"File no longer exists, deleting DB entry: {filepath}")
                try:
                    db.cursor.execute('DELETE FROM media_files WHERE filepath = ?', (filepath,))
                    db.conn.commit()
                    stats['files_deleted'] += 1
                    logging.info(f"Deleted DB entry for missing file: {filepath}")
                except Exception as e:
                    logging.error(f"Error deleting DB entry for {filepath}: {e}")
                    stats['files_error'] += 1
                continue
            
            # Check if media analysis info already exists
            # Only skip if the file has meaningful analysis data
            # Note: people_count and talking_detected checks are disabled since these features are disabled
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
                activities_str = ','.join(analysis_result.get('activities', []))
                
                # Update database with analysis results
                # Note: people_count and talking_detected are disabled (set to 0/False) 
                # but database columns are kept for future use
                semantic_data = {
                    'people_count': 0,  # Disabled: always set to 0
                    'activities': activities_str,
                    'scenery': analysis_result.get('scenery', ''),
                    'talking_detected': 0  # Disabled: always set to False (0)
                }
                
                db.update_media_file_semantic(filepath, semantic_data)
                stats['files_updated'] += 1
                
                # Log the analysis results
                logging.info(f"> Updated analysis for {os.path.basename(filepath)}: "
                           # f"people=0 (disabled), "
                           f"activities={activities_str}, "
                           f"scenery={analysis_result.get('scenery', '')}")
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
            
            if db.file_exists(filepath):
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
                #    logging.warning(f"Metadata for {filepath}: ****** Missing creation_time")
                #    input("Paused for debugging. Press Enter to continue...")

                db.add_media_file(metadata)
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
                # Check if thumbnail already exists before generating
                file_dir = os.path.dirname(filepath)
                file_name = os.path.basename(filepath)
                name_without_ext = os.path.splitext(file_name)[0]
                thumbnail_path = os.path.join(file_dir, f"{name_without_ext}_thumb.jpg")
                
                if not os.path.exists(thumbnail_path):
                    # Only generate thumbnail if it doesn't exist
                    generated_thumbnail_path = db.generate_thumbnail(filepath)
                    if generated_thumbnail_path:
                        thumbnail_count += 1
                        logging.debug(f"Generated new thumbnail: {generated_thumbnail_path}")
                else:
                    logging.debug(f"Thumbnail already exists, skipping: {thumbnail_path}")
        logging.info(f"Sync FS and DB: Generated {thumbnail_count} new thumbnails")
        
        db.cursor.execute('SELECT filepath FROM media_files')
        db_files_set = set(row[0] for row in db.cursor.fetchall())

        # Files to remove from DB
        files_to_remove = db_files_set - current_files_set
        for filepath in files_to_remove:
            try:
                db.cursor.execute('DELETE FROM media_files WHERE filepath = ?', (filepath,))
                logging.info(f"Sync FS and DB: Removed from DB (file no longer exists): {filepath}")
            except sqlite3.Error as e:
                logging.error(f"Sync FS and DB: Error removing {filepath} from DB: {e}")
        db.conn.commit()

        # This section is repeated here to ensure new files are added above.
        # Files to add to DB (new files)
        files_to_add = current_files_set - db_files_set
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
                db.add_media_file(metadata)
            else:
                logging.warning(f"Sync FS and DB: Could not extract metadata for new file: {filepath}")
    else:
        logging.info("Do not Sync File System and DB, go to next step.")

    # ==================================================================================
    # Update city translation if requested
    if args.updateCity:
        image_files_with_geo = db.get_files_with_geo()
        for image_file in image_files_with_geo:
            db.update_city_translation(image_file[0], extractor)
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
        image_files_with_geo = db.get_files_with_geo()
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
            # convert image_file[1] (creation_time in YYYY-MM-DD HH:MM:SS format) to datetime object  
            image_datetime = datetime.strptime(image_file[1], '%Y-%m-%d %H:%M:%S')
            updated_image_file = image_file + (image_datetime,)
            updated_image_files_with_geo.append(updated_image_file)       
        # Update the original list
        image_files_with_geo = updated_image_files_with_geo

        # Process each media file without geo data to find closest image with geo data
        for media_file in all_files_without_geo:
            media_filepath = media_file[0]
            media_creation_time = media_file[1]

            try:
                media_time = datetime.strptime(media_creation_time, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError) as e:
                logging.debug(f"Skipping {media_filepath} - invalid creation time format: {media_creation_time}")
                continue

            # Already use SQL to filter out files without creation_time (SQL: creation_time IS NOT NULL)
            #if not media_creation_time:
            #    logging.debug(f"Skipping {media_filepath} - no creation time available")
            #    continue

            # Find the closest image file by creation time
            closest_image = None
            min_time_diff = float('inf')
            
            for image_file in image_files_with_geo:
                image_filepath = image_file[0]
                image_time = image_file[-1]

                # Already use SQL to filter out files without creation_time (SQL: creation_time IS NOT NULL)
                # if not image_creation_time:
                #    continue
                    
                try:
                    # Calculate time difference in seconds
                    time_diff = abs((media_time - image_time).total_seconds())

                    if time_diff > time_diff_seconds:  # Use seconds for search, default 4h (240 minutes = 4 hours)
                        continue  # Skip images that are more than 4 hours apart

                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_image = image_file
                        
                except (ValueError, TypeError) as e:
                    logging.debug(f"Error parsing timestamps for {media_filepath} or {image_filepath}: {e}")
                    continue

            # If we found a close image (within reasonable time window, e.g., 4 hours = 240 minutes)
            if closest_image and min_time_diff <= time_diff_seconds:  # 240 minutes = 4 hours
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
                try:
                    db.cursor.execute('''
                        UPDATE media_files
                        SET latitude = ?, longitude = ?, city_en = ?, city_zh = ?, 
                            region_en = ?, region_zh = ?, subregion_en = ?, subregion_zh = ?,
                            country_code = ?, country_en = ?, country_zh = ?, timezone = ?
                        WHERE filepath = ?
                    ''', (
                        geo_data['latitude'], geo_data['longitude'],
                        geo_data['city_en'], geo_data['city_zh'],
                        geo_data['region_en'], geo_data['region_zh'],
                        geo_data['subregion_en'], geo_data['subregion_zh'],
                        geo_data['country_code'], geo_data['country_en'],
                        geo_data['country_zh'], geo_data['timezone'],
                        media_filepath
                    ))
                    db.conn.commit()
                    
                    logging.info(f"Updated geo data for {media_filepath} from {closest_image[0]} "
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

    db.close()
    logging.info("Media organization complete.")

if __name__ == "__main__":
    main()

