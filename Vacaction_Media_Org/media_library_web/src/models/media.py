from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

def convert_iso8601_to_local_display(iso_datetime_str, timezone_str=None):
    """
    Convert ISO 8601 datetime string with timezone offset to local time for display.
    
    Args:
        iso_datetime_str: ISO 8601 format datetime (e.g., "2023-12-25T14:30:45.123+08:00")
        timezone_str: Optional timezone string from database (e.g., "Asia/Hong_Kong")
        
    Returns:
        String in format "YYYY-MM-DD HH:MM:SS" in local timezone for display
    """
    if not iso_datetime_str:
        return None
        
    try:
        # Handle ISO 8601 format: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
        if 'T' in iso_datetime_str:
            # Extract datetime part and timezone offset
            if '+' in iso_datetime_str:
                datetime_part, tz_offset = iso_datetime_str.split('+')
                tz_sign = 1
            elif iso_datetime_str.count('-') > 2:  # Has timezone (more than 2 dashes)
                parts = iso_datetime_str.rsplit('-', 1)
                datetime_part = parts[0]
                tz_offset = parts[1]
                tz_sign = -1
            else:
                # No timezone, treat as local
                datetime_part = iso_datetime_str
                tz_offset = None
                tz_sign = 0
            
            # Parse the datetime part
            try:
                # Try with subseconds first
                dt = datetime.strptime(datetime_part, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                try:
                    # Try without subseconds
                    dt = datetime.strptime(datetime_part, '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    # Fallback: return original string if parsing fails
                    return iso_datetime_str
            
            # For display purposes, we'll return the datetime in a readable format
            # The timezone offset is already "baked into" the datetime when it was extracted
            # so we just need to format it nicely for display
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Handle legacy formats
        elif '+' in iso_datetime_str or iso_datetime_str.count('-') >= 3:
            # Legacy timezone format: YYYY-MM-DD hh:mm:ss±##.##
            if '+' in iso_datetime_str:
                time_part = iso_datetime_str.rsplit('+', 1)[0]
            else:
                time_part = iso_datetime_str.rsplit('-', 1)[0]
            return time_part  # Already in YYYY-MM-DD HH:MM:SS format
        
        else:
            # Legacy format: YYYY-MM-DD HH:MM:SS
            return iso_datetime_str
            
    except Exception as e:
        # Fallback: return original string if any error occurs
        return iso_datetime_str

class Media(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filepath = db.Column(db.String(500), unique=True, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_type = db.Column(db.String(50))
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
    activities = db.Column(db.Text)  # JSON string
    scenery = db.Column(db.Text)     # JSON string
    talking_detected = db.Column(db.Boolean, default=False)
    scanned_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        # Convert creation_time from ISO 8601 to local display format
        display_creation_time = convert_iso8601_to_local_display(self.creation_time, self.timezone)
        
        return {
            'id': self.id,
            'filepath': self.filepath,
            'filename': self.filename,
            'file_extension': self.file_extension,
            'file_type': self.file_type,
            'size': self.size,
            'creation_time': display_creation_time,  # Converted to local display format
            'creation_time_raw': self.creation_time,  # Keep original ISO 8601 for reference
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
            'activities': self.activities,
            'scenery': self.scenery,
            'talking_detected': self.talking_detected,
            'scanned_at': self.scanned_at
        }

class Config(db.Model):
    __tablename__ = 'config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())
    updated_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())
    
    @staticmethod
    def get_value(key, default=None):
        """Get a configuration value by key"""
        config = Config.query.filter_by(key=key).first()
        return config.value if config else default
    
    @staticmethod
    def get_base_directory():
        """Get the base directory from configuration"""
        return Config.get_value('base_directory')
