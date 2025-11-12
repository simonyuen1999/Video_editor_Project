# TODO List - Vacation Media Organizer Improvements

## Priority 1: UTC Timestamp Unification

### 1. Change Collect Timestamp to UTC and Unify Database Storage
- [ ] **Database Schema Changes**
  - [ ] Modify `media` table to store all timestamps in UTC format
  - [ ] Add new column `creation_time_utc` (DATETIME) to replace region-specific timestamps
  - [ ] Keep existing tables (journal, config, etc.) unchanged to preserve user data
  - [ ] Create migration script to backup current media table before changes
  
- [ ] **Media Scanning Updates**
  - [ ] Update `metadata_extractor.py` to extract timestamps in UTC
  - [ ] Modify scanning logic to convert all extracted timestamps to UTC before storage
  - [ ] Re-scan all existing media files to populate UTC timestamps
  - [ ] Remove region offset calculations from timestamp extraction
  
- [ ] **Benefits**
  - Eliminates timezone confusion and offset calculation errors
  - Provides consistent timestamp storage across all media files
  - Simplifies sorting and filtering logic in all views

### 2. Enhanced DJI File Timestamp Extraction
- [ ] **ExifTool Integration**
  - [ ] Research ExifTool commands for DJI UTC timestamp extraction
  - [ ] Update `exif_Tool.py` to prioritize EXIF creation time over filename parsing
  - [ ] Add fallback to filename parsing if EXIF data is unavailable
  - [ ] Validate that DJI camera internal timer is synced with phone Mimo app
  
- [ ] **Implementation Steps**
  - [ ] Test ExifTool UTC extraction on sample DJI files
  - [ ] Compare EXIF timestamps vs filename timestamps for accuracy
  - [ ] Update extraction priority: EXIF UTC > EXIF local > filename parsing
  - [ ] Document DJI camera sync requirements for users

## Priority 2: UTC Display with GUI Offset Conversion

### 3. Universal UTC Display System
- [ ] **Frontend Display Updates**
  - [ ] Update all view pages (Daily, City, Map, Journal, Special) to display UTC times
  - [ ] Add timezone offset selector in GUI settings
  - [ ] Implement client-side UTC to local time conversion
  - [ ] Show both UTC and converted local time where helpful
  
- [ ] **User Interface Enhancements**
  - [ ] Add timezone selector dropdown (common timezones + custom offset)
  - [ ] Display format: "2025-03-20 14:30:00 UTC (22:30:00 +08:00)"
  - [ ] Save user's preferred timezone in browser localStorage
  - [ ] Add "Show UTC" toggle option for advanced users

## Priority 3: Media File Management

### 4. Media File Deletion System
- [ ] **Safe Deletion Implementation**
  - [ ] Create backup/trash system before permanent deletion
  - [ ] Add "Delete Media" button in Daily/Special views
  - [ ] Implement confirmation dialog with file preview
  - [ ] Update database to remove deleted file records
  
- [ ] **File System Integration**
  - [ ] Move deleted files to trash folder before permanent removal
  - [ ] Log all deletion operations for audit trail
  - [ ] Add "Restore from Trash" functionality
  - [ ] Implement bulk deletion for multiple files

### 5. Media File Movement Between Time Ranges
- [ ] **Cross-Date Movement System**
  - [ ] Add "Move to Date" functionality in Daily View
  - [ ] Implement drag-and-drop between date pages
  - [ ] Update database timestamps when files are moved
  - [ ] Maintain file system organization
  
- [ ] **User Interface Design**
  - [ ] Add date picker for destination date selection
  - [ ] Show confirmation dialog with old/new timestamps
  - [ ] Update all affected views automatically after move
  - [ ] Add undo functionality for accidental moves

## Priority 4: Enhanced Geo Information

### 6. HEIC Geo Information Sharing
- [ ] **HEIC GPS Extraction**
  - [ ] Research HEIC GPS metadata extraction methods
  - [ ] Update `metadata_extractor.py` to extract GPS from HEIC files
  - [ ] Implement GPS coordinate sharing between related files
  - [ ] Add GPS accuracy and confidence metrics
  
- [ ] **Smart Geo Sharing Logic**
  - [ ] Share GPS from HEIC to nearby non-GPS files (time-based proximity)
  - [ ] Implement "GPS inheritance" for sequential photos/videos
  - [ ] Add manual GPS assignment interface
  - [ ] Show GPS source info (direct, shared, manual) in file details

## Technical Implementation Notes

### Database Migration Strategy
```sql
-- Example migration for UTC timestamps
ALTER TABLE media_files ADD COLUMN creation_time_utc DATETIME;
UPDATE media_files SET creation_time_utc = datetime(creation_time, 'utc');
-- After validation, drop old timestamp columns
```

### File Organization
```
/project_root/
├── migrations/
│   ├── backup_media_table.sql
│   ├── add_utc_timestamps.sql
│   └── rescan_media_utc.py
├── utils/
│   ├── timezone_converter.py
│   ├── media_file_manager.py
│   └── geo_extractor.py
└── TODO.md (this file)
```

### Testing Requirements
- [ ] Test with mixed timezone media files
- [ ] Validate UTC conversion accuracy
- [ ] Test deletion/restoration workflows
- [ ] Verify GPS sharing algorithms
- [ ] Performance test with large media libraries

## Dependencies and Prerequisites
- [ ] ExifTool installation and configuration
- [ ] Database backup procedures
- [ ] JavaScript timezone libraries for frontend
- [ ] File system permissions for deletion/movement
- [ ] GPS coordinate validation libraries

## Estimated Timeline
- **Phase 1 (UTC Conversion)**: 2-3 weeks
- **Phase 2 (Display Updates)**: 1-2 weeks  
- **Phase 3 (File Management)**: 2-3 weeks
- **Phase 4 (Geo Enhancement)**: 1-2 weeks
- **Testing & Polish**: 1 week

---
*Created: November 12, 2025*
*Project: Vacation Media Organizer*
*Status: Planning Phase*