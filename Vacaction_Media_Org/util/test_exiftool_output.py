#!/usr/bin/env python3
"""
Test script to examine the real exiftool output structure for create_time fields.
This will help understand how different date/time fields appear in exiftool output.
"""

import subprocess
import json
import sys
import os

def test_exiftool_output(filepath):
    """Test exiftool output for a specific file"""
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    
    print(f"Testing exiftool output for: {filepath}")
    print("=" * 60)
    
    try:
        # Run exiftool with JSON output
        result = subprocess.run(
            ['exifTool', '-n', '-j', filepath],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print(f"Error running exiftool: {result.stderr}")
            return
            
        metadata = json.loads(result.stdout)
        
        if not metadata:
            print("No metadata found")
            return
            
        file_metadata = metadata[0]
        
        # Check for errors
        if 'Error' in file_metadata:
            print(f"ExifTool error: {file_metadata['Error']}")
            return
        
        print("FULL EXIFTOOL OUTPUT:")
        print(json.dumps(file_metadata, indent=2))
        print("\n" + "=" * 60)
        
        # Extract and display date/time related fields
        print("DATE/TIME FIELDS ANALYSIS:")
        print("=" * 30)
        
        date_fields = [
            'CreationDate',
            'CreateDate', 
            'DateTimeOriginal',
            'GPSDateTime',
            'ModifyDate',
            'FileModifyDate',
            'FileCreateDate',
            'DateCreated',
            'TimeCreated',
            'MediaCreateDate',
            'TrackCreateDate',
        ]
        
        found_dates = {}
        for field in date_fields:
            if field in file_metadata:
                found_dates[field] = file_metadata[field]
                print(f"{field:20}: {file_metadata[field]}")
        
        if not found_dates:
            print("No date/time fields found!")
        
        print("\n" + "=" * 60)
        print("NEW PRIORITY-BASED EXTRACTION LOGIC RESULT:")
        print("=" * 45)
        
        # Simulate new priority-based extraction logic
        CreateDate = None
        source_field = None
        
        # Priority 1: DateTimeOriginal - Original capture time (most reliable)
        if "DateTimeOriginal" in file_metadata:
            raw_date = file_metadata["DateTimeOriginal"]
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.replace(":", "-", 2)  # Replace only first 2 colons
                source_field = "DateTimeOriginal"
        
        # Priority 2: CreateDate - File creation time
        elif "CreateDate" in file_metadata:
            raw_date = file_metadata["CreateDate"]
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.replace(":", "-", 2)  # Replace only first 2 colons
                source_field = "CreateDate"
        
        # Priority 3: CreationDate - Alternative creation time
        elif "CreationDate" in file_metadata:
            raw_date = file_metadata["CreationDate"]
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.split("+")[0].replace(":", "-", 2)
                source_field = "CreationDate"
        
        # Priority 4: GPSDateTime - GPS timestamp (when available)
        elif "GPSDateTime" in file_metadata:
            raw_date = file_metadata["GPSDateTime"]
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.replace("Z", "").replace(":", "-", 2)
                source_field = "GPSDateTime"
        
        # Priority 5: FileCreateDate - File system creation (least reliable)
        elif "FileCreateDate" in file_metadata:
            raw_date = file_metadata["FileCreateDate"]
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.split("+")[0].split("-")[0].replace(":", "-", 2)
                source_field = "FileCreateDate"
        
        if CreateDate and source_field:
            print(f"✅ Selected: {source_field} -> {CreateDate}")
            print(f"   Priority: {['DateTimeOriginal', 'CreateDate', 'CreationDate', 'GPSDateTime', 'FileCreateDate'].index(source_field) + 1}")
        else:
            print("❌ No suitable creation date found!")
        
        print(f"\nFinal CreateDate: {CreateDate}")
        print(f"Source Field: {source_field}")
        
        # Show priority order
        print(f"\nPriority Order Used:")
        priorities = [
            "1. DateTimeOriginal (most reliable)",
            "2. CreateDate",
            "3. CreationDate", 
            "4. GPSDateTime",
            "5. FileCreateDate (least reliable)"
        ]
        for p in priorities:
            print(f"  {p}")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        print(f"Raw output: {result.stdout}")
    except subprocess.SubprocessError as e:
        print(f"Error running exiftool: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_exiftool_output.py <media_file_path>")
        print("\nExample:")
        print("  python test_exiftool_output.py /path/to/your/photo.jpg")
        print("  python test_exiftool_output.py /path/to/your/video.mp4")
        print("\nThis script will show you the complete exiftool output structure")
        print("and how the current date extraction logic processes it.")
        sys.exit(1)
    
    filepath = sys.argv[1]
    test_exiftool_output(filepath)

if __name__ == "__main__":
    main()