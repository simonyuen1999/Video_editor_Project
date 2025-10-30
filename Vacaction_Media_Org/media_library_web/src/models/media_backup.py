from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

def convert_iso8601_to_local_display(iso_datetime_str, timezone_str=None, target_offset=None):
    """
    Convert ISO 8601 datetime string to consistent local display time using config offsetTime.
    This function converts the ISO 8601 datetime to the target timezone specified in config.
    
    Args:
        iso_datetime_str: ISO 8601 format datetime (e.g., "2023-12-25T14:30:45.123+08:00")
        timezone_str: Optional timezone string from database (e.g., "Asia/Hong_Kong") - not used currently
        target_offset: Target timezone offset for display (e.g., "+08:00") from config
        
    Returns:
        String in format "YYYY-MM-DD HH:MM:SS" converted to target timezone for consistent display
    """
    if not iso_datetime_str:
        return None
        
    try:
        from datetime import datetime, timezone, timedelta
        import re
        
        # Parse target offset if provided
        target_tz = None
        if target_offset:
            # Parse target offset format: +HH:MM or -HH:MM
            match = re.match(r'^([+-])(\d{2}):(\d{2})$', target_offset)
            if match:
                sign, hours, minutes = match.groups()
                offset_hours = int(hours) if sign == '+' else -int(hours)
                offset_minutes = int(minutes) if sign == '+' else -int(minutes)
                total_minutes = offset_hours * 60 + offset_minutes
                target_tz = timezone(timedelta(minutes=total_minutes))
        
        # Handle ISO 8601 format: YYYY-MM-DDThh:mm:ss[.###]±HH:MM
        if 'T' in iso_datetime_str:
            # Parse ISO 8601 datetime with timezone
            dt_with_tz = datetime.fromisoformat(iso_datetime_str.replace('Z', '+00:00'))
            
            if target_tz:
                # Convert to target timezone for consistent display
                converted_dt = dt_with_tz.astimezone(target_tz)
                return converted_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # No target timezone - use original behavior
                local_dt = dt_with_tz.replace(tzinfo=None)
                tz_offset = dt_with_tz.utcoffset()
                if tz_offset:
                    total_seconds = int(tz_offset.total_seconds())
                    hours = total_seconds // 3600
                    minutes = abs((total_seconds % 3600) // 60)
                    if hours >= 0:
                        tz_display = f"UTC+{hours:02d}:{minutes:02d}"
                    else:
                        tz_display = f"UTC{hours:03d}:{minutes:02d}"
                    return f"{local_dt.strftime('%Y-%m-%d %H:%M:%S')} ({tz_display})"
                else:
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
            
            # If target_tz is provided, try to convert legacy format too
            if target_tz:
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
                    
                    # Parse and convert
                    dt_naive = datetime.fromisoformat(dt_str)
                    dt_with_tz = dt_naive.replace(tzinfo=original_tz)
                    converted_dt = dt_with_tz.astimezone(target_tz)
                    return converted_dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    # Fall back to original format
                    pass
            
            # Format timezone display for legacy format
            if ':' in tz_part:
                tz_hours, tz_minutes = tz_part.split(':')
            elif '.' in tz_part:
                tz_hours, tz_minutes = tz_part.split('.')
            else:
                if len(tz_part) >= 4:
                    tz_hours = tz_part[:2]
                    tz_minutes = tz_part[2:4]
                else:
                    tz_hours = tz_part
                    tz_minutes = '00'
            
            tz_display = f"UTC{tz_sign}{tz_hours.zfill(2)}:{tz_minutes.zfill(2)}"
            return f"{datetime_part} ({tz_display})"
        
        else:
            # No timezone information - display as local time
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
    
    def to_dict(self):
        """Convert Media object to dictionary for JSON response"""
        return {
            'id': self.id,
            'filepath': self.filepath,
            'filename': self.filename,
            'file_extension': self.file_extension,
            'file_type': self.file_type,
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
            'formatted_creation_time': convert_iso8601_to_local_display(self.creation_time, self.timezone)
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