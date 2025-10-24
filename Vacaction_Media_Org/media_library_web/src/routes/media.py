from flask import Blueprint, jsonify, request, send_file, Response
from src.models.media import Media, Config, db, convert_iso8601_to_local_display
import json
import os
import subprocess
import platform
import mimetypes
import sys
from datetime import datetime
import re

# Add the parent directory to the path to import metadata_extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from metadata_extractor import MetadataExtractor

media_bp = Blueprint('media', __name__)

# Initialize MetadataExtractor for geo data
# Use the same database path as configured in main.py
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'media_organizer.db')
metadata_extractor = None
if os.path.exists(db_path):
    try:
        metadata_extractor = MetadataExtractor(db_path)
        print(f"✅ MetadataExtractor initialized with database: {db_path}")
    except Exception as e:
        print(f"❌ Warning: Could not initialize MetadataExtractor: {e}")
        metadata_extractor = None
else:
    print(f"⚠️  Warning: Database not found at {db_path}")

def get_absolute_file_path(relative_path):
    """
    Convert relative path from database to absolute path using base_directory configuration.
    If relative_path is already absolute, return it as-is.
    """
    if os.path.isabs(relative_path):
        # If path is already absolute, return it
        return relative_path
    
    # Get base directory from config
    base_directory = Config.get_base_directory()
    if not base_directory:
        # Fallback: if no base directory configured, assume relative_path is correct
        print(f"⚠️  Warning: No base_directory configured, using relative path as-is: {relative_path}")
        return relative_path
    
    # Combine base directory with relative path
    absolute_path = os.path.join(base_directory, relative_path)
    return os.path.normpath(absolute_path)

def convert_date_filter_to_iso8601(date_str):
    """
    Convert date filter input to ISO 8601 format for database comparison.
    
    Args:
        date_str: Date string in various formats (YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, etc.)
        
    Returns:
        String that can be compared with ISO 8601 datetime strings in database
    """
    if not date_str:
        return None
        
    try:
        # If already in ISO 8601 format, return as-is
        if 'T' in date_str:
            return date_str
            
        # Handle YYYY-MM-DD format
        if len(date_str) == 10 and date_str.count('-') == 2:
            # For date range filtering, add time component
            # Start of day: YYYY-MM-DD -> YYYY-MM-DDT00:00:00
            return f"{date_str}T00:00:00"
            
        # Handle YYYY-MM-DD HH:MM:SS format
        if len(date_str) == 19 and date_str.count('-') == 2 and date_str.count(':') == 2:
            # Convert to ISO 8601: YYYY-MM-DD HH:MM:SS -> YYYY-MM-DDTHH:MM:SS
            return date_str.replace(' ', 'T')
            
        # Return as-is for other formats
        return date_str
        
    except Exception:
        return date_str

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
            # If the city parameter encodes both city and country using 'city||country'
            if '||' in city:
                try:
                    city_en, country_en = city.split('||', 1)
                    city_en = city_en.strip()
                    country_en = country_en.strip()
                    if city_en and country_en:
                        query = query.filter(
                            Media.city_en.ilike(f'%{city_en}%'),
                            Media.country_en.ilike(f'%{country_en}%')
                        )
                    else:
                        # Fallback to original behavior if parsing failed
                        query = query.filter(db.or_(
                            Media.city_en.ilike(f'%{city}%'),
                            Media.city_zh.ilike(f'%{city}%')
                        ))
                except Exception:
                    query = query.filter(db.or_(
                        Media.city_en.ilike(f'%{city}%'),
                        Media.city_zh.ilike(f'%{city}%')
                    ))
            else:
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
            # Convert date filters to ISO 8601 format for proper comparison
            iso_date_from = convert_date_filter_to_iso8601(date_from)
            iso_date_to = convert_date_filter_to_iso8601(date_to)
            
            # For end date, if it's just YYYY-MM-DD, make it end of day
            if iso_date_to and len(date_to) == 10:
                iso_date_to = f"{date_to}T23:59:59"
            
            # Filter by creation_time range (comparing ISO format strings)
            query = query.filter(
                Media.creation_time.between(iso_date_from, iso_date_to)
            )
        elif date_from:
            iso_date_from = convert_date_filter_to_iso8601(date_from)
            query = query.filter(Media.creation_time >= iso_date_from)
        elif date_to:
            iso_date_to = convert_date_filter_to_iso8601(date_to)
            # For end date, if it's just YYYY-MM-DD, make it end of day
            if len(date_to) == 10:
                iso_date_to = f"{date_to}T23:59:59"
            query = query.filter(Media.creation_time <= iso_date_to)
            
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
        file_path = get_absolute_file_path(media.filepath)
        
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
        file_path = get_absolute_file_path(media.filepath)
        
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
        file_path = get_absolute_file_path(media.filepath)
        
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
        
        # Convert ISO 8601 dates to display format
        earliest_display = convert_iso8601_to_local_display(date_range.earliest) if date_range.earliest else None
        latest_display = convert_iso8601_to_local_display(date_range.latest) if date_range.latest else None
        
        return jsonify({
            'total_media': total_media,
            'total_with_location': total_with_location,
            'total_with_talking': total_with_talking,
            'date_range': {
                'earliest': earliest_display,
                'latest': latest_display
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/date-range', methods=['GET'])
def get_date_range():
    """Get the earliest and latest creation_time dates from media records"""
    try:
        date_range = db.session.query(
            db.func.min(Media.creation_time).label('earliest'),
            db.func.max(Media.creation_time).label('latest')
        ).filter(
            Media.creation_time.isnot(None),
            Media.creation_time != '',
            Media.creation_time != 'null',
            Media.creation_time != '0000-00-00 00:00:00',
            ~Media.creation_time.like('0000-%')  # Exclude any dates starting with 0000
        ).first()
        
        # If no valid creation_time found, fall back to scanned_at
        if not date_range.earliest or not date_range.latest:
            date_range = db.session.query(
                db.func.min(Media.scanned_at).label('earliest'),
                db.func.max(Media.scanned_at).label('latest')
            ).filter(
                Media.scanned_at.isnot(None)
            ).first()
        
        # Convert ISO 8601 dates to display format for GUI
        earliest_display = convert_iso8601_to_local_display(date_range.earliest) if date_range.earliest else None
        latest_display = convert_iso8601_to_local_display(date_range.latest) if date_range.latest else None
        
        # Extract just the date part (YYYY-MM-DD) for date range picker
        if earliest_display:
            earliest_date = earliest_display.split(' ')[0]  # Get YYYY-MM-DD part
        else:
            earliest_date = None
            
        if latest_display:
            latest_date = latest_display.split(' ')[0]  # Get YYYY-MM-DD part
        else:
            latest_date = None
        
        return jsonify({
            'earliest': earliest_date,
            'latest': latest_date,
            'earliest_full': earliest_display,  # Full datetime for reference
            'latest_full': latest_display       # Full datetime for reference
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/filename-patterns', methods=['GET'])
def get_filename_patterns():
    """Get unique filename patterns (filename without extension, with DJI files removing last 3 chars, others last 2 chars)"""
    try:
        # Get all filenames from database
        filenames = db.session.query(Media.filename).filter(
            Media.filename.isnot(None),
            Media.filename != ''
        ).all()
        
        # Process filenames: remove extension, then remove suffix based on file type
        patterns = set()
        for filename_row in filenames:
            filename = filename_row.filename
            
            # Remove file extension
            if '.' in filename:
                base_filename = filename.rsplit('.', 1)[0]  # Remove last extension
            else:
                base_filename = filename
            
            # Determine pattern based on filename prefix
            if base_filename.upper().startswith('DJI_'):
                import re
                # For DJI files: keep DJI_ plus first 8 digits only
                dji_match = re.match(r'^DJI_(\d+)', base_filename, re.IGNORECASE)
                if dji_match:
                    # Extract all digits after DJI_ and take first 8
                    digits = dji_match.group(1)
                    # Take only the first 8 digits
                    if len(digits) > 8:
                        pattern = f"DJI_{digits[:8]}"
                    else:
                        pattern = f"DJI_{digits}"
                    patterns.add(pattern)
                else:
                    # Fallback for DJI files without digits - remove last 3 characters
                    if len(base_filename) > 3:
                        pattern = base_filename[:-3]
                        patterns.add(pattern)
            else:
                # For other files, remove last 2 characters from base filename
                if len(base_filename) > 2:
                    pattern = base_filename[:-2]
                    patterns.add(pattern)
        
        # Sort patterns alphabetically
        sorted_patterns = sorted(list(patterns))
        
        return jsonify(sorted_patterns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/by-filename-pattern', methods=['GET'])
def get_media_by_filename_pattern():
    """Get media files matching a filename pattern (handling DJI vs regular files)"""
    try:
        pattern = request.args.get('pattern')
        if not pattern:
            return jsonify({'error': 'pattern parameter is required'}), 400
        
        # Find all media files where the processed filename matches the pattern
        all_media = Media.query.filter(
            Media.filename.isnot(None),
            Media.filename != ''
        ).all()
        
        matching_media = []
        for media in all_media:
            filename = media.filename
            
            # Remove file extension
            if '.' in filename:
                base_filename = filename.rsplit('.', 1)[0]
            else:
                base_filename = filename
            
            # Generate pattern based on filename type
            file_pattern = None
            if base_filename.upper().startswith('DJI_'):
                import re
                # For DJI files: keep DJI_ plus first 8 digits only
                dji_match = re.match(r'^DJI_(\d+)', base_filename, re.IGNORECASE)
                if dji_match:
                    # Extract all digits after DJI_ and take first 8
                    digits = dji_match.group(1)
                    # Take only the first 8 digits
                    if len(digits) > 8:
                        file_pattern = f"DJI_{digits[:8]}"
                    else:
                        file_pattern = f"DJI_{digits}"
                else:
                    # Fallback for DJI files without digits - remove last 3 characters
                    if len(base_filename) > 3:
                        file_pattern = base_filename[:-3]
            else:
                # For other files, remove last 2 characters
                if len(base_filename) > 2:
                    file_pattern = base_filename[:-2]
            
            # Check if this file matches the requested pattern
            if file_pattern == pattern:
                matching_media.append(media)
        
        # Sort by creation time
        matching_media.sort(key=lambda x: x.creation_time or '')
        
        # Convert to dict format
        result = []
        for media in matching_media:
            media_dict = media.to_dict()
            result.append(media_dict)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/cities', methods=['GET'])
def get_cities():
    """Get all unique cities with standardized coordinates from database geo data"""
    try:
        if not metadata_extractor or not metadata_extractor.geo_data:
            # Fallback to database data if geo data is not available
            return get_cities_from_database()
        
        # Get unique city+country combinations from database
        city_countries = db.session.query(
            Media.city_en, 
            Media.country_en
        ).filter(
            Media.city_en.isnot(None), 
            Media.city_en != '',
            Media.country_en.isnot(None),
            Media.country_en != ''
        ).distinct().all()
        
        city_list = []
        processed_combinations = set()
        
        # For each city+country combination from database, get standardized geo data
        for city_en, country_en in city_countries:
            combination_key = (city_en, country_en)
            
            # Skip if we've already processed this combination
            if combination_key in processed_combinations:
                continue
            processed_combinations.add(combination_key)
            
            # Find matching geo data
            matching_geo = None
            for geo_entry in metadata_extractor.geo_data:
                # geo_entry format: (lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone)
                geo_city_en = geo_entry[2]
                geo_country_en = geo_entry[9]
                
                if geo_city_en == city_en and geo_country_en == country_en:
                    matching_geo = geo_entry
                    break
            
            if matching_geo:
                # Use standardized coordinates and names from geo database
                lat, lon, geo_city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, geo_country_en, country_zh, timezone = matching_geo
                
                city_display = f"{geo_city_en} | {city_zh}" if city_zh else geo_city_en
                country_display = f"{geo_country_en} | {country_zh}" if country_zh else geo_country_en
                full_display = f"{city_display} | {country_display}"
                
                city_list.append({
                    'value': f"{lat},{lon}",  # Keep coordinates as compatibility value
                    'search_value': f"{geo_city_en}||{geo_country_en}",  # For searching by city and country
                    'display': full_display,
                    'city_en': geo_city_en,
                    'city_zh': city_zh,
                    'country_en': geo_country_en,
                    'country_zh': country_zh,
                    'latitude': lat,
                    'longitude': lon
                })
            else:
                # City+country not found in geo database, get Chinese name from media database if available
                db_city_zh = db.session.query(Media.city_zh).filter(
                    Media.city_en == city_en,
                    Media.country_en == country_en,
                    Media.city_zh.isnot(None),
                    Media.city_zh != ''
                ).first()
                
                db_country_zh = db.session.query(Media.country_zh).filter(
                    Media.city_en == city_en,
                    Media.country_en == country_en,
                    Media.country_zh.isnot(None),
                    Media.country_zh != ''
                ).first()
                
                # Get first available coordinates for this city+country from database
                db_coords = db.session.query(Media.latitude, Media.longitude).filter(
                    Media.city_en == city_en,
                    Media.country_en == country_en,
                    Media.latitude.isnot(None),
                    Media.longitude.isnot(None)
                ).first()
                
                if db_coords:
                    city_zh = db_city_zh.city_zh if db_city_zh else None
                    country_zh = db_country_zh.country_zh if db_country_zh else None
                    
                    city_display = f"{city_en} | {city_zh}" if city_zh else city_en
                    country_display = f"{country_en} | {country_zh}" if country_zh else country_en
                    full_display = f"{city_display} | {country_display}"
                    
                    city_list.append({
                        'value': f"{db_coords.latitude},{db_coords.longitude}",
                        'search_value': f"{city_en}||{country_en}",
                        'display': full_display,
                        'city_en': city_en,
                        'city_zh': city_zh,
                        'country_en': country_en,
                        'country_zh': country_zh,
                        'latitude': db_coords.latitude,
                        'longitude': db_coords.longitude
                    })
        
        # Sort by city name
        city_list.sort(key=lambda x: x['city_en'])
        
        return jsonify(city_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_cities_from_database():
    """Fallback method to get cities directly from database (original implementation)"""
    try:
        cities = db.session.query(
            Media.city_en, 
            Media.city_zh, 
            Media.country_en, 
            Media.country_zh,
            Media.latitude,
            Media.longitude
        ).filter(
            Media.city_en.isnot(None), 
            Media.city_en != '',
            Media.latitude.isnot(None),
            Media.longitude.isnot(None)
        ).distinct().order_by(Media.city_en.asc()).all()
        
        city_list = []
        for city_en, city_zh, country_en, country_zh, lat, lng in cities:
            city_display = f"{city_en} | {city_zh}" if city_zh else city_en
            country_display = f"{country_en} | {country_zh}" if country_zh else country_en
            full_display = f"{city_display} | {country_display}"
            
            city_list.append({
                'value': f"{lat},{lng}",  # Store coordinates as value (compatibility)
                'search_value': f"{city_en}||{country_en}",
                'display': full_display,
                'city_en': city_en,
                'city_zh': city_zh,
                'country_en': country_en,
                'country_zh': country_zh,
                'latitude': lat,
                'longitude': lng
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

@media_bp.route('/media/geo-countries', methods=['GET'])
def get_geo_countries():
    """Get all countries from database geo_data table (for FixInfo view)"""
    try:
        # Use the metadata_extractor to get countries from geo file
        if not metadata_extractor or not metadata_extractor.geo_data:
            return jsonify({'error': 'Geo data not available'}), 500
        
        country_set = set()
        
        # Extract unique countries from geo_data
        # geo_data format: (lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone)
        for geo_entry in metadata_extractor.geo_data:
            (lat, lon, city_en, city_zh, region_en, region_zh, 
             subregion_en, subregion_zh, country_code, country_en, country_zh, timezone) = geo_entry
            
            if country_en and country_en.strip():
                country_set.add((country_en, country_zh if country_zh else country_en))
        
        # Convert to list and sort
        country_list = []
        for country_en, country_zh in sorted(country_set):
            display_name = f"{country_en} | {country_zh}" if country_zh and country_zh != country_en else country_en
            country_list.append({
                'value': country_en,
                'display': display_name
            })
        
        return jsonify(country_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/cities-by-country', methods=['GET'])
def get_cities_by_country():
    """Get cities filtered by country"""
    try:
        country = request.args.get('country')
        if not country:
            return jsonify({'error': 'Country parameter is required'}), 400
        
        # Group by city to get unique cities with representative coordinates
        cities = db.session.query(
            Media.city_en,
            Media.city_zh,
            db.func.min(Media.latitude).label('latitude'),
            db.func.min(Media.longitude).label('longitude')
        ).filter(
            Media.city_en.isnot(None),
            Media.city_en != '',
            Media.country_en == country
        ).group_by(Media.city_en, Media.city_zh).order_by(Media.city_en.asc()).all()
        
        city_list = []
        for city_en, city_zh, latitude, longitude in cities:
            # For Map View, city display doesn't need country info since country is already selected
            display_name = f"{city_en} | {city_zh}" if city_zh else city_en
            # Search value combines city and country for backend filtering
            search_value = f"{city_en}||{country}"
            
            # Get country_zh for the selected country
            country_zh = db.session.query(Media.country_zh).filter(
                Media.country_en == country,
                Media.country_zh.isnot(None),
                Media.country_zh != ''
            ).first()
            country_zh = country_zh[0] if country_zh else None
            
            city_data = {
                'value': search_value,
                'display': display_name,
                'city_en': city_en,
                'city_zh': city_zh,
                'country_en': country,
                'country_zh': country_zh
            }
            # Include coordinates if available (for "View on Map" functionality)
            if latitude is not None and longitude is not None:
                city_data['latitude'] = latitude
                city_data['longitude'] = longitude
            city_list.append(city_data)
        
        return jsonify(city_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/geo-cities-by-country', methods=['GET'])
def get_geo_cities_by_country():
    """Get all cities from database geo_data table filtered by country (for FixInfo view)"""
    try:
        country = request.args.get('country')
        if not country:
            return jsonify({'error': 'Country parameter is required'}), 400
        
        # Use the metadata_extractor to get cities from geo file
        if not metadata_extractor or not metadata_extractor.geo_data:
            return jsonify({'error': 'Geo data not available'}), 500
        
        city_list = []
        seen_cities = set()
        
        # Iterate through geo_data and filter by country
        # geo_data format: (lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone)
        for geo_entry in metadata_extractor.geo_data:
            (lat, lon, city_en, city_zh, region_en, region_zh, 
             subregion_en, subregion_zh, country_code, country_en_geo, country_zh, timezone) = geo_entry
            
            # Filter by country (match either country_en or country_zh)
            if country_en_geo == country or country_zh == country:
                # Create unique identifier to avoid duplicates
                city_key = (city_en, city_zh)
                if city_key not in seen_cities:
                    seen_cities.add(city_key)
                    
                    # Format display name similar to existing format
                    display_name = f"{city_en} | {city_zh}" if city_zh else city_en
                    
                    city_data = {
                        'value': f"{city_en}||{country_en_geo}",  # Search value for consistency
                        'display': display_name,
                        'city_en': city_en,
                        'city_zh': city_zh,
                        'country_en': country_en_geo,
                        'country_zh': country_zh,
                        'latitude': lat,
                        'longitude': lon,
                        'region_en': region_en,
                        'region_zh': region_zh,
                        'subregion_en': subregion_en,
                        'subregion_zh': subregion_zh,
                        'country_code': country_code,
                        'timezone': timezone
                    }
                    city_list.append(city_data)
        
        # Sort by city_en for consistent ordering
        city_list.sort(key=lambda x: x['city_en'])
        
        return jsonify(city_list)
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

@media_bp.route('/media/without-time', methods=['GET'])
def get_media_without_time():
    """Get all media records that don't have creation_time set"""
    try:
        # Query for media files where creation_time is NULL or empty string
        media_records = Media.query.filter(
            db.or_(
                Media.creation_time.is_(None),
                Media.creation_time == '',
                Media.creation_time == 'NULL'
            )
        ).order_by(Media.filename.asc()).all()
        
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

@media_bp.route('/media/<int:media_id>/time', methods=['PUT'])
def update_media_creation_time(media_id):
    """Update the creation_time for a specific media record"""
    try:
        # Get the media record
        media = Media.query.get_or_404(media_id)
        
        # Get the new creation_time from request body
        data = request.get_json()
        if not data or 'creation_time' not in data:
            return jsonify({'error': 'creation_time is required'}), 400
        
        new_creation_time = data['creation_time']
        
        # Validate the format (should be YYYY-MM-DD HH:MM:SS or YYYY-MM-DD hh:mm:ss±##.##)
        try:
            from datetime import datetime
            # Try to parse timezone info (both + and - timezones)
            if ('+' in new_creation_time or new_creation_time.count('-') >= 3):
                # New format with timezone: YYYY-MM-DD hh:mm:ss±##.##
                # Split on the last '+' or '-' to separate time from timezone for validation
                if '+' in new_creation_time:
                    time_part = new_creation_time.rsplit('+', 1)[0]
                else:
                    time_part = new_creation_time.rsplit('-', 1)[0]
                datetime.strptime(time_part, '%Y-%m-%d %H:%M:%S')
            else:
                # Old format: YYYY-MM-DD HH:MM:SS
                datetime.strptime(new_creation_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid datetime format. Expected YYYY-MM-DD HH:MM:SS or YYYY-MM-DD hh:mm:ss±##.##'}), 400
        
        # Update the creation_time
        media.creation_time = new_creation_time
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Creation time updated successfully for {media.filename}',
            'creation_time': new_creation_time
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/bulk-update', methods=['PUT'])
def bulk_update_media():
    """Bulk update media files with city, date, and GPS information"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        media_ids = data.get('media_ids', [])
        city_en = data.get('city_en')
        city_zh = data.get('city_zh')
        country_en = data.get('country_en')
        country_zh = data.get('country_zh')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        creation_time = data.get('creation_time')
        force_update_time = data.get('force_update_time', False)
        
        if not media_ids:
            return jsonify({'error': 'media_ids is required'}), 400
        
        # Validate creation_time format if provided
        if creation_time:
            try:
                from datetime import datetime
                # Try to parse timezone info (both + and - timezones)
                if ('+' in creation_time or creation_time.count('-') >= 3):
                    # New format with timezone: YYYY-MM-DD hh:mm:ss±##.##
                    # Split on the last '+' or '-' to separate time from timezone for validation
                    if '+' in creation_time:
                        time_part = creation_time.rsplit('+', 1)[0]
                    else:
                        time_part = creation_time.rsplit('-', 1)[0]
                    datetime.strptime(time_part, '%Y-%m-%d %H:%M:%S')
                else:
                    # Old format: YYYY-MM-DD HH:MM:SS
                    datetime.strptime(creation_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return jsonify({'error': 'Invalid datetime format. Expected YYYY-MM-DD HH:MM:SS or YYYY-MM-DD hh:mm:ss±##.##'}), 400
        
        updated_files = []
        failed_files = []
        
        for media_id in media_ids:
            try:
                media = Media.query.get(media_id)
                if not media:
                    failed_files.append({'id': media_id, 'error': 'Media not found'})
                    continue
                
                # Update database fields
                if city_en is not None:
                    media.city_en = city_en
                if city_zh is not None:
                    media.city_zh = city_zh
                if country_en is not None:
                    media.country_en = country_en
                if country_zh is not None:
                    media.country_zh = country_zh
                if latitude is not None:
                    media.latitude = latitude
                if longitude is not None:
                    media.longitude = longitude
                
                # Conditional creation_time update logic
                if creation_time is not None:
                    if force_update_time:
                        # Force update: overwrite all selected files' creation_time
                        media.creation_time = creation_time
                    else:
                        # Conditional update: only update if file doesn't have creation_time
                        if not media.creation_time or media.creation_time.strip() == '':
                            media.creation_time = creation_time
                
                # Update file metadata using exiftool if any GPS or date info provided
                if latitude is not None and longitude is not None and creation_time is not None:
                    try:
                        # Build exiftool command
                        cmd = ['exiftool']
                        cmd.extend(['-DateTimeOriginal=' + creation_time.replace(' ', ' ')])
                        cmd.extend([f'-GPSLatitude={latitude}'])
                        cmd.extend([f'-GPSLongitude={longitude}'])
                        cmd.extend(['-overwrite_original'])
                        cmd.append(get_absolute_file_path(media.filepath))
                        
                        # Execute exiftool command
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode != 0:
                            print(f"Exiftool warning/error for {media.filename}: {result.stderr}")
                        
                    except Exception as exif_error:
                        print(f"Failed to update EXIF data for {media.filename}: {exif_error}")
                        # Continue with database update even if EXIF update fails
                
                updated_files.append({
                    'id': media.id,
                    'filename': media.filename,
                    'updated_fields': {
                        'city_en': city_en,
                        'city_zh': city_zh,
                        'country_en': country_en,
                        'country_zh': country_zh,
                        'latitude': latitude,
                        'longitude': longitude,
                        'creation_time': creation_time
                    }
                })
                
            except Exception as e:
                failed_files.append({'id': media_id, 'error': str(e)})
        
        # Commit all database changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': len(updated_files),
            'failed_count': len(failed_files),
            'updated_files': updated_files,
            'failed_files': failed_files
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@media_bp.route('/config/timezone', methods=['GET'])
def get_timezone_config():
    """Get timezone configuration for web display"""
    try:
        offset_time = Config.get_value('offsetTime', '+08:00')
        display_time = Config.get_value('displayTime', 'ASIA Time')
        
        return jsonify({
            'offsetTime': offset_time,
            'displayTime': display_time
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
