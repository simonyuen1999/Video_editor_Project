#!python
import sys
import pillow_heif
from PIL import Image
import os

# Register HEIF opener
pillow_heif.register_heif_opener()

# Print all arguments
print("All arguments:", sys.argv)

# Access individual arguments
if len(sys.argv) < 2:
   sys.exit(0)

photofile = sys.argv[1]
print(f'Reading {photofile} file')

try:
    # Load the HEIC file using PIL with pillow-heif
    image = Image.open(photofile)
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Extract EXIF data if available
    exif_data = image.getexif()
    
    if exif_data:
        # Try to get creation date from EXIF
        date_taken = None
        for tag_id, value in exif_data.items():
            tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal' or tag == 'DateTime':
                date_taken = value
                print(f'Date taken: {date_taken}')
                break
        
        if not date_taken:
            print('No date information found in EXIF data')
    else:
        print('No EXIF data found in image')
    
    # Get image info
    print(f'Image size: {image.size}')
    print(f'Image mode: {image.mode}')
    print(f'Image format: {image.format}')
    
    # Save as JPEG if needed
    output_file = photofile.rsplit('.', 1)[0] + '.jpg'
    image.save(output_file, 'JPEG', quality=95)
    print(f'Converted and saved as: {output_file}')
    
except Exception as e:
    print(f'Error processing {photofile}: {e}')
    sys.exit(1)

