from scan_main import MediaOrganizerDB
import logging
import sqlite3
import os

logging.basicConfig(level=logging.DEBUG)

db = MediaOrganizerDB()
conn = sqlite3.connect('media_organizer.db')
cursor = conn.cursor()

# Get first 3 image files from database
cursor.execute("SELECT filepath FROM media_files WHERE file_extension IN ('.jpg', '.heic') LIMIT 3")
results = cursor.fetchall()

for result in results:
    filepath = result[0]
    print(f'\n--- Testing file: {filepath} ---')
    print(f'File exists: {os.path.exists(filepath)}')
    
    if os.path.exists(filepath):
        try:
            thumbnail = db.generate_thumbnail(filepath)
            print(f'Thumbnail result: {thumbnail}')
        except Exception as e:
            print(f'Exception: {e}')
    else:
        print('File does not exist - external drive might be unmounted')

conn.close()
db.close()
