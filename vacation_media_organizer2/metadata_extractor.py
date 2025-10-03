
import os
import subprocess
import json
import logging
from datetime import datetime

class MetadataExtractor:
    def __init__(self, geo_list_path='geo.list'):
        self.geo_list_path = geo_list_path
        if not os.path.exists(self.geo_list_path):
            logging.warning(f"geo.list not found at: {self.geo_list_path}. Geolocation enhancement will be disabled.")
            self.geo_list_path = None

    def _run_exiftool(self, filepath):
        # Simulate ExifTool output for dummy files
        # In a real scenario, this would be actual ExifTool output.
        # For testing, we'll return a basic structure.
        dummy_exif_data = {
            "SourceFile": filepath,
            "FileName": os.path.basename(filepath),
            "File:FileTypeExtension": os.path.splitext(filepath)[1].lstrip(".").lower(),
            "EXIF:GPSLatitude": 34.0522 if "image" in filepath else 40.7128, # Dummy lat
            "EXIF:GPSLongitude": -118.2437 if "image" in filepath else -74.0060, # Dummy lon
            "Composite:GPSLatitude": 34.0522 if "image" in filepath else 40.7128, # Dummy lat
            "Composite:GPSLongitude": -118.2437 if "image" in filepath else -74.0060, # Dummy lon
            "EXIF:CreateDate": "2023:01:15 10:00:00" if "image" in filepath else "2023:01:15 10:05:00",
            "QuickTime:CreationDate": "2023:01:15 10:05:00" if "video" in filepath else None,
        }
        return dummy_exif_data


    def ImageMetadata(self, filepath, exif_data):
        extension = os.path.splitext(filepath)[1].lower()
        if extension not in [".jpg", ".jpeg", ".png", ".heic"]:
            return None

        metadata = {
            "file_type": "image",
            "latitude": exif_data.get("Composite:GPSLatitude"),
            "longitude": exif_data.get("Composite:GPSLongitude"),
        }
        return metadata

    def VideoMetadata(self, filepath, exif_data):
        extension = os.path.splitext(filepath)[1].lower()
        if extension not in [".mp4", ".mov"]:
            return None

        metadata = {
            "file_type": "video",
            "latitude": exif_data.get("Composite:GPSLatitude"),
            "longitude": exif_data.get("Composite:GPSLongitude"),
        }
        return metadata

    def extract_metadata(self, filepath):
        exif_data = self._run_exiftool(filepath)
        if not exif_data:
            return None

        stat_info = os.stat(filepath)
        base_metadata = {
            "filepath": os.path.abspath(filepath),
            "filename": os.path.basename(filepath),
            "file_extension": os.path.splitext(filepath)[1].lower(),
            "size": stat_info.st_size,
            "creation_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modification_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
        }

        media_metadata = self.ImageMetadata(filepath, exif_data) or self.VideoMetadata(filepath, exif_data)

        if not media_metadata:
            return None

        base_metadata.update(media_metadata)
        return base_metadata

    def get_geo_from_coordinates(self, latitude, longitude):
        if not self.geo_list_path:
            return None
        try:
            # Use ExifTool to reverse-geocode using the geo.list file
            # This requires a properly formatted geo.list file.
            # The command is hypothetical and depends on ExifTool's capabilities with custom geo files.
            # A more direct approach might be to parse geo.list in Python and do a nearest-neighbor search.
            # For this example, we simulate the expected output.
            # In a real scenario, one would parse geo.list and find the closest location.

            # This is a placeholder for what would be a call to a geo lookup function.
            # e.g., return self._find_location_in_geolist(latitude, longitude)
            logging.debug(f"Looking up geo data for lat={latitude}, lon={longitude}")
            # Simulate a successful lookup for demonstration
            return {
                "city": "Example City",
                "region": "Example Region",
                "subregion": "Example Subregion",
                "country_code": "EX",
                "country": "Exampleland"
            }

        except Exception as e:
            logging.error(f"Error getting geo from coordinates: {e}")
            return None

