import os
import sys
import argparse
from main import organize_media

def main():
    parser = argparse.ArgumentParser(description="Organize media files into a structured library.")
    parser.add_argument("source_directory", help="Path to the directory containing raw media files.")
    parser.add_argument("library_directory", help="Path to the root directory of the media library.")
    
    args = parser.parse_args()

    print(f"Starting media organization from {args.source_directory} to {args.library_directory}")
    organize_media(args.source_directory, args.library_directory)
    print("Media organization process completed.")

if __name__ == "__main__":
    # Add the current directory to the Python path to ensure main.py is found
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
