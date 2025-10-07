
from importlib.metadata import metadata
from math import radians, sin, cos, sqrt, atan2
import os
import subprocess
import json
import logging
from datetime import datetime
import pickle
from pathlib import Path

class MetadataExtractor:
    def __init__(self, geo_list_path='geo_chinese_.list'):

        self.geo_list_path = geo_list_path
        if not os.path.exists(self.geo_list_path):
            logging.warning(f"File {self.geo_list_path} not found. Geolocation enhancement will be disabled.")
            self.geo_list_path = None
        else:
            # Read and parse geo.list comma separator CSV file and store in memory as a list of tuples
            # This is the first line of the CSV file:
            #   City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
            self.geo_data = []
            with open(self.geo_list_path, 'r', encoding='utf-8') as f:
                # Skip header line
                next(f)
                for line in f:
                    # Each line is comma-separated values and values are
                    #  0:City_en,1:City_zn,2:Region_en,3:Region_zn,4:Subregion_en,5:Subregion_zn,6:CountryCode,7:Country_en,8:Country_zn,9:TimeZone,10:Latitude,11:Longitude
                    # logging.info(f"Parsing line in geo.list: {line.strip()}")
                    parts = line.strip().split(',')
                    try:
                        city_en = parts[0]
                        city_zn = parts[1]
                        region_en = parts[2]
                        region_zn = parts[3]
                        subregion_en = parts[4]
                        subregion_zn = parts[5]
                        country_code = parts[6]
                        country_en = parts[7]
                        country_zn = parts[8]
                        timezone = parts[9]
                        lat = float(parts[10])
                        lon = float(parts[11])
                        self.geo_data.append((lat, lon, city_en, city_zn, region_en, region_zn, subregion_en, subregion_zn, country_code, country_en, country_zn, timezone))
                    except ValueError:
                        logging.error(f"Error parsing line in geo.list: {line}")
                        continue
            logging.info(f"Loaded {len(self.geo_data)} entries from {self.geo_list_path}")

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

        # pretty print metadata for debugging
        # print(json.dumps(metadata, indent=3))
        # input("Paused for debugging. Press Enter to continue...")

        fileExt = os.path.splitext(filepath)[1].lstrip(".").lower()

        Latitude  = metadata[0].get("GPSLatitude", "N/A") if "GPSLatitude" in metadata[0] else None
        Longitude = metadata[0].get("GPSLongitude", "N/A") if "GPSLongitude" in metadata[0] else None

        CreateDate = None
        #if "CreationDate" in metadata[0]:
        #    # CreateDate format: 2023:10:05 14:30:00+08:00, we only want the date and time part
        #    CreateDate = metadata[0].get("CreationDate", "N/A").split("+")[0]

        #if "GPSDateTime" in metadata[0]:
        #    # GPSDateTime format: 2023:10:05 14:30:00Z, replace the 'Z'
        #    CreateDate = metadata[0].get("GPSDateTime", "N/A").replace("Z", "")

        #if "DateTimeOriginal" in metadata[0]:
        #    CreateDate = metadata[0].get("DateTimeOriginal", "N/A")

        if "CreateDate" in metadata[0]:
            CreateDate = metadata[0].get("CreateDate", "N/A")

        # if fileExt in ["mp4", "mov"]:
        #if CreateDate is None or CreateDate == "N/A":
        #    print(f"\nFile detected: {filepath} no CreateDate")
        #    print(json.dumps(metadata[0], indent=3))
        #    # input("Paused for debugging. Press Enter to continue...")

        dummy_exif_data = {
            "SourceFile": filepath,
            "FileName": os.path.basename(filepath),
            "FileTypeExtension": os.path.splitext(filepath)[1].lstrip(".").lower(),
            "Latitude": Latitude,
            "Longitude": Longitude,
            "CreateDate": CreateDate,
        }
        return dummy_exif_data

    def extract_metadata(self, filepath):
        fileType = 'Undefined'
        extension = os.path.splitext(filepath)[1].lower()
        if extension in [".jpg", ".jpeg", ".png", ".heic"]:
            fileType = 'Image'
        elif extension in [".mp4", ".mov"]:
            fileType = 'Video'
        else:
            logging.warning(f"Unsupported file type for {filepath}. Skipping.")
            return None
        
        exif_data = self._run_exiftool(filepath)
        if not exif_data:
            return None

        stat_info = os.stat(filepath)
        base_metadata = {
            "filepath": os.path.abspath(filepath),   # exif_data.get("SourceFile", filepath),
            "filename": os.path.basename(filepath),  # exif_data.get("FileName", os.path.basename(filepath)),
            "file_extension": exif_data.get("FileTypeExtension", extension),
            "file_type": fileType,
            "size": stat_info.st_size,
            "creation_time": exif_data.get("CreateDate", None),
            "latitude": exif_data.get("Latitude", None),
            "longitude": exif_data.get("Longitude", None),
        }
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

            # 0:lat, 1:lon, 2:city_en, 3:city_zn, 4:region_en, 5:region_zn, 6:subregion_en, 7:subregion_zn, 8:country_code, 9:country_en, 10:country_zn, 11:timezone
            return {
                "latitude": latitude,   # closest[0],
                "longitude": longitude, # closest[1],
                "city_en": closest[2],
                "city_zh": closest[3],
                "region_en": closest[4],
                "region_zh": closest[5],
                "subregion_en": closest[6],
                "subregion_zh": closest[7],
                "country_code": closest[8],
                "country_en": closest[9],
                "country_zh": closest[10],
                "timezone": closest[11],
                "distance_km": round(self.haversine(latitude, longitude, closest[0], closest[1]), 2)
            }
        except Exception as e:
            logging.error(f"Error getting geo from coordinates: {e}")
            return None