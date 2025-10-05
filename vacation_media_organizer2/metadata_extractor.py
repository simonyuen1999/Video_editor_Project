
from math import radians, sin, cos, sqrt, atan2
import os
import subprocess
import json
import logging
from datetime import datetime
from unittest import result

class MetadataExtractor:
    def __init__(self, geo_list_path='geo.list'):
        self.geo_list_path = geo_list_path
        if not os.path.exists(self.geo_list_path):
            logging.warning(f"geo.list not found at: {self.geo_list_path}. Geolocation enhancement will be disabled.")
            self.geo_list_path = None
        else:
            # Read and parse geo.list comma separator CSV file and store in memory as a list of tuples
            # This is the first line of the geo.list file:
            #   City,Region,Subregion,CountryCode,Country,TimeZone,FeatureCode,Population,Latitude,Longitude
            self.geo_data = []
            with open(self.geo_list_path, 'r', encoding='utf-8') as f:
                # Skip header line
                next(f)
                for line in f:
                    # Each line is comma-separated values and values are 0:City,1:Region,2:Subregion,3:CountryCode,4:Country,5:TimeZone,6:FeatureCode,7:Population,8:Latitude,9:Longitude
                    # After splitting, we want to store (Latitude, Longitude, City, Region, Subregion, CountryCode, Country)
                    parts = line.strip().split(',')
                    try:
                        lat = float(parts[8])
                        lon = float(parts[9])
                        city = parts[0]
                        region = parts[1]
                        subregion = parts[2]
                        country_code = parts[3]
                        country = parts[4]
                        self.geo_data.append((lat, lon, city, region, subregion, country_code, country))
                    except ValueError:
                        logging.error(f"Error parsing line in geo.list: {line}")
                        continue
            logging.info(f"Loaded {len(self.geo_data)} entries from geo.list")

    def _run_exiftool(self, filepath):
        result = subprocess.run(
            ['exifTool', '-n', '-j', filepath],
            capture_output=True, text=True
        )
        metadata = json.loads(result.stdout)
        # logging.debug(f"ExifTool output for {filepath}: {metadata}")

        if not metadata or 'Error' in metadata[0]:
            logging.error(f"Error reading metadata from {filepath}: {metadata[0].get('Error', 'Unknown error')}")
            return None

        GPSLatitude  = metadata[0].get("GPSLatitude", "N/A") if "GPSLatitude" in metadata[0] else None
        GPSLongitude = metadata[0].get("GPSLongitude", "N/A") if "GPSLongitude" in metadata[0] else None
        createDate   = metadata[0].get("DateTimeOriginal", "N/A") if "DateTimeOriginal" in metadata[0] else None

        dummy_exif_data = {
            "SourceFile": filepath,
            "FileName": os.path.basename(filepath),
            "File:FileTypeExtension": os.path.splitext(filepath)[1].lstrip(".").lower(),
            "EXIF:GPSLatitude": GPSLatitude,
            "EXIF:GPSLongitude": GPSLongitude,
            "Composite:GPSLatitude": GPSLatitude,
            "Composite:GPSLongitude": GPSLongitude,
            "EXIF:CreateDate": createDate if createDate else "2025:01:01 01:00:00",
            "QuickTime:CreationDate": createDate if createDate else "2025:01:01 02:00:00",
        }
        return dummy_exif_data

    def ImageMetadata(self, filepath, exif_data):
        extension = os.path.splitext(filepath)[1].lower()
        if extension not in [".jpg", ".jpeg", ".png", ".heic"]:
            return None

        metadata = {
            "file_type": "image",
            "latitude": exif_data.get("Composite:GPSLatitude", "N/A"),
            "longitude": exif_data.get("Composite:GPSLongitude", "N/A"),
            "creation_date": exif_data.get("EXIF:CreateDate", "N/A"),
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
        }

        media_metadata = self.ImageMetadata(filepath, exif_data) or self.VideoMetadata(filepath, exif_data)

        if not media_metadata:
            return None

        base_metadata.update(media_metadata)
        return base_metadata

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

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
            closest = min(self.geo_data, key=lambda g: self.haversine(latitude, longitude, g[0], g[1]))
            logging.info(f"Closest geo data found: {closest}")

            return {
                "city": closest[2],
                "region": closest[3],
                "subregion": closest[4],
                "country_code": closest[5],
                "country": closest[6],
                "latitude": closest[0],
                "longitude": closest[1],
                "distance_km": round(self.haversine(latitude, longitude, closest[0], closest[1]), 2)
            }

        except Exception as e:
            logging.error(f"Error getting geo from coordinates: {e}")
            return None

