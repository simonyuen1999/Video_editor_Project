import exiftool
from mediameta import ImageMetadata, VideoMetadata
import datetime
import os
from geopy.geocoders import Nominatim

def extract_metadata(file_path):
    metadata = {
        "file_path": file_path,
        "creation_date": None,
        "creation_time": None,
        "latitude": None,
        "longitude": None,
        "city": None,
        "country": None,
    }

    try:
        # Try mediameta first for a unified approach
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            meta = ImageMetadata(file_path)
        elif file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
            meta = VideoMetadata(file_path)
        else:
            print(f"Unsupported file type for mediameta: {file_path}")
            meta = None

        if meta:
            # Date and Time
            if meta.date_created:
                metadata["creation_date"] = meta.date_created.strftime("%Y-%m-%d")
                metadata["creation_time"] = meta.date_created.strftime("%H:%M:%S")
            elif meta.date_modified:
                metadata["creation_date"] = meta.date_modified.strftime("%Y-%m-%d")
                metadata["creation_time"] = meta.date_modified.strftime("%H:%M:%S")

            # Geographic Location
            if meta.gps_latitude and meta.gps_longitude:
                metadata["latitude"] = meta.gps_latitude
                metadata["longitude"] = meta.gps_longitude
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="media_organizer_app")
                location = geolocator.reverse(f"{metadata["latitude"]}, {metadata["longitude"]}")
                if location:
                    address = location.raw.get("address", {})
                    metadata["city"] = address.get("city") or address.get("town") or address.get("village")
                    metadata["country"] = address.get("country")

    except Exception as e:
        print(f"Error with mediameta for {file_path}: {e}")

    # Fallback to PyExifTool for more comprehensive data, especially for videos or if mediameta fails
    if not metadata["creation_date"] or not metadata["latitude"]:
        try:
            with exiftool.ExifToolHelper() as et:
                exif_data = et.get_metadata(file_path)
                if exif_data:
                    # ExifTool returns a list of dicts, usually one per file
                    exif_data = exif_data[0]

                    # Date and Time
                    if 'EXIF:DateTimeOriginal' in exif_data:
                        dt_str = exif_data['EXIF:DateTimeOriginal']
                        dt_obj = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                        metadata["creation_date"] = dt_obj.strftime("%Y-%m-%d")
                        metadata["creation_time"] = dt_obj.strftime("%H:%M:%S")
                    elif 'QuickTime:CreateDate' in exif_data:
                        dt_str = exif_data['QuickTime:CreateDate']
                        dt_obj = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                        metadata["creation_date"] = dt_obj.strftime("%Y-%m-%d")
                        metadata["creation_time"] = dt_obj.strftime("%H:%M:%S")
                    elif 'File:FileModifyDate' in exif_data:
                        # Fallback to file modification date if creation date is not found
                        dt_str = exif_data['File:FileModifyDate'].split('+')[0].strip() # Remove timezone info
                        dt_obj = datetime.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                        metadata["creation_date"] = dt_obj.strftime("%Y-%m-%d")
                        metadata["creation_time"] = dt_obj.strftime("%H:%M:%S")

                    # Geographic Location
                    if 'GPS:GPSLatitude' in exif_data and 'GPS:GPSLongitude' in exif_data:
                        metadata["latitude"] = exif_data['GPS:GPSLatitude']
                        metadata["longitude"] = exif_data['GPS:GPSLongitude']
                        geolocator = Nominatim(user_agent="media_organizer_app")
                        location = geolocator.reverse(f"{metadata["latitude"]}, {metadata["longitude"]}")
                        if location:
                            address = location.raw.get("address", {})
                            metadata["city"] = address.get("city") or address.get("town") or address.get("village")
                            metadata["country"] = address.get("country")

        except Exception as e:
            print(f"Error with PyExifTool for {file_path}: {e}")

    return metadata

if __name__ == '__main__':
    # Example Usage (replace with actual file paths)
    # Create dummy files for testing
    with open("test_image.jpg", "w") as f:
        f.write("dummy image content")
    with open("test_video.mp4", "w") as f:
        f.write("dummy video content")

    image_file = "test_image.jpg"
    video_file = "test_video.mp4"

    print(f"Extracting metadata for {image_file}:")
    img_meta = extract_metadata(image_file)
    print(img_meta)

    print(f"\nExtracting metadata for {video_file}:")
    vid_meta = extract_metadata(video_file)
    print(vid_meta)

    # Clean up dummy files
    os.remove("test_image.jpg")
    os.remove("test_video.mp4")

    # For real testing, you would point to actual media files
    # real_image_path = "/path/to/your/image.jpg"
    # real_video_path = "/path/to/your/video.mp4"
    # print(extract_metadata(real_image_path))
    # print(extract_metadata(real_video_path))

