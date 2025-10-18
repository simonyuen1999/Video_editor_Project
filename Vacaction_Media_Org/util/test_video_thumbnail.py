#!/usr/bin/env python3
"""
Test script for debugging video thumbnail generation issues
Usage: python test_video_thumbnail.py <video_file_path>
"""

import sys
import os
import subprocess
import logging
from scan_main import MediaOrganizerDB

def test_video_file(filepath):
    """Test video file with enhanced debugging"""
    logging.basicConfig(level=logging.DEBUG)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    print(f"🎬 Testing video file: {filepath}")
    print(f"📊 File size: {os.path.getsize(filepath)} bytes")
    
    # Test with ffprobe first
    print("\n🔍 Running ffprobe analysis...")
    info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', filepath]
    info_result = subprocess.run(info_cmd, capture_output=True, text=True)
    
    if info_result.returncode == 0:
        print("✅ ffprobe successful")
        try:
            import json
            probe_data = json.loads(info_result.stdout)
            streams = probe_data.get('streams', [])
            video_streams = [s for s in streams if s.get('codec_type') == 'video']
            
            print(f"📺 Found {len(video_streams)} video stream(s)")
            for i, stream in enumerate(video_streams):
                duration = stream.get('duration', 'N/A')
                codec = stream.get('codec_name', 'unknown')
                print(f"   Stream {i}: {codec}, duration: {duration}")
        except json.JSONDecodeError:
            print("⚠️  Could not parse ffprobe output")
    else:
        print("❌ ffprobe failed:")
        print(info_result.stderr)
        
    # Test thumbnail generation
    print("\n🖼️  Testing thumbnail generation...")
    db = MediaOrganizerDB()
    result = db.generate_thumbnail(filepath)
    
    if result and os.path.exists(result):
        size = os.path.getsize(result)
        print(f"✅ Thumbnail generated: {result}")
        print(f"📏 Thumbnail size: {size} bytes")
        return True
    else:
        print("❌ Thumbnail generation failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_video_thumbnail.py <video_file_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    success = test_video_file(video_path)
    sys.exit(0 if success else 1)
