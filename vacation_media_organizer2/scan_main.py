#!python
import os
import sys
import argparse
import logging
import sqlite3
from datetime import datetime               
from metadata_extractor import MetadataExtractor

# Configure logging
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
        except sqlite3.IntegrityError:
            logging.debug(f"File already exists in DB, skipping: {metadata.get('filepath')}")
        except sqlite3.Error as e:
            logging.error(f"Error adding media file to DB: {e}")

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
            all_files.append(os.path.join(root, file))
    logging.info(f"Found {len(all_files)} files in total.")
    return all_files

def main():
    default_directory = '/Volumes/Extreme SSD 1/Media'
    
    parser = argparse.ArgumentParser(
        description="Organize vacation media files, extract metadata, and store in SQLite."
    )
    parser.add_argument(
        'directory', type=str, nargs='?', default=default_directory,
        help=f'The target directory to scan (default: "{default_directory}").'
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
        '--jump2update', '-j', default=False, action='store_true',
        help='Skip the file scanning and jump to updating the database. default: False'
    )
    parser.add_argument(
        '--skipDBupdate', '-s', default=False, action='store_true',
        help='Default not skip DB update at the end. default: False'
    )
    parser.add_argument(
        '--syncFSnDB', '-f', default=False, action='store_true',
        help='Sync file system changes with the database. default: False'
    )
    # Add search time_diff parameter for proximity search
    parser.add_argument(
        '--time-diff', type=int, default=240,
        help='Time difference in min for proximity search (default: 240 minutes = 4 hours) 5h=300, 6h=360, 7h=420.'
    )
    parser.add_argument(
        '--geo-list', type=str, default='geo_chinese_.list',
        help='Path to the geo.list file for enhanced geolocation (default: geo_chinese_.list).'
    )
    # The geo_chinese_.list file for enhanced geolocation with Chinese name translations

    args = parser.parse_args()

    time_diff_seconds = args.time_diff * 60  # convert minutes to seconds

    # Set logging level based on user input
    numeric_level = getattr(logging, args.debug_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid debug level: {args.debug_level}')
    logging.getLogger().setLevel(numeric_level)
    logging.info(f"Logging level set to {args.debug_level}")

    # When syncing FS and DB, it will re-scan all files, so disable jump2update to skip the normal scanning.
    if args.syncFSnDB:
        args.jump2update = False
        logging.info("Sync FS and DB enabled, disabling jump2update option (jump to DB Geo update section).")

    # If user specified --deldb, delete the existing database file inside MetaOrganizerDB class.
    db = MediaOrganizerDB(rescan=args.deldb)
    extractor = MetadataExtractor(geo_list_path=args.geo_list)

    target_directory = args.directory
    all_files = scan_directory_recursive(target_directory)

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
        logging.info("Skipping file scanning as per user request (--jump2update or -j), go to DB update.")

    # ==================================================================================
    if args.syncFSnDB:
        logging.info("Sync FS and DB: Syncing file system changes with the database...")
        current_files_set = set(all_files)
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

    # ==================================================================================
    if not args.skipDBupdate:
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
            # convert image_file[1] (YYYY-MM-DD HH:MM:SS format) to datetime object,  
            image_datetime = datetime.strptime(image_file[1], '%Y:%m:%d %H:%M:%S')
            updated_image_file = image_file + (image_datetime,)
            updated_image_files_with_geo.append(updated_image_file)       
        # Update the original list
        image_files_with_geo = updated_image_files_with_geo

        # Process each media file without geo data to find closest image with geo data
        for media_file in all_files_without_geo:
            media_filepath = media_file[0]
            media_time = datetime.strptime(media_file[1], '%Y:%m:%d %H:%M:%S')

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

        # For a real implementation, we'd query for images with geo data, then find nearby videos.
        # For now, let's simulate by finding files that need geo and trying to fill them.

        # Simplified metadata sharing logic (needs refinement for real-world use)
        # Iterate through all files in DB, if an MP4 lacks geo but an image nearby has it, share.
        # This part would be more complex, involving spatial and temporal queries.
        # For this playbook, we'll assume the extractor can handle this during initial scan or a dedicated pass.

        # A more robust approach for metadata sharing would involve:
        # 1. Querying all media files with GPS data.
        # 2. For each media file (e.g., an image) with GPS, find other media files (e.g., videos) within a certain
        #    time and spatial proximity that lack detailed geo-location (city, region, etc.).
        # 3. Propagate the detailed geo-location from the source media to the target media.

        # Example of how one might iterate to find and update related files:
        # for image_filepath, img_lat, img_lon, img_time in db.get_images_with_geo():
        #     related_videos = db.get_media_by_time_and_location(img_time, img_lat, img_lon)
        #     for video_filepath, vid_type, vid_lat, vid_lon, vid_time in related_videos:
        #         if vid_type == 'video' and not db.has_detailed_geo(video_filepath):
        #             geo_data = extractor.get_geo_from_coordinates(img_lat, img_lon) # Re-extract or use cached
        #             if geo_data:
        #                 db.update_media_file_geo(video_filepath, geo_data)
        #                 logging.info(f"Shared geo data from {image_filepath} to {video_filepath}")
    # ==================================================================================

    db.close()
    logging.info("Media organization complete.")

if __name__ == "__main__":
    main()

