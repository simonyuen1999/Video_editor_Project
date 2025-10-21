#!/usr/bin/env python3
"""
Test script to verify the new date extraction logic in metadata_extractor.py
"""

def test_date_extraction_logic():
    """Test the new date extraction priority logic"""
    
    print("=" * 60)
    print("Testing New Date Extraction Logic")
    print("=" * 60)
    
    # Test cases simulating different metadata scenarios
    test_cases = [
        {
            "name": "Both CreationDate and CreateDate exist",
            "metadata": {
                "CreationDate": "2023:10:05 14:30:00+08:00",
                "CreateDate": "2023:10:05 12:30:00",
                "DateTimeOriginal": "2023:10:05 11:30:00",
                "GPSDateTime": "2023:10:05 13:30:00Z"
            },
            "expected": "2023-10-05 14:30:00"  # Should use CreationDate
        },
        {
            "name": "Only CreateDate exists",
            "metadata": {
                "CreateDate": "2023:10:05 12:30:00",
                "DateTimeOriginal": "2023:10:05 11:30:00",
                "GPSDateTime": "2023:10:05 13:30:00Z"
            },
            "expected": "2023-10-05 12:30:00"  # Should use CreateDate
        },
        {
            "name": "Neither CreationDate nor CreateDate exist",
            "metadata": {
                "DateTimeOriginal": "2023:10:05 11:30:00",
                "GPSDateTime": "2023:10:05 13:30:00Z"
            },
            "expected": "2023-10-05 11:30:00"  # Should use DateTimeOriginal
        },
        {
            "name": "Only GPSDateTime exists",
            "metadata": {
                "GPSDateTime": "2023:10:05 13:30:00Z"
            },
            "expected": "2023-10-05 13:30:00"  # Should use GPSDateTime
        },
        {
            "name": "CreationDate is None but CreateDate exists",
            "metadata": {
                "CreationDate": None,
                "CreateDate": "2023:10:05 12:30:00",
                "DateTimeOriginal": "2023:10:05 11:30:00"
            },
            "expected": "2023-10-05 12:30:00"  # Should use CreateDate
        }
    ]
    
    # Simulate the new logic
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input metadata: {test_case['metadata']}")
        
        metadata = [test_case['metadata']]  # Wrap in list like exiftool output
        CreateDate = None
        
        # Apply the new logic
        creation_date_raw = metadata[0].get("CreationDate", None)
        create_date_raw = metadata[0].get("CreateDate", None)
        datetime_original_raw = metadata[0].get("DateTimeOriginal", None)
        gps_datetime_raw = metadata[0].get("GPSDateTime", None)
        
        # Check CreationDate first (highest priority when available)
        if creation_date_raw and creation_date_raw != "N/A":
            # CreationDate format: 2023:10:05 14:30:00+08:00, we only want the date and time part
            CreateDate = creation_date_raw.split("+")[0].replace(":", "-", 2)
            source = "CreationDate"
        
        # If CreationDate is None, use CreateDate
        elif create_date_raw and create_date_raw != "N/A":
            # Convert YYYY:MM:DD HH:MM:SS format to YYYY-MM-DD HH:MM:SS format
            CreateDate = create_date_raw.replace(":", "-", 2)  # Replace only first 2 colons
            source = "CreateDate"
        
        # If both CreationDate and CreateDate are None, fall back to DateTimeOriginal
        elif datetime_original_raw and datetime_original_raw != "N/A":
            # Convert YYYY:MM:DD HH:MM:SS format to YYYY-MM-DD HH:MM:SS format
            CreateDate = datetime_original_raw.replace(":", "-", 2)  # Replace only first 2 colons
            source = "DateTimeOriginal"
        
        # Final fallback to GPSDateTime
        elif gps_datetime_raw and gps_datetime_raw != "N/A":
            # GPSDateTime format: 2023:10:05 14:30:00Z, replace the 'Z' and convert format
            CreateDate = gps_datetime_raw.replace("Z", "").replace(":", "-", 2)
            source = "GPSDateTime"
        else:
            source = "None"
        
        print(f"Result: {CreateDate} (from {source})")
        print(f"Expected: {test_case['expected']}")
        
        if CreateDate == test_case['expected']:
            print("✅ PASS")
        else:
            print("❌ FAIL")
        
        print("-" * 40)

if __name__ == "__main__":
    test_date_extraction_logic()