# Database Enhancement Summary

## Overview
Enhanced the database schema and user configuration workflow to support GPS tracking and web server timezone display configuration.

## Changes Made

### 1. Database Schema Changes

#### Config Table Enhancements
Added two new default configuration entries:
- **offsetTime**: Default value `-04:00` - Web server display timezone offset for converting UTC creation_time to local display time
- **displayTime**: Default value `Toronto` - Web server display timezone location name shown in views

#### Media Files Table Enhancements
Added two new boolean columns:
- **hasGPS**: INTEGER DEFAULT 0 - Tracks whether the media file has GPS coordinates
- **shareGPS**: INTEGER DEFAULT 0 - Flag for whether GPS information should be shared

### 2. Database Logic Updates

#### Enhanced add_media_file() Function
- Automatically sets `hasGPS=1` when latitude and longitude are present
- Sets `shareGPS=0` as default for privacy
- Maintains backward compatibility with existing database structure

#### New configure_timezone_settings() Function
- Interactive user configuration for web server timezone display settings
- Validates timezone offset format (±HH:MM)
- Allows customization of display location name
- Integrates with existing configuration workflow

### 3. User Workflow Integration

The timezone configuration is now automatically triggered:
1. After user sets up base directory configuration
2. Before media scanning begins
3. Provides interactive prompts for web server timezone display customization

## Implementation Details

### Web Server Timezone Display Purpose

The `offsetTime` and `displayTime` config values are used by **web server views** to convert and display creation_time in a consistent local timezone:

**Examples:**
- When config `offsetTime='+08:00'` and media file `creation_time='2025-03-20T16:23:51.000+08:00'`
  - Display: `2025-03-20 4:23:51 PM`
- When config `offsetTime='+08:00'` and media file `creation_time='2025-04-25T18:20:18.000-04:00'`
  - Display: `2025-04-26 06:20:18 AM`

All web views will display the config `offsetTime` and `displayTime` values as labels on top of the view, so users know all thumbnails and lists are using these settings to display media local capture time.

## Implementation Details

### Database Table Structure
```sql
-- Config table (existing, enhanced with new entries)
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Media files table (enhanced with GPS tracking)
CREATE TABLE IF NOT EXISTS media_files (
    -- ... existing columns ...
    hasGPS INTEGER DEFAULT 0,
    shareGPS INTEGER DEFAULT 0
);
```

### Key Functions Added/Modified

1. **configure_timezone_settings(db)**
   - Location: Lines 881-950
   - Purpose: Interactive web server timezone display configuration
   - Features: Input validation, current value display, error handling, example display conversions

2. **add_media_file() - Enhanced**
   - Location: Lines 277-325
   - Enhancement: Automatic GPS detection and column population
   - Logic: Sets hasGPS=1 when both latitude and longitude exist

3. **Main workflow integration**
   - Location: Line 1206
   - Integration: Called after base directory configuration
   - Context: Part of initial setup process for web server timezone display

## Benefits

1. **GPS Awareness**: Database now tracks which files have GPS information
2. **Web Server Timezone Display**: Users can set consistent timezone for web view display
3. **Privacy Control**: shareGPS flag allows control over GPS data sharing
4. **Backward Compatibility**: Existing databases work with new schema
5. **User-Friendly**: Interactive configuration with input validation
6. **Consistent Display**: All web views show media capture time in configured local timezone
7. **Clear Context**: Timezone offset and location labels shown on all web views

## Usage Notes

- Default timezone is set to `-04:00` (EDT/Toronto) for web display
- Configuration is persistent and stored in database
- GPS detection is automatic based on coordinate presence
- Timezone settings control web server view display conversion
- Import process maintains original creation_time with proper timezone information
- Web views convert UTC creation_time to configured local display time

## Integration with Existing Features

This enhancement complements the previously implemented timezone conversion system:
- Web interface displays capture time in configured local timezone
- Database tracks GPS capability per file
- Configuration provides consistent timezone display across all web views
- Import process logic determines and saves proper creation_time with timezone
- Web server converts UTC creation_time using config offsetTime for display
- Display labels show current timezone context to users

## Testing Status

- ✅ Syntax validation passed
- ✅ Database schema modifications implemented
- ✅ User workflow integration completed
- ✅ Function definitions and integration verified
- 🔄 Runtime testing pending (requires actual execution)

## Next Steps for Validation

1. Run Main_scan_media.py to test new configuration workflow
2. Verify database creation with new columns
3. Test timezone configuration user interaction
4. Validate GPS detection logic with sample files
5. Confirm web interface compatibility with enhanced database