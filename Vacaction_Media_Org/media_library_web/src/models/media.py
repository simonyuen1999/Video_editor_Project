from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

def convert_iso8601_to_local_display(iso_datetime_str, timezone_str=None):
    """
    Convert ISO 8601 datetime string with timezone offset to local time for display.
    This function converts the ISO 8601 datetime (which represents the actual local time 
    when the photo was taken) to a display format showing the capture location's local time.
    
    Args:
        iso_datetime_str: ISO 8601 format datetime (e.g., "2023-12-25T14:30:45.123+08:00")
        timezone_str: Optional timezone string from database (e.g., "Asia/Hong_Kong")
        
    Returns:
        String in format "YYYY-MM-DD HH:MM:SS (Local)" showing capture location time
    """
    if not iso_datetime_str:
        return None
        
    try:
        from datetime import datetime, timezone, timedelta
        import re
        
        # Handle ISO 8601 format: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
        if 'T' in iso_datetime_str:
            # Parse ISO 8601 datetime with timezone
            # This datetime already represents the local time when photo was taken
            dt_with_tz = datetime.fromisoformat(iso_datetime_str.replace('Z', '+00:00'))
            
            # Extract the local time component (this is what we want to display)
            # The timezone offset tells us what timezone the photo was taken in
            local_dt = dt_with_tz.replace(tzinfo=None)  # Remove timezone info for display
            
            # Get timezone info for display
            tz_offset = dt_with_tz.utcoffset()
            if tz_offset:
                # Calculate timezone offset for display
                total_seconds = int(tz_offset.total_seconds())
                hours = total_seconds // 3600
                minutes = abs((total_seconds % 3600) // 60)
                
                # Format timezone offset
                if hours >= 0:
                    tz_display = f"UTC+{hours:02d}:{minutes:02d}"
                else:
                    tz_display = f"UTC{hours:03d}:{minutes:02d}"
                
                # Return formatted datetime with timezone indication
                return f"{local_dt.strftime('%Y-%m-%d %H:%M:%S')} ({tz_display})"
            else:
                # No timezone info available
                return f"{local_dt.strftime('%Y-%m-%d %H:%M:%S')} (Local)"
        
        # Handle legacy formats with timezone
        elif '+' in iso_datetime_str or iso_datetime_str.count('-') >= 3:
            # Legacy timezone format: YYYY-MM-DD hh:mm:ss±##:## or YYYY-MM-DD hh:mm:ss±##.##
            
            # Extract datetime and timezone parts
            if '+' in iso_datetime_str:
                datetime_part, tz_part = iso_datetime_str.rsplit('+', 1)
                tz_sign = '+'
            else:
                # Handle negative timezone (more than 2 dashes means timezone present)
                parts = iso_datetime_str.rsplit('-', 1)
                datetime_part = parts[0]
                tz_part = parts[1]
                tz_sign = '-'
            
            # Parse timezone offset
            if ':' in tz_part:
                # Format: HH:MM
                tz_hours, tz_minutes = tz_part.split(':')
            elif '.' in tz_part:
                # Format: HH.MM
                tz_hours, tz_minutes = tz_part.split('.')
            else:
                # Format: HHMM or HH
                if len(tz_part) >= 4:
                    tz_hours = tz_part[:2]
                    tz_minutes = tz_part[2:4]
                else:
                    tz_hours = tz_part
                    tz_minutes = '00'
            
            # Format timezone display
            tz_display = f"UTC{tz_sign}{tz_hours.zfill(2)}:{tz_minutes.zfill(2)}"
            
            # Return formatted datetime with timezone indication
            return f"{datetime_part} ({tz_display})"
        
        else:
            # No timezone information - display as local time
            # Try to parse and reformat for consistency
            try:
                if ' ' in iso_datetime_str and ':' in iso_datetime_str:
                    # Format: YYYY-MM-DD HH:MM:SS
                    dt = datetime.strptime(iso_datetime_str, '%Y-%m-%d %H:%M:%S')
                    return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} (Local)"
                else:
                    return f"{iso_datetime_str} (Local)"
            except ValueError:
                return f"{iso_datetime_str} (Local)"
            
    except Exception as e:
        # Fallback: return original string with local indication if any error occurs
        return f"{iso_datetime_str} (Unknown TZ)" if iso_datetime_str else None

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
