#!python
import sys
import os
import subprocess
import json
import re
from datetime import datetime, timedelta

# DJI pocket 3 is using (set) to Toronto time, so the file name needs to shift 12 hour to match Asia time.
# iPhone is using local time, so the creation time is correct.
# Regex pattern for strict filename match
pattern = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.MP4$")
patter2 = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.MP4$")
patter3 = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.HEIC$")
patter4 = re.compile(r"^IMG_\d*\.MOV$")

def get_creation_date(filepath):
    result = subprocess.run(
        ['exiftool', '-j', '-DateTimeOriginal', filepath],
        capture_output=True, text=True
    )
    metadata = json.loads(result.stdout)
    return metadata[0].get('DateTimeOriginal', 'Not found')

def get_mov_creation_date(filepath):
    result = subprocess.run(
        ['exiftool', '-CreateDate', '-s3', filepath],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def proc_dir():
    for photofile in os.listdir("."):

      # Skip the non file or temp file
      if not os.path.isfile(photofile) or photofile.startswith("."):
         continue
   
      # Fixing the old file name, by replace ':' with '-'
      if patter3.match(photofile):
         timestamp = photofile.replace(":", "-")
         os.rename(photofile, timestamp)
         print(f"Renamed: {photofile} → {timestamp}")
         continue
   
      if patter2.match(photofile):
         timestamp = photofile.replace(":", "-").replace(".MP4","")+"_.MP4"
         os.rename(photofile, timestamp)
         print(f"Renamed: {photofile} → {timestamp}")
         continue
   
      # Fix MOV file name with creation time
      if patter4.match(photofile):
         date_time = get_mov_creation_date(photofile)
         timestamp = date_time.replace(":", "-", 2).replace(" ", "_").replace(":", "-")+".MOV"
         print(f"Photo MOV file {photofile} taken on {date_time}, rename to {timestamp}")
         os.rename( photofile, timestamp )
         continue
   
      # Fix the iPhone HEIC photofile with creation time file name
      if photofile.startswith("IMG_") and photofile.lower().endswith(".heic"):
         date_time = get_creation_date(photofile)
         timestamp = date_time.replace(":", "-", 2).replace(" ", "_").replace(":", "-")+".HEIC"
         print(f"Photo file {photofile} taken on {date_time}, rename to {timestamp}")
         os.rename( photofile, timestamp )
         continue
   
      # Fix the DJI video file by adding 12 hr (shift fromo Toronto time to Asia time)
      if pattern.match(photofile):
         base, ext = os.path.splitext(photofile)
         try:
           timestamp = datetime.strptime(base, "%Y-%m-%d_%H-%M-%S")
         except ValueError:
           print(f"Skipping: {photofile} (unparsable timestamp)")
           continue
   
         shifted = timestamp + timedelta(hours=12)
         new_base = shifted.strftime("%Y-%m-%d_%H-%M-%S_")
         new_filename = f"{new_base}{ext}"
   
         os.rename(photofile, new_filename)
         print(f"Renamed: {photofile} → {new_filename}")
         continue

def process_directory(path):
    original_dir = os.getcwd()
    os.chdir(path)

    print(f"Entered: {path}")
    proc_dir()
    os.chdir(original_dir)

def traverse_and_process(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        process_directory(dirpath)

# Example usage
traverse_and_process(".")

