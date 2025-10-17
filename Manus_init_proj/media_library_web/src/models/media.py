from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Media(db.Model):
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    original_path = db.Column(db.String(500), nullable=False)
    new_path = db.Column(db.String(500), nullable=False)
    creation_date = db.Column(db.String(20))
    creation_time = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    people_count = db.Column(db.Integer, default=0)
    activities = db.Column(db.Text)  # JSON string
    scenery = db.Column(db.Text)     # JSON string
    talking_detected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'original_path': self.original_path,
            'new_path': self.new_path,
            'creation_date': self.creation_date,
            'creation_time': self.creation_time,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city': self.city,
            'country': self.country,
            'people_count': self.people_count,
            'activities': self.activities,
            'scenery': self.scenery,
            'talking_detected': self.talking_detected,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
