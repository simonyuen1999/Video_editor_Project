from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
            'people_count': self.people_count,
            'activities': self.activities,
            'scenery': self.scenery,
            'talking_detected': self.talking_detected,
            'scanned_at': self.scanned_at
        }
