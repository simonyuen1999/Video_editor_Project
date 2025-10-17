#!/bin/bash

# Script to clean up all thumbnail files (_thumb.jpg) from media directories
# Usage: ./cleanup_thumbnails.sh [directory]

MEDIA_DIR="${1:-/Volumes/Extreme SSD 1/Media}"

echo "🧹 Cleaning up thumbnail files in: $MEDIA_DIR"
echo "================================================"

if [ ! -d "$MEDIA_DIR" ]; then
    echo "❌ Error: Directory '$MEDIA_DIR' does not exist"
    exit 1
fi

# Count thumbnails before deletion
THUMB_COUNT=$(find "$MEDIA_DIR" -name "*_thumb.jpg" -type f | wc -l | tr -d ' ')
echo "📊 Found $THUMB_COUNT thumbnail files"

if [ "$THUMB_COUNT" -eq 0 ]; then
    echo "✅ No thumbnail files found - nothing to clean up"
    exit 0
fi

# Ask for confirmation
echo "⚠️  This will DELETE all files matching pattern: *_thumb.jpg"
read -p "Continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting thumbnail files..."
    
    # Delete thumbnail files and count successful deletions
    DELETED=0
    while IFS= read -r -d '' file; do
        if rm "$file" 2>/dev/null; then
            ((DELETED++))
            echo "  Deleted: $(basename "$file")"
        else
            echo "  ❌ Failed to delete: $(basename "$file")"
        fi
    done < <(find "$MEDIA_DIR" -name "*_thumb.jpg" -type f -print0)
    
    echo "✅ Successfully deleted $DELETED thumbnail files"
else
    echo "❌ Operation cancelled"
    exit 1
fi
