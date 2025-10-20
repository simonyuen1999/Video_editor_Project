from flask import Blueprint, jsonify, request, send_file, Response
from src.models.media import Media, db
import json
import os
import subprocess
import platform
import mimetypes

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
        talking = request.args.get('talking')
        activity = request.args.get('activity')
        scenery = request.args.get('scenery')
        order = request.args.get('order', 'asc')  # Default to ASC (oldest first)
        
        query = Media.query
        
        # Apply filters based on new schema
        if city:
            query = query.filter(db.or_(
                Media.city_en.ilike(f'%{city}%'),
                Media.city_zh.ilike(f'%{city}%')
            ))
        if country:
            query = query.filter(db.or_(
                Media.country_en.ilike(f'%{country}%'),
                Media.country_zh.ilike(f'%{country}%')
            ))
        if date_from and date_to:
            # Filter by creation_time range (assuming ISO format)
            query = query.filter(
                Media.creation_time.between(date_from, date_to)
            )
        elif date_from:
            query = query.filter(Media.creation_time >= date_from)
        elif date_to:
            query = query.filter(Media.creation_time <= date_to)
            
        if talking == 'true':
            query = query.filter(Media.talking_detected == True)
        elif talking == 'false':
            query = query.filter(Media.talking_detected == False)
        
        # Order by creation_time based on order parameter
        if order.lower() == 'asc':
            query = query.order_by(Media.creation_time.asc())
        else:
            query = query.order_by(Media.creation_time.desc())  # Default DESC (newest first)
        
        media_records = query.all()
        
        # Apply activity and scenery filtering after DB query (since JSON search is complex)
        if activity or scenery:
            filtered_records = []
            for media in media_records:
                include_record = False
                
                if activity:
                    try:
                        # Handle both JSON and comma-separated formats
                        if media.activities:
                            if media.activities.startswith('['):
                                activities = json.loads(media.activities)
                            else:
                                activities = [act.strip() for act in media.activities.split(',') if act.strip()]
                            
                            if any(activity.lower() in act.lower() for act in activities):
                                include_record = True
                    except (json.JSONDecodeError, AttributeError):
                        if media.activities and activity.lower() in media.activities.lower():
                            include_record = True
                
                if scenery and not include_record:
                    try:
                        # Handle both JSON and comma-separated formats
                        if media.scenery:
                            if media.scenery.startswith('['):
                                scenery_items = json.loads(media.scenery)
                            else:
                                scenery_items = [scene.strip() for scene in media.scenery.split(',') if scene.strip()]
                            
                            if any(scenery.lower() in scene.lower() for scene in scenery_items):
                                include_record = True
                    except (json.JSONDecodeError, AttributeError):
                        if media.scenery and scenery.lower() in media.scenery.lower():
                            include_record = True
                
                if include_record:
                    filtered_records.append(media)
            
            media_records = filtered_records
        
        # Convert to list of dictionaries and parse JSON fields
        result = []
        for media in media_records:
            media_dict = media.to_dict()
            # Parse activities and scenery fields (handle both JSON and comma-separated formats)
            try:
                if media_dict['activities']:
                    if media_dict['activities'].startswith('['):
                        media_dict['activities'] = json.loads(media_dict['activities'])
                    else:
                        media_dict['activities'] = [activity.strip() for activity in media_dict['activities'].split(',') if activity.strip()]
                else:
                    media_dict['activities'] = []
            except:
                media_dict['activities'] = []
            try:
                if media_dict['scenery']:
                    if media_dict['scenery'].startswith('['):
                        media_dict['scenery'] = json.loads(media_dict['scenery'])
                    else:
                        media_dict['scenery'] = [scene.strip() for scene in media_dict['scenery'].split(',') if scene.strip()]
                else:
                    media_dict['scenery'] = []
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
        
        # Parse activities and scenery fields (handle both JSON and comma-separated formats)
        try:
            if media_dict['activities']:
                if media_dict['activities'].startswith('['):
                    media_dict['activities'] = json.loads(media_dict['activities'])
                else:
                    media_dict['activities'] = [activity.strip() for activity in media_dict['activities'].split(',') if activity.strip()]
            else:
                media_dict['activities'] = []
        except:
            media_dict['activities'] = []
        try:
            if media_dict['scenery']:
                if media_dict['scenery'].startswith('['):
                    media_dict['scenery'] = json.loads(media_dict['scenery'])
                else:
                    media_dict['scenery'] = [scene.strip() for scene in media_dict['scenery'].split(',') if scene.strip()]
            else:
                media_dict['scenery'] = []
        except:
            media_dict['scenery'] = []
        
        return jsonify(media_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/<int:media_id>/file', methods=['GET'])
def serve_media_file(media_id):
    """Serve the actual media file with streaming support for large files"""
    try:
        media = Media.query.get_or_404(media_id)
        file_path = media.filepath
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # For large files (>10MB), use streaming
        if file_size > 10 * 1024 * 1024:  # 10MB
            def generate():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            response = Response(generate(), mimetype=mime_type)
            response.headers['Content-Length'] = str(file_size)
            response.headers['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            return response
        else:
            # For smaller files, use regular send_file
            return send_file(file_path, as_attachment=False)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/<int:media_id>/thumbnail', methods=['GET'])
def serve_media_thumbnail(media_id):
    """Serve a thumbnail image for fast grid display"""
    try:
        media = Media.query.get_or_404(media_id)
        file_path = media.filepath
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Generate thumbnail file path
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        thumbnail_path = os.path.join(file_dir, f"{name_without_ext}_thumb.jpg")
        
        # Check if thumbnail exists
        if os.path.exists(thumbnail_path):
            # Serve the thumbnail file
            response = send_file(thumbnail_path, as_attachment=False, mimetype='image/jpeg')
            # Add cache headers for better performance
            response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
            response.headers['ETag'] = f'"{media_id}-thumb"'
            return response
        else:
            # Fallback: serve original file with reduced quality headers for images
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.heic', '.webp']:
                response = send_file(file_path, as_attachment=False)
                response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
                response.headers['ETag'] = f'"{media_id}-{media.size}"'
                return response
            else:
                # For videos without thumbnails, return a placeholder or error
                return jsonify({'error': 'Thumbnail not available'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/<int:media_id>/open', methods=['POST'])
def open_media_file(media_id):
    """Open media file with system default application"""
    try:
        media = Media.query.get_or_404(media_id)
        file_path = media.filepath
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Open file with system default application
        system = platform.system()
        if system == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        elif system == 'Windows':
            os.startfile(file_path)
        elif system == 'Linux':
            subprocess.run(['xdg-open', file_path])
        else:
            return jsonify({'error': 'Unsupported operating system'}), 400
            
        return jsonify({'success': True, 'message': f'Opened {media.filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/locations', methods=['GET'])
def get_locations():
    """Get all unique locations (city, country combinations) with media counts"""
    try:
        locations = db.session.query(
            Media.city_en, 
            Media.country_en, 
            Media.latitude, 
            Media.longitude,
            db.func.count(Media.id).label('count')
        ).filter(
            Media.city_en.isnot(None), 
            Media.country_en.isnot(None),
            Media.latitude.isnot(None),
            Media.longitude.isnot(None)
        ).group_by(
            Media.city_en, 
            Media.country_en, 
            Media.latitude, 
            Media.longitude
        ).all()
        
        result = []
        for location in locations:
            result.append({
                'city': location.city_en,
                'country': location.country_en,
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
        total_with_talking = Media.query.filter(Media.talking_detected == True).count()
        
        # Get date range from creation_time
        date_range = db.session.query(
            db.func.min(Media.creation_time).label('earliest'),
            db.func.max(Media.creation_time).label('latest')
        ).first()
        
        return jsonify({
            'total_media': total_media,
            'total_with_location': total_with_location,
            'total_with_talking': total_with_talking,
            'date_range': {
                'earliest': date_range.earliest,
                'latest': date_range.latest
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/cities', methods=['GET'])
def get_cities():
    """Get all unique cities in ascending order with both English and Chinese names"""
    try:
        cities = db.session.query(Media.city_en, Media.city_zh).filter(
            Media.city_en.isnot(None), 
            Media.city_en != ''
        ).distinct().order_by(Media.city_en.asc()).all()
        
        city_list = []
        for city_en, city_zh in cities:
            display_name = f"{city_en} | {city_zh}" if city_zh else city_en
            city_list.append({
                'value': city_en,
                'display': display_name
            })
        
        return jsonify(city_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/countries', methods=['GET'])
def get_countries():
    """Get all unique countries in ascending order with both English and Chinese names"""
    try:
        countries = db.session.query(Media.country_en, Media.country_zh).filter(
            Media.country_en.isnot(None), 
            Media.country_en != ''
        ).distinct().order_by(Media.country_en.asc()).all()
        
        country_list = []
        for country_en, country_zh in countries:
            display_name = f"{country_en} | {country_zh}" if country_zh else country_en
            country_list.append({
                'value': country_en,
                'display': display_name
            })
        
        return jsonify(country_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/activities', methods=['GET'])
def get_activities():
    """Get all unique activities from all media records"""
    try:
        # Get all media records that have activities
        media_records = Media.query.filter(
            Media.activities.isnot(None),
            Media.activities != '',
            Media.activities != '[]'
        ).all()
        
        all_activities = set()
        
        for media in media_records:
            if media.activities:
                # Handle both JSON array format and comma-separated string format
                try:
                    # Try parsing as JSON first
                    if media.activities.startswith('['):
                        activities = json.loads(media.activities)
                    else:
                        # Handle comma-separated string format
                        activities = [activity.strip() for activity in media.activities.split(',') if activity.strip()]
                    
                    for activity in activities:
                        # Filter out people-related activities and clean up the activity name
                        activity_clean = activity.strip()
                        if (activity_clean and 
                            not activity_clean.lower().startswith('people') and 
                            'people' not in activity_clean.lower() and
                            'person' not in activity_clean.lower()):
                            all_activities.add(activity_clean)
                except (json.JSONDecodeError, AttributeError) as e:
                    # Handle comma-separated string format as fallback
                    if isinstance(media.activities, str):
                        activities = [activity.strip() for activity in media.activities.split(',') if activity.strip()]
                        for activity in activities:
                            activity_clean = activity.strip()
                            if (activity_clean and 
                                not activity_clean.lower().startswith('people') and 
                                'people' not in activity_clean.lower() and
                                'person' not in activity_clean.lower()):
                                all_activities.add(activity_clean)
        
        # Convert to sorted list
        activities_list = sorted(list(all_activities))
        
        return jsonify(activities_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/scenery', methods=['GET'])
def get_scenery():
    """Get all unique scenery items from all media records"""
    try:
        # Get all media records that have scenery
        media_records = Media.query.filter(
            Media.scenery.isnot(None),
            Media.scenery != '',
            Media.scenery != '[]'
        ).all()
        
        all_scenery = set()
        
        for media in media_records:
            if media.scenery:
                # Handle both JSON array format and comma-separated string format
                try:
                    # Try parsing as JSON first
                    if media.scenery.startswith('['):
                        scenery = json.loads(media.scenery)
                    else:
                        # Handle comma-separated string format
                        scenery = [scene.strip() for scene in media.scenery.split(',') if scene.strip()]
                    
                    for scene in scenery:
                        # Filter out people-related scenery and clean up the scene name
                        scene_clean = scene.strip()
                        if (scene_clean and 
                            not scene_clean.lower().startswith('people') and 
                            'people' not in scene_clean.lower() and
                            'person' not in scene_clean.lower()):
                            all_scenery.add(scene_clean)
                except (json.JSONDecodeError, AttributeError):
                    # Handle comma-separated string format as fallback
                    if isinstance(media.scenery, str):
                        scenery = [scene.strip() for scene in media.scenery.split(',') if scene.strip()]
                        for scene in scenery:
                            scene_clean = scene.strip()
                            if (scene_clean and 
                                not scene_clean.lower().startswith('people') and 
                                'people' not in scene_clean.lower() and
                                'person' not in scene_clean.lower()):
                                all_scenery.add(scene_clean)
        
        # Convert to sorted list
        scenery_list = sorted(list(all_scenery))
        
        return jsonify(scenery_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
