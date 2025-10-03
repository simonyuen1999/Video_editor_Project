#!python
import os
import sys
import argparse
import logging
import sqlite3
from metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(levelname)s - %(message)s')

class MediaOrganizerDB:
    def __init__(self, db_path='media_organizer.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
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
                    modification_time TEXT,
                    latitude REAL,
                    longitude REAL,
                    city TEXT,
                    region TEXT,
                    subregion TEXT,
                    country_code TEXT,
                    country TEXT,
                    scanned_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
            logging.debug("Media files table ensured to exist with geo fields.")
        except sqlite3.Error as e:
            logging.error(f"Error creating table: {e}")
            sys.exit(1)

    def file_exists(self, filepath):
        self.cursor.execute(
            'SELECT 1 FROM media_files WHERE filepath = ?', (filepath,))
        return self.cursor.fetchone() is not None

    def add_media_file(self, metadata):
        try:
            self.cursor.execute('''
                INSERT INTO media_files (
                    filepath, filename, file_extension, file_type, size,
                    creation_time, modification_time, latitude, longitude,
                    city, region, subregion, country_code, country
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get('filepath'),
                metadata.get('filename'),
                metadata.get('file_extension'),
                metadata.get('file_type'),
                metadata.get('size'),
                metadata.get('creation_time'),
                metadata.get('modification_time'),
                metadata.get('latitude'),
                metadata.get('longitude'),
                metadata.get('city'),
                metadata.get('region'),
                metadata.get('subregion'),
                metadata.get('country_code'),
                metadata.get('country'),
            ))
            self.conn.commit()
            logging.info(f"Added/Updated: {metadata.get('filepath')}")
        except sqlite3.IntegrityError:
            logging.debug(f"File already exists in DB, skipping: {metadata.get('filepath')}")
        except sqlite3.Error as e:
            logging.error(f"Error adding media file to DB: {e}")

    def update_media_file_geo(self, filepath, geo_data):
        try:
            self.cursor.execute('''
                UPDATE media_files
                SET city = ?, region = ?, subregion = ?, country_code = ?, country = ?
                WHERE filepath = ?
            ''', (
                geo_data.get('city'),
                geo_data.get('region'),
                geo_data.get('subregion'),
                geo_data.get('country_code'),
                geo_data.get('country'),
                filepath
            ))
            self.conn.commit()
            logging.debug(f"Updated geo data for {filepath}")
        except sqlite3.Error as e:
            logging.error(f"Error updating geo data for {filepath}: {e}")

    def get_files_without_geo(self):
        self.cursor.execute(
            'SELECT filepath, latitude, longitude FROM media_files WHERE city IS NULL AND latitude IS NOT NULL'
        )
        return self.cursor.fetchall()

    def get_media_by_time_and_location(self, timestamp, lat, lon, time_window_minutes=5, distance_threshold_km=0.1):
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
            all_files.append(os.path.join(root, file))
    logging.info(f"Found {len(all_files)} files in total.")
    return all_files

def main():
    parser = argparse.ArgumentParser(
        description="Organize vacation media files, extract metadata, and store in SQLite."
    )
    parser.add_argument(
        'directory', type=str, nargs='?', default='.',
        help='The target directory to scan (default: current directory).'
    )
    parser.add_argument(
        '--debug-level', type=str, default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging debug level (default: INFO).'
    )
    parser.add_argument(
        '--skip-scanned', action='store_true',
        help='Skip files that have already been scanned and exist in the database.'
    )
    parser.add_argument(
        '--geo-list', type=str, default='geo.list',
        help='Path to the geo.list file for enhanced geolocation (default: geo.list).'
    )

    args = parser.parse_args()

    # Set logging level based on user input
    numeric_level = getattr(logging, args.debug_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid debug level: {args.debug_level}')
    logging.getLogger().setLevel(numeric_level)
    logging.info(f"Logging level set to {args.debug_level}")

    db = MediaOrganizerDB()
    extractor = MetadataExtractor(geo_list_path=args.geo_list)

    target_directory = args.directory
    all_files = scan_directory_recursive(target_directory)

    for filepath in all_files:
        if args.skip_scanned and db.file_exists(filepath):
            logging.debug(f"Skipping already scanned file: {filepath}")
            continue

        logging.debug(f"Processing file: {filepath}")
        metadata = extractor.extract_metadata(filepath)

        if metadata:
            # Attempt to get geo data from geo.list if GPS coords are present
            if metadata.get('latitude') is not None and metadata.get('longitude') is not None:
                geo_data = extractor.get_geo_from_coordinates(
                    metadata['latitude'], metadata['longitude']
                )
                if geo_data:
                    metadata.update(geo_data)

            db.add_media_file(metadata)
        else:
            logging.warning(f"Could not extract metadata for: {filepath}")

    # Post-processing for metadata sharing (MP4 from HEIC/Images)
    logging.info("Attempting to share geo metadata between related files...")
    image_files_with_geo = db.get_files_without_geo() # This is a placeholder, needs actual query for images with geo
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

    db.close()
    logging.info("Media organization complete.")

if __name__ == "__main__":
    main()

