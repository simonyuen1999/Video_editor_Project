#!/usr/bin/env python3
"""
Test script to verify the date range functionality
"""
import sqlite3
import os

# Connect to the database
db_path = "/Users/syuen/Video_editor_Project/vacation_media_organizer2/media_organizer.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get the date range
    cursor.execute("""
        SELECT 
            MIN(creation_time) as earliest,
            MAX(creation_time) as latest,
            COUNT(*) as total_files
        FROM media_files 
        WHERE creation_time IS NOT NULL
    """)
    
    result = cursor.fetchone()
    earliest, latest, total_files = result
    
    print(f"Database has {total_files} files with creation times")
    print(f"Earliest: {earliest}")
    print(f"Latest: {latest}")
    
    # Test the date format conversion for datetime-local inputs
    def format_for_datetime_local(date_str):
        """Convert database format to datetime-local format"""
        if not date_str:
            return ''
        
        # Handle the database format with dashes in time part
        formatted = date_str
        if formatted and '-' in formatted and ' ' in formatted:
            # Convert "YYYY-MM-DD HH-MM-SS" to "YYYY-MM-DD HH:MM:SS"
            parts = formatted.split(' ')
            if len(parts) == 2:
                date_part = parts[0]
                time_part = parts[1]
                if time_part.count('-') == 2:  # Format: HH-MM-SS
                    time_part = time_part.replace('-', ':')
                    formatted = f"{date_part} {time_part}"
        
        # Convert to datetime-local format (YYYY-MM-DDTHH:MM)
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(formatted)
            return dt.strftime('%Y-%m-%dT%H:%M')
        except:
            return ''
    
    # Test the conversion
    earliest_input = format_for_datetime_local(earliest)
    latest_input = format_for_datetime_local(latest)
    
    print(f"\nConverted for datetime-local inputs:")
    print(f"Date From: {earliest_input}")
    print(f"Date To: {latest_input}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()