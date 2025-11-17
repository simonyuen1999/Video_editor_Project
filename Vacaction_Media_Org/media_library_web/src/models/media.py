from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

def convert_iso8601_to_local_display(iso_datetime_str, timezone_str=None, target_offset=None):
    """
    Convert ISO 8601 datetime string to consistent local display time using config offsetTime.
    Always returns format "YYYY-MM-DD hh:mm:ss AM/PM" for consistent display.
    
    Args:
        iso_datetime_str: ISO 8601 format datetime (e.g., "2023-12-25T14:30:45.123+08:00")
        timezone_str: Optional timezone string from database (e.g., "Asia/Hong_Kong") - not used currently
        target_offset: Target timezone offset for display (e.g., "+08:00") from config
        
    Returns:
        String in format "YYYY-MM-DD hh:mm:ss AM/PM" converted to target timezone for consistent display
    """
    if not iso_datetime_str:
        return None
        
    try:
        from datetime import datetime, timezone, timedelta
        import re
        
        # Default target timezone (use +08:00 if not specified)
        target_tz = timezone(timedelta(hours=8))  # Default to +08:00
        
        # Parse target offset if provided
        if target_offset:
            # Parse target offset format: +HH:MM or -HH:MM
            match = re.match(r'^([+-])(\d{2}):(\d{2})$', target_offset)
            if match:
                sign, hours, minutes = match.groups()
                offset_hours = int(hours) if sign == '+' else -int(hours)
                offset_minutes = int(minutes) if sign == '+' else -int(minutes)
                total_minutes = offset_hours * 60 + offset_minutes
                target_tz = timezone(timedelta(minutes=total_minutes))
        
        # Clean up malformed datetime strings (e.g., "2025-03-20T05:59:12.157Z+08:00")
        clean_datetime_str = iso_datetime_str
        if 'Z+' in clean_datetime_str or 'Z-' in clean_datetime_str:
            # Remove the Z and keep only the timezone offset
            clean_datetime_str = re.sub(r'Z([+-]\d{2}:\d{2})$', r'\1', clean_datetime_str)
        
        # Handle ISO 8601 format: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
        if 'T' in clean_datetime_str:
            # Replace Z with +00:00 for proper parsing
            if clean_datetime_str.endswith('Z'):
                clean_datetime_str = clean_datetime_str.replace('Z', '+00:00')
            
            # Parse ISO 8601 datetime with timezone
            dt_with_tz = datetime.fromisoformat(clean_datetime_str)
            
            # Always convert to target timezone and return 12-hour format
            converted_dt = dt_with_tz.astimezone(target_tz)
            return converted_dt.strftime('%Y-%m-%d %I:%M:%S %p')
        
        # Handle legacy formats with timezone
        elif '+' in clean_datetime_str or clean_datetime_str.count('-') >= 3:
            # Legacy timezone format: YYYY-MM-DD hh:mm:ss±##:## or YYYY-MM-DD hh:mm:ss±##.##
            
            # Extract datetime and timezone parts
            if '+' in clean_datetime_str:
                datetime_part, tz_part = clean_datetime_str.rsplit('+', 1)
                tz_sign = '+'
            else:
                # Handle negative timezone (more than 2 dashes means timezone present)
                parts = clean_datetime_str.rsplit('-', 1)
                datetime_part = parts[0]
                tz_part = parts[1]
                tz_sign = '-'
            
            try:
                # Create datetime with original timezone
                dt_str = datetime_part.replace(' ', 'T')
                if ':' in tz_part:
                    tz_hours, tz_minutes = tz_part.split(':')
                elif '.' in tz_part:
                    tz_hours, tz_minutes = tz_part.split('.')
                else:
                    tz_hours = tz_part[:2] if len(tz_part) >= 2 else tz_part
                    tz_minutes = tz_part[2:4] if len(tz_part) >= 4 else '00'
                
                # Create timezone offset
                offset_hours = int(tz_hours) if tz_sign == '+' else -int(tz_hours)
                offset_minutes = int(tz_minutes) if tz_sign == '+' else -int(tz_minutes)
                original_tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
                
                # Parse and convert with 12-hour format
                dt_naive = datetime.fromisoformat(dt_str)
                dt_with_tz = dt_naive.replace(tzinfo=original_tz)
                converted_dt = dt_with_tz.astimezone(target_tz)
                return converted_dt.strftime('%Y-%m-%d %I:%M:%S %p')
            except:
                # Fall back to simple format conversion
                try:
                    dt = datetime.strptime(datetime_part, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%Y-%m-%d %I:%M:%S %p')
                except:
                    return datetime_part
        
        else:
            # No timezone information - treat as local time and convert to 12-hour format
            try:
                if ' ' in clean_datetime_str and ':' in clean_datetime_str:
                    # Format: YYYY-MM-DD HH:MM:SS
                    dt = datetime.strptime(clean_datetime_str, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%Y-%m-%d %I:%M:%S %p')
                else:
                    # Try parsing without seconds
                    dt = datetime.strptime(clean_datetime_str, '%Y-%m-%d %H:%M')
                    return dt.strftime('%Y-%m-%d %I:%M:%S %p')
            except ValueError:
                # If all parsing fails, return original with fallback formatting
                return clean_datetime_str
            
    except Exception as e:
        return iso_datetime_str

class Media(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filepath = db.Column(db.String(500), unique=True, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    media_type = db.Column(db.String(50))
    size = db.Column(db.Integer)
    creation_time = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    city_en = db.Column(db.String(100))
    city_zh = db.Column(db.String(100))
    region_en = db.Column(db.String(100))
    region_zh = db.Column(db.String(100))
    subregion_en = db.Column(db.String(100))
    subregion_zh = db.Column(db.String(100))
    country_code = db.Column(db.String(10))
    country_en = db.Column(db.String(100))
    country_zh = db.Column(db.String(100))
    timezone = db.Column(db.String(50))
    people_count = db.Column(db.Integer, default=0)
    activities = db.Column(db.Text)
    scenery = db.Column(db.Text)
    talking_detected = db.Column(db.Boolean, default=False)
    hasGPS = db.Column(db.Boolean, default=False)
    shareGPS = db.Column(db.Boolean, default=False)
    scanned_at = db.Column(db.String(50))
    
    def to_dict(self):
        """Convert Media object to dictionary for JSON response"""
        # Get timezone configuration for consistent display
        offset_time = Config.get_value('offsetTime', '+08:00')
        
        return {
            'id': self.id,
            'filepath': self.filepath,
            'filename': self.filename,
            'file_extension': self.file_extension,
            'media_type': self.media_type,
            'size': self.size,
            'creation_time': self.creation_time,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city_en': self.city_en,
            'city_zh': self.city_zh,
            'region_en': self.region_en,
            'region_zh': self.region_zh,
            'subregion_en': self.subregion_en,
            'subregion_zh': self.subregion_zh,
            'country_code': self.country_code,
            'country_en': self.country_en,
            'country_zh': self.country_zh,
            'timezone': self.timezone,
            'people_count': self.people_count,
            'activities': self.activities,
            'scenery': self.scenery,
            'talking_detected': self.talking_detected,
            'hasGPS': self.hasGPS,
            'shareGPS': self.shareGPS,
            'formatted_creation_time': convert_iso8601_to_local_display(self.creation_time, self.timezone, offset_time)
        }

class Config(db.Model):
    __tablename__ = 'config'
    
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.String(50), default=lambda: datetime.now().isoformat())
    updated_at = db.Column(db.String(50), default=lambda: datetime.now().isoformat())
    
    @staticmethod
    def get_value(key, default=None):
        """Get a configuration value by key"""
        config = Config.query.filter_by(key=key).first()
        return config.value if config else default
    
    @staticmethod
    def get_base_directory():
        """Get the base directory from configuration"""
        return Config.get_value('base_directory')
    
    @staticmethod
    def get_thumb_directory():
        """Get the thumbnail directory from configuration"""
        return Config.get_value('thumb_directory')