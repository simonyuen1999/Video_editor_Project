from flask import Blueprint, jsonify, request, send_file
from src.models.media import Media, db
import json
import os

media_bp = Blueprint('media', __name__)

@media_bp.route('/media', methods=['GET'])
def get_all_media():
    """Get all media records with optional filtering"""
    try:
        # Get query parameters for filtering
        city = request.args.get('city')
        country = request.args.get('country')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        has_people = request.args.get('has_people')
        talking = request.args.get('talking')
        
        query = Media.query
        
        # Apply filters
        if city:
            query = query.filter(Media.city.ilike(f'%{city}%'))
        if country:
            query = query.filter(Media.country.ilike(f'%{country}%'))
        if date_from:
            query = query.filter(Media.creation_date >= date_from)
        if date_to:
            query = query.filter(Media.creation_date <= date_to)
        if has_people == 'true':
            query = query.filter(Media.people_count > 0)
        if talking == 'true':
            query = query.filter(Media.talking_detected == True)
        
        media_records = query.all()
        
        # Convert to list of dictionaries and parse JSON fields
        result = []
        for media in media_records:
            media_dict = media.to_dict()
            # Parse JSON strings back to lists
            try:
                media_dict['activities'] = json.loads(media_dict['activities']) if media_dict['activities'] else []
            except:
                media_dict['activities'] = []
            try:
                media_dict['scenery'] = json.loads(media_dict['scenery']) if media_dict['scenery'] else []
            except:
                media_dict['scenery'] = []
            result.append(media_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/<int:media_id>', methods=['GET'])
def get_media(media_id):
    """Get a specific media record by ID"""
    try:
        media = Media.query.get_or_404(media_id)
        media_dict = media.to_dict()
        
        # Parse JSON strings back to lists
        try:
            media_dict['activities'] = json.loads(media_dict['activities']) if media_dict['activities'] else []
        except:
            media_dict['activities'] = []
        try:
            media_dict['scenery'] = json.loads(media_dict['scenery']) if media_dict['scenery'] else []
        except:
            media_dict['scenery'] = []
        
        return jsonify(media_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/<int:media_id>/file', methods=['GET'])
def serve_media_file(media_id):
    """Serve the actual media file"""
    try:
        media = Media.query.get_or_404(media_id)
        file_path = media.new_path
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/locations', methods=['GET'])
def get_locations():
    """Get all unique locations (city, country combinations) with media counts"""
    try:
        locations = db.session.query(
            Media.city, 
            Media.country, 
            Media.latitude, 
            Media.longitude,
            db.func.count(Media.id).label('count')
        ).filter(
            Media.city.isnot(None), 
            Media.country.isnot(None),
            Media.latitude.isnot(None),
            Media.longitude.isnot(None)
        ).group_by(
            Media.city, 
            Media.country, 
            Media.latitude, 
            Media.longitude
        ).all()
        
        result = []
        for location in locations:
            result.append({
                'city': location.city,
                'country': location.country,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'count': location.count
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/stats', methods=['GET'])
def get_stats():
    """Get statistics about the media library"""
    try:
        total_media = Media.query.count()
        total_with_location = Media.query.filter(
            Media.latitude.isnot(None), 
            Media.longitude.isnot(None)
        ).count()
        total_with_people = Media.query.filter(Media.people_count > 0).count()
        total_with_talking = Media.query.filter(Media.talking_detected == True).count()
        
        # Get date range
        date_range = db.session.query(
            db.func.min(Media.creation_date).label('earliest'),
            db.func.max(Media.creation_date).label('latest')
        ).first()
        
        return jsonify({
            'total_media': total_media,
            'total_with_location': total_with_location,
            'total_with_people': total_with_people,
            'total_with_talking': total_with_talking,
            'date_range': {
                'earliest': date_range.earliest,
                'latest': date_range.latest
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
