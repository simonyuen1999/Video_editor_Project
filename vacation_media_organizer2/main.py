'''
Main script to orchestrate the media organization workflow.
'''

import os
import shutil
import json
from database_manager import create_connection, create_table, insert_media_record
from metadata_extractor import extract_metadata
from semantic_analyzer import analyze_video

def organize_media(source_dir, library_dir):
    """
    Organizes media files from a source directory into a structured library.

    Args:
        source_dir (str): The directory containing the media files to organize.
        library_dir (str): The root directory of the media library.
    """
    # Create the library directory if it doesn't exist
    os.makedirs(library_dir, exist_ok=True)
    organized_by_dir = os.path.join(library_dir, "OrganizedBy")
    os.makedirs(organized_by_dir, exist_ok=True)

    # Initialize database
    conn = create_connection()
    if conn:
        create_table(conn)
    else:
        print("Error: Could not connect to database.")
        return

    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)
        if not os.path.isfile(source_path):
            continue

        print(f"Processing {filename}...")

        # 1. Extract Metadata
        metadata = extract_metadata(source_path)

        # 2. Perform Semantic Analysis (for videos)
        semantic_info = {}
        if filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            semantic_info = analyze_video(source_path)

        # 3. Organize File by Date
        new_path = None
        if metadata["creation_date"]:
            year, month, day = metadata["creation_date"].split("-")
            date_dir = os.path.join(library_dir, year, month, day)
            os.makedirs(date_dir, exist_ok=True)
            new_path = os.path.join(date_dir, filename)
            shutil.move(source_path, new_path)
        else:
            # If no date, move to an 'unsorted' directory
            unsorted_dir = os.path.join(library_dir, "unsorted")
            os.makedirs(unsorted_dir, exist_ok=True)
            new_path = os.path.join(unsorted_dir, filename)
            shutil.move(source_path, new_path)

        # 4. Create Symbolic Links (by location and scenery)
        # Location
        if metadata["city"] and metadata["country"] and new_path:
            location_dir = os.path.join(organized_by_dir, "Location", f"{metadata["city"]}_{metadata["country"]}")
            os.makedirs(location_dir, exist_ok=True)
            try:
                os.symlink(new_path, os.path.join(location_dir, filename))
            except FileExistsError:
                print(f"Symlink already exists for {filename} in {location_dir}")
        
        # Scenery
        if semantic_info.get("scenery") and new_path:
            for scene in semantic_info["scenery"]:
                scenery_dir = os.path.join(organized_by_dir, "Scenery", scene)
                os.makedirs(scenery_dir, exist_ok=True)
                try:
                    os.symlink(new_path, os.path.join(scenery_dir, filename))
                except FileExistsError:
                    print(f"Symlink already exists for {filename} in {scenery_dir}")

        # 5. Save information to Database
        record = {
            "original_path": source_path,
            "new_path": new_path,
            "creation_date": metadata.get("creation_date"),
            "creation_time": metadata.get("creation_time"),
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "city": metadata.get("city"),
            "country": metadata.get("country"),
            "people_count": semantic_info.get("people_count", 0),
            "activities": json.dumps(semantic_info.get("activities", [])), # Store as JSON string
            "scenery": json.dumps(semantic_info.get("scenery", [])),       # Store as JSON string
            "talking_detected": semantic_info.get("talking_detected", False)
        }
        insert_media_record(conn, record)

    conn.close()
    print(f"\nMedia organization complete. Library created at: {library_dir}")
    print(f"Metadata and analysis results saved to: {library_dir}/media_library.db")

if __name__ == '__main__':
    # Example Usage
    # Create dummy source directory and files for testing
    source_directory = "vacation_media"
    os.makedirs(source_directory, exist_ok=True)
    with open(os.path.join(source_directory, "test_image.jpg"), "w") as f:
        f.write("dummy image")
    with open(os.path.join(source_directory, "test_video.mp4"), "w") as f:
        f.write("dummy video")

    library_directory = "MyMediaLibrary"

    organize_media(source_directory, library_directory)

    # Clean up dummy directories
    shutil.rmtree(source_directory)
    # Keep the library for inspection
    # shutil.rmtree(library_directory)

