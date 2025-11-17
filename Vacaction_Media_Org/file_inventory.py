#!/usr/bin/env python3
"""
File Inventory Tool

This script walks through a directory structure and creates a CSV inventory of all files
with their checksums, creation times, modification times, and relative paths.

Usage:
    python file_inventory.py /path/to/directory

Output:
    Creates a CSV file with columns: filename, checksum, creation_time, modify_time, relative_path
    Files are sorted by filename for consistent output.
"""

import os
import sys
import csv
import hashlib
import time
from datetime import datetime
from pathlib import Path


def calculate_checksum(file_path, algorithm='md5'):
    """
    Calculate checksum for a file using the specified algorithm.
    
    Args:
        file_path (str): Path to the file
        algorithm (str): Hash algorithm ('md5', 'sha1', 'sha256', 'crc32', etc.)
    
    Returns:
        str: Hexadecimal checksum string
    """
    try:
        with open(file_path, 'rb') as f:
            if algorithm.lower() == 'crc32':
                # Use zlib.crc32 for CRC32 calculation
                import zlib
                crc = 0
                for chunk in iter(lambda: f.read(8192), b''):
                    crc = zlib.crc32(chunk, crc)
                # Convert to unsigned 32-bit value and return as hex
                return f"{crc & 0xffffffff:08x}"
            else:
                # Use hashlib for other algorithms
                hash_obj = hashlib.new(algorithm)
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)
                return hash_obj.hexdigest()
    except (IOError, OSError) as e:
        print(f"Warning: Could not read file {file_path}: {e}")
        return "ERROR"


def get_file_times(file_path):
    """
    Get creation and modification times for a file.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        tuple: (creation_time_str, modify_time_str) in ISO format
    """
    try:
        stat_info = os.stat(file_path)
        
        # Get modification time
        modify_time = datetime.fromtimestamp(stat_info.st_mtime)
        
        # Get creation time (platform-specific)
        if hasattr(stat_info, 'st_birthtime'):
            # macOS and some BSD systems
            creation_time = datetime.fromtimestamp(stat_info.st_birthtime)
        elif hasattr(stat_info, 'st_ctime') and os.name == 'nt':
            # Windows - st_ctime is creation time
            creation_time = datetime.fromtimestamp(stat_info.st_ctime)
        else:
            # Linux and other Unix systems - use st_ctime as fallback
            # Note: st_ctime is not creation time on Unix, but metadata change time
            creation_time = datetime.fromtimestamp(stat_info.st_ctime)
        
        # Format as ISO 8601 strings
        creation_time_str = creation_time.strftime('%Y-%m-%d %H:%M:%S')
        modify_time_str = modify_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return creation_time_str, modify_time_str
        
    except (OSError, ValueError) as e:
        print(f"Warning: Could not get file times for {file_path}: {e}")
        return "ERROR", "ERROR"


def should_skip_file(filename):
    """
    Check if a file should be skipped (dot files, hidden files, etc.).
    
    Args:
        filename (str): Name of the file
    
    Returns:
        bool: True if file should be skipped
    """
    # Skip files starting with dot
    if filename.startswith('.'):
        return True
    
    # Skip common system/hidden files
    skip_patterns = [
        'Thumbs.db',
        'Desktop.ini',
        '.DS_Store',
        '__pycache__',
        '*.tmp',
        '*.temp'
    ]
    
    filename_lower = filename.lower()
    for pattern in skip_patterns:
        if pattern.startswith('*'):
            if filename_lower.endswith(pattern[1:]):
                return True
        elif filename_lower == pattern.lower():
            return True
    
    return False


def create_file_inventory(root_directory, output_file=None, checksum_algorithm='md5'):
    """
    Create a CSV inventory of all files in the directory tree.
    
    Args:
        root_directory (str): Root directory to scan
        output_file (str): Output CSV file path (optional)
        checksum_algorithm (str): Hash algorithm to use
    
    Returns:
        str: Path to the created CSV file
    """
    root_path = Path(root_directory).resolve()
    
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {root_directory}")
    
    if not root_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root_directory}")
    
    # Generate output filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_dirname = root_path.name.replace(' ', '_').replace('/', '_')
        output_file = f"file_inventory_{safe_dirname}_{timestamp}.csv"
    
    print(f"📁 Scanning directory: {root_path}")
    print(f"💾 Output file: {output_file}")
    print(f"🔐 Checksum algorithm: {checksum_algorithm}")
    print()
    
    # Collect file information
    file_data = []
    total_files = 0
    processed_files = 0
    
    # First pass: count total files for progress indication
    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            if not should_skip_file(filename):
                total_files += 1
    
    print(f"📊 Found {total_files} files to process")
    print()
    
    # Second pass: process files
    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            if should_skip_file(filename):
                continue
            
            processed_files += 1
            file_path = os.path.join(root, filename)
            
            # Calculate relative path (remove root directory)
            relative_path = os.path.relpath(file_path, root_path)
            relative_dir = os.path.dirname(relative_path) if os.path.dirname(relative_path) != '.' else ''
            
            # Show progress
            if processed_files % 50 == 0 or processed_files == total_files:
                print(f"⏳ Processing: {processed_files}/{total_files} files... ({filename})")
            
            try:
                # Get file information
                checksum = calculate_checksum(file_path, checksum_algorithm)
                creation_time, modify_time = get_file_times(file_path)
                
                # Store file data
                file_data.append({
                    'filename': filename,
                    'checksum': checksum,
                    'creation_time': creation_time,
                    'modify_time': modify_time,
                    'relative_path': relative_dir
                })
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                # Add error entry
                file_data.append({
                    'filename': filename,
                    'checksum': 'ERROR',
                    'creation_time': 'ERROR',
                    'modify_time': 'ERROR',
                    'relative_path': relative_dir
                })
    
    # Sort by filename for consistent output
    file_data.sort(key=lambda x: x['filename'].lower())
    
    # Write CSV file
    print(f"\n📝 Writing CSV file: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'checksum', 'creation_time', 'modify_time', 'relative_path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data
        for row in file_data:
            writer.writerow(row)
    
    print(f"✅ Successfully created inventory with {len(file_data)} files")
    print(f"📄 Output saved to: {output_file}")
    
    return output_file


def main():
    """Main function to handle command line arguments and run the inventory."""
    if len(sys.argv) < 2:
        print("Usage: python file_inventory.py <directory_path> [output_file] [checksum_algorithm]")
        print()
        print("Arguments:")
        print("  directory_path     : Directory to scan (required)")
        print("  output_file        : Output CSV file path (optional)")
        print("  checksum_algorithm : Hash algorithm - md5, sha1, sha256, sha512, crc32 (default: md5)")
        print()
        print("Examples:")
        print("  python file_inventory.py /Users/john/Documents")
        print("  python file_inventory.py ./my_folder inventory.csv")
        print("  python file_inventory.py /path/to/data output.csv md5")
        sys.exit(1)
    
    # Parse arguments
    directory = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    checksum_algorithm = sys.argv[3] if len(sys.argv) > 3 else 'md5'
    
    # Validate checksum algorithm
    available_algorithms = list(hashlib.algorithms_available) + ['crc32']
    if checksum_algorithm not in available_algorithms:
        print(f"❌ Error: Unsupported checksum algorithm '{checksum_algorithm}'")
        print(f"Available algorithms: {', '.join(sorted(available_algorithms))}")
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        # Create inventory
        result_file = create_file_inventory(directory, output_file, checksum_algorithm)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"\n🎉 Inventory completed in {elapsed:.2f} seconds")
        print(f"📊 CSV file created: {result_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()