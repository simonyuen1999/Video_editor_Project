#!/bin/bash

# Check if a media file was provided
if [ -z "$1" ]; then
  echo "Usage: $0 MEDIA_FILE"
  exit 1
fi

# Run exiftool and filter date/time fields
exiftool -j -n "$1" | grep -i -e DateTimeOriginal -e CreationDate -e CreateDate -e ModifyDate -e OffsetTime -e filetype -e mime -e gpsposition -e Altitude -e Latitude -e LensID

