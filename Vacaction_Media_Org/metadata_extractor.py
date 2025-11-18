
from importlib.metadata import metadata
from math import radians, sin, cos, sqrt, atan2
import os
import subprocess
import json
import logging
import sqlite3
from datetime import datetime
import pickle
from pathlib import Path

# Setup logger for this module
logger = logging.getLogger('metadata_extractor')

# Optional imports for media analysis
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Visual analysis will be limited.")

try:
    import librosa  # type: ignore
    LIBROSA_AVAILABLE = True
    
    # Configure librosa to suppress audio backend warnings
    import warnings
    # Suppress specific librosa/audioread warnings
    warnings.filterwarnings('ignore', message='PySoundFile failed')
    warnings.filterwarnings('ignore', message='audioread')
    warnings.filterwarnings('ignore', category=UserWarning, module='librosa')
    
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("Librosa not available. Audio analysis will be disabled.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
    
    # Try to enable HEIC support
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        HEIF_AVAILABLE = True
        logger.debug("HEIC support enabled via pillow-heif")
    except ImportError:
        HEIF_AVAILABLE = False
        logger.debug("pillow-heif not available, HEIC support may be limited")
        
except ImportError:
    PIL_AVAILABLE = False
    HEIF_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Image processing will be limited.")

class MetadataExtractor:
    def __init__(self, db_path='media_organizer.db'):
        """
        Initialize MetadataExtractor with geo data from database.
        
        Args:
            db_path: Path to the SQLite database containing geo_data table
        """
        self.city_dict: dict[str, str] = {}
        self.geo_data = []
        self.db_path = db_path
        
        # Load geo data from database geo_data table
        self._load_geo_data_from_db()
        
        # ORIGINAL FILE-BASED GEO DATA LOADING (commented out for future reference)
        # The following code was used to load geo data from geo_chinese.list file
        # Search for "FILE_BASED_GEO_LOADING_DISABLED" to restore this functionality
        #
        # self.geo_list_path = geo_list_path
        # if not os.path.exists(self.geo_list_path):
        #     logging.warning(f"File {self.geo_list_path} not found. Geolocation enhancement will be disabled.")
        #     self.geo_list_path = None
        # else:
        #     # Read and parse geo.list comma separator CSV file and store in memory as a list of tuples
        #     # This is the first line of the CSV file:
        #     #   City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
        #     self.geo_data = []
        #     with open(self.geo_list_path, 'r', encoding='utf-8') as f:
        #         # Skip header line
        #         next(f)
        #         for line in f:
        #             # Each line is comma-separated values and values are
        #             #  0:City_en,1:City_zn,2:Region_en,3:Region_zn,4:Subregion_en,5:Subregion_zn,6:CountryCode,7:Country_en,8:Country_zn,9:TimeZone,10:Latitude,11:Longitude
        #             # logging.info(f"Parsing line in geo.list: {line.strip()}")
        #             parts = line.strip().split(',')
        #             try:
        #                 city_en = parts[0]
        #                 city_zn = parts[1]
        #                 region_en = parts[2]
        #                 region_zn = parts[3]
        #                 subregion_en = parts[4]
        #                 subregion_zn = parts[5]
        #                 country_code = parts[6]
        #                 country_en = parts[7]
        #                 country_zn = parts[8]
        #                 timezone = parts[9]
        #                 lat = float(parts[10])
        #                 lon = float(parts[11])
        #                 # Save city translation mapping with country for unique identification
        #                 # Key format: (city_en, country_en) -> city_zh
        #                 self.city_dict[(city_en, country_en)] = city_zn
        #                 self.geo_data.append((lat, lon, city_en, city_zn, region_en, region_zn, subregion_en, subregion_zn, country_code, country_en, country_zn, timezone))
        #             except ValueError:
        #                 logging.error(f"Error parsing line in geo.list: {line}")
        #                 continue
        #     logging.info(f"Loaded {len(self.geo_data)} entries from {self.geo_list_path}")
        #     logging.info(f"City translation dictionary contains {len(self.city_dict)} unique (city, country) pairs")
        #     
        #     # Debug: Show some statistics about potential duplicates
        #     city_counts = {}
        #     for (city, country) in self.city_dict.keys():
        #         if city in city_counts:
        #             city_counts[city] += 1
        #         else:
        #             city_counts[city] = 1
        #     
        #     duplicates = {city: count for city, count in city_counts.items() if count > 1}
        #     if duplicates:
        #         logging.info(f"Found {len(duplicates)} city names that appear in multiple countries:")
        #         for city, count in sorted(duplicates.items())[:10]:  # Show first 10
        #             countries = [country for (c, country) in self.city_dict.keys() if c == city]
        #             logging.info(f"  {city}: {count} countries ({', '.join(countries[:3])}{'...' if len(countries) > 3 else ''})")
        #     else:
        #         logging.info("No duplicate city names found across different countries")

    def _load_geo_data_from_db(self):
        """
        Load geo data from database geo_data table instead of from file.
        This method replaces the file-based geo data loading for better performance.
        """
        try:
            if not os.path.exists(self.db_path):
                logging.warning(f"Database {self.db_path} not found. Geolocation enhancement will be disabled.")
                return
            
            # Connect to database and load geo data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if geo_data table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='geo_data'
            """)
            
            if not cursor.fetchone():
                logging.warning("geo_data table not found in database. Geolocation enhancement will be disabled.")
                logging.info("Run 'python Main_scan_media.py --populateGeoTable -g' to populate geo data first.")
                conn.close()
                return
            
            # Load all geo data from database
            cursor.execute("""
                SELECT latitude, longitude, city_en, city_zh, region_en, region_zh, 
                       subregion_en, subregion_zh, country_code, country_en, country_zh, timezone
                FROM geo_data
                ORDER BY city_en, country_en
            """)
            
            rows = cursor.fetchall()
            
            # Process loaded data into the same format as file-based loading
            for row in rows:
                lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone = row
                
                # Save city translation mapping with country for unique identification
                # Key format: (city_en, country_en) -> city_zh
                self.city_dict[(city_en, country_en)] = city_zh
                
                # Store geo data in same format as original: (lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone)
                self.geo_data.append((lat, lon, city_en, city_zh, region_en, region_zh, subregion_en, subregion_zh, country_code, country_en, country_zh, timezone))
            
            conn.close()
            
            logging.info(f"Loaded {len(self.geo_data)} entries from database geo_data table")
            logging.info(f"City translation dictionary contains {len(self.city_dict)} unique (city, country) pairs")
            
            # Debug: Show some statistics about potential duplicates
            city_counts = {}
            for (city, country) in self.city_dict.keys():
                if city in city_counts:
                    city_counts[city] += 1
                else:
                    city_counts[city] = 1
            
            duplicates = {city: count for city, count in city_counts.items() if count > 1}
            if duplicates:
                logging.info(f"Found {len(duplicates)} city names that appear in multiple countries:")
                for city, count in sorted(duplicates.items())[:10]:  # Show first 10
                    countries = [country for (c, country) in self.city_dict.keys() if c == city]
                    logging.info(f"  {city}: {count} countries ({', '.join(countries[:3])}{'...' if len(countries) > 3 else ''})")
            else:
                logging.info("No duplicate city names found across different countries")
                
        except sqlite3.Error as e:
            logging.error(f"Database error while loading geo data: {e}")
            logging.warning("Geolocation enhancement will be disabled.")
        except Exception as e:
            logging.error(f"Unexpected error while loading geo data: {e}")
            logging.warning("Geolocation enhancement will be disabled.")

    def _get_city_translation(self, city_name: str, country_name: str = None) -> str:
        """
        Get Chinese translation for a city name, using country for disambiguation.
        
        Args:
            city_name: English city name
            country_name: English country name (optional, for disambiguation)
            
        Returns:
            Chinese city name if found, None otherwise
        """
        if not city_name:
            return None
            
        # Try exact match with country first (most accurate)
        if country_name:
            key = (city_name, country_name)
            if key in self.city_dict:
                rc_city_zh = self.city_dict[key]
                logger.debug(f"City translation found (exact): {city_name}, {country_name} -> {rc_city_zh}")
                return rc_city_zh
        
        # Fallback: try to find any match for the city name (less accurate)
        # This handles cases where country might be None or not matching exactly
        for (stored_city, stored_country), stored_translation in self.city_dict.items():
            if stored_city == city_name:
                logger.debug(f"City translation found (fallback): {city_name} -> {stored_translation} (from {stored_country})")
                return stored_translation
        
        logger.debug(f"No city translation found for: {city_name}" + (f" in {country_name}" if country_name else ""))
        return None

    def get_city_disambiguation_stats(self):
        """
        Returns statistics about cities that would benefit from country disambiguation.
        Useful for understanding the impact of the country-based lookup.
        """
        city_counts = {}
        for (city, country) in self.city_dict.keys():
            if city in city_counts:
                city_counts[city].append(country)
            else:
                city_counts[city] = [country]
        
        duplicates = {city: countries for city, countries in city_counts.items() if len(countries) > 1}
        
        stats = {
            'total_cities': len(city_counts),
            'unique_city_names': len(city_counts),
            'cities_with_multiple_countries': len(duplicates),
            'duplicate_examples': dict(list(duplicates.items())[:5])  # First 5 examples
        }
        
        return stats

    def _analysis_mediafile(self, filepath):
        """
        Analyze image or video file to extract semantic information.
        
        Args:
            filepath: Path to the media file to analyze
            
        Returns:
            dict: Analysis results containing:
                - people_count: Number of people detected (int)
                - activities: List of detected activities (list of strings)
                - scenery: Description of scenery/environment (string)
                - talking_detected: Whether talking/speech is detected (bool)
        """
        if not os.path.exists(filepath):
            logging.error(f"File not found: {filepath}")
            return {
                'people_count': 0,
                'activities': [],
                'scenery': '',
                'talking_detected': False
            }
        
        extension = os.path.splitext(filepath)[1].upper()
        
        # Initialize results
        analysis_result = {
            'people_count': 0,
            'activities': [],
            'scenery': '',
            'talking_detected': False
        }
        
        try:
            if extension in ['.JPG', '.JPEG', '.PNG', '.HEIC']:
                # Analyze image file
                analysis_result.update(self._analyze_image(filepath))
            elif extension in ['.MP4', '.MOV', '.AVI', '.MKV', '.WEBM']:
                # Analyze video file
                analysis_result.update(self._analyze_video(filepath))
            else:
                logging.warning(f"Unsupported file type for analysis: {extension}")
                
        except Exception as e:
            logging.error(f"Error analyzing media file {filepath}: {e}\n")
            logger.debug(f"Analysis result (partial) for {filepath}: {analysis_result}")

        return analysis_result
    
    def _analyze_image(self, filepath):
        """Analyze image file for people, activities, and scenery."""
        result = {
            'people_count': 0,
            'activities': [],
            'scenery': '',
            'talking_detected': False  # Images don't have audio
        }
        
        if not CV2_AVAILABLE:
            logging.debug("OpenCV not available, skipping image analysis")
            return result
            
        try:
            # Load image using OpenCV
            image = cv2.imread(filepath)
            if image is None:
                # Try loading with PIL for HEIC files and other formats OpenCV can't handle
                if PIL_AVAILABLE:
                    try:
                        logging.debug(f"OpenCV failed, trying PIL for: {filepath}")
                        pil_image = Image.open(filepath)
                        
                        # Convert PIL image to OpenCV format
                        # Handle different modes (RGBA, RGB, L, etc.)
                        if pil_image.mode == 'RGBA':
                            # Convert RGBA to RGB with white background
                            rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                            rgb_image.paste(pil_image, mask=pil_image.split()[-1])  # Use alpha channel as mask
                            pil_image = rgb_image
                        elif pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        # Convert PIL RGB to OpenCV BGR
                        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                        logging.debug(f"Successfully loaded with PIL: {filepath}")
                        
                    except Exception as pil_error:
                        logging.error(f"PIL also failed to load image {filepath}: {pil_error}")
                        return result
                else:
                    logging.warning(f"Could not load image (OpenCV failed, PIL not available): {filepath}")
                    return result
            
            # People detection using Haar Cascades (basic approach)
            result['people_count'] = self._detect_people_in_frame(image)
            
            # Scene analysis
            result['scenery'] = self._analyze_scene(image)
            
            # Activity detection (basic approach based on image content)
            result['activities'] = self._detect_activities_in_image(image)
            
        except Exception as e:
            logging.error(f"Error analyzing image {filepath}: {e}\n")
            logging.debug(f"Analysis result (partial) for {filepath}: {result}")

        return result
    
    def _analyze_video(self, filepath):
        """Analyze video file for people, activities, scenery, and audio."""
        result = {
            'people_count': 0,
            'activities': [],
            'scenery': '',
            'talking_detected': False
        }
        
        try:
            # Analyze video frames
            if CV2_AVAILABLE:
                video_result = self._analyze_video_frames(filepath)
                result.update(video_result)
            
            # PERFORMANCE ENHANCEMENT: Audio analysis disabled for performance reasons
            # Talking detection is not needed and consumes significant processing time
            # Search for "AUDIO_ANALYSIS_DISABLED" to re-enable audio processing
            # if LIBROSA_AVAILABLE:
            #     audio_result = self._analyze_audio(filepath)
            #     result['talking_detected'] = audio_result.get('talking_detected', False)
            
            # Set talking_detected to False since audio analysis is disabled
            result['talking_detected'] = False  # AUDIO_ANALYSIS_DISABLED
                
        except Exception as e:
            logging.error(f"Error analyzing video {filepath}: {e}\n")
            logging.debug(f"Analysis result (partial) for {filepath}: {result}")

        return result
    
    def _analyze_video_frames(self, filepath):
        """Analyze video frames for visual content."""
        result = {
            'people_count': 0,
            'activities': [],
            'scenery': ''
        }
        
        try:
            cap = cv2.VideoCapture(filepath)
            if not cap.isOpened():
                logging.warning(f"Could not open video: {filepath}")
                return result
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            # Sample frames for analysis (every 2 seconds or max 10 frames)
            sample_interval = max(1, int(fps * 2)) if fps > 0 else 30
            max_samples = min(10, frame_count // sample_interval)
            
            people_counts = []
            scenery_descriptions = []
            activities_detected = set()
            
            for i in range(0, frame_count, sample_interval):
                if len(people_counts) >= max_samples:
                    break
                    
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if ret:
                    # Analyze this frame
                    people_count = self._detect_people_in_frame(frame)
                    people_counts.append(people_count)
                    
                    scenery = self._analyze_scene(frame)
                    if scenery:
                        scenery_descriptions.append(scenery)
                    
                    activities = self._detect_activities_in_image(frame)
                    activities_detected.update(activities)
            
            cap.release()
            
            # Aggregate results
            result['people_count'] = max(people_counts) if people_counts else 0
            result['activities'] = list(activities_detected)
            result['scenery'] = self._aggregate_scenery_descriptions(scenery_descriptions)
            
        except Exception as e:
            logging.error(f"Error analyzing video frames {filepath}: {e}\n")
            logging.debug(f"Analysis result (partial) for {filepath}: {result}")

        return result
    
    def _detect_people_in_frame(self, frame):
        """Detect people in a single frame using Haar Cascades."""
        
        # PERFORMANCE ENHANCEMENT: People detection disabled for performance and accuracy reasons
        # Return 0 immediately to skip processing. Search for "PEOPLE_DETECTION_DISABLED" to re-enable.
        # TODO: Re-enable when more accurate people detection algorithm is available
        return 0  # PEOPLE_DETECTION_DISABLED
        
        # Original people detection code (commented out for performance):
        # try:
        #     # Convert to grayscale for face detection
        #     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #     
        #     # Use Haar Cascade for face detection (proxy for people)
        #     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        #     faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        #     
        #     # Also try upper body detection
        #     body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        #     bodies = body_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50))
        #     
        #     # Take the maximum of face or body detection
        #     people_count = max(len(faces), len(bodies))
        #     
        #     logging.debug(f"Detected {len(faces)} faces and {len(bodies)} bodies, count: {people_count}")
        #     return people_count
        #     
        # except Exception as e:
        #     logging.error(f"Error detecting people in frame: {e}\n")
        #     return 0
    
    def _analyze_scene(self, frame):
        """Analyze scene content to determine scenery type."""
        try:
            # Basic scene analysis based on color distribution and edges
            height, width = frame.shape[:2]
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Analyze color distribution
            hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
            
            # Edge detection for structure analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (height * width)
            
            # Basic scenery classification based on color and structure
            scenery_type = self._classify_scenery(hist_h, hist_s, hist_v, edge_density)
            
            return scenery_type
            
        except Exception as e:
            logging.error(f"Error analyzing scene: {e}\n")
            return ""
    
    def _classify_scenery(self, hist_h, hist_s, hist_v, edge_density):
        """Classify scenery based on color histograms and edge density."""
        try:
            # Normalize histograms
            hist_h = hist_h.flatten() / np.sum(hist_h)
            hist_s = hist_s.flatten() / np.sum(hist_s)
            hist_v = hist_v.flatten() / np.sum(hist_v)
            
            # Check for dominant colors
            green_range = np.sum(hist_h[35:85])  # Green hues
            blue_range = np.sum(hist_h[100:130])  # Blue hues
            
            # Check saturation and brightness
            high_saturation = np.sum(hist_s[128:])  # High saturation
            low_brightness = np.sum(hist_v[:64])   # Low brightness
            high_brightness = np.sum(hist_v[192:]) # High brightness
            
            # Classification logic
            if blue_range > 0.3 and high_saturation > 0.4:
                return "waterscape"
            elif green_range > 0.4 and high_saturation > 0.3:
                return "nature/outdoor"
            elif edge_density > 0.15:  # High edge density suggests buildings/urban
                return "urban/architectural"
            elif low_brightness > 0.5:
                return "indoor/low-light"
            elif high_brightness > 0.6 and high_saturation < 0.2:
                return "bright/overexposed"
            else:
                return "general"
                
        except Exception as e:
            logging.error(f"Error classifying scenery: {e}")
            return "unknown"
    
    def _detect_activities_in_image(self, frame):
        """Detect activities based on image content."""
        activities = []
        
        try:
            # Basic activity detection based on scene analysis
            scenery = self._analyze_scene(frame)
            
            if "waterscape" in scenery:
                activities.extend(["swimming", "boating", "beach"])
            elif "nature" in scenery:
                activities.extend(["hiking", "sightseeing", "outdoor"])
            elif "urban" in scenery:
                activities.extend(["sightseeing", "walking", "tourism"])
            elif "indoor" in scenery:
                activities.extend(["indoor", "dining", "visiting"])
                
            # Additional activity detection could be added here
            # (e.g., object detection for specific activities)
            
        except Exception as e:
            logging.error(f"Error detecting activities: {e}")
            
        return activities
    
    def _analyze_audio(self, filepath):
        """Analyze audio content for talking detection."""
        result = {'talking_detected': False}
        
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                logging.warning(f"Audio file not found: {filepath}")
                return result
            
            # Get file extension to determine approach
            extension = os.path.splitext(filepath)[1].upper()
            
            # For video files, we need to be more careful with audio loading
            if extension in ['.MP4', '.MOV', '.AVI', '.MKV', '.WEBM']:
                # Check if video has audio streams first
                if not self._has_audio_stream(filepath):
                    logging.debug(f"No audio streams detected in video: {filepath}")
                    return result
                
                # Always try ffmpeg first for video files to avoid librosa warnings
                audio_data = self._extract_audio_from_video(filepath)
                if audio_data is None:
                    logging.debug(f"Could not extract audio from video: {filepath}")
                    return result
                y, sr = audio_data
            else:
                # For audio files, use librosa directly with warning suppression
                try:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        y, sr = librosa.load(filepath, duration=30, sr=None)  # Preserve original sample rate
                except Exception as load_error:
                    logging.warning(f"Could not load audio file {filepath}: {load_error}")
                    return result
            
            if len(y) == 0:
                logging.debug(f"Empty audio data for: {filepath}")
                return result
            
            # Voice activity detection using spectral features
            talking_detected = self._detect_voice_activity(y, sr)
            result['talking_detected'] = talking_detected
            
        except Exception as e:
            logging.error(f"Error analyzing audio {filepath}: {e}")
            
        return result
    
    def _has_audio_stream(self, filepath):
        """Check if video file has audio streams."""
        try:
            import ffmpeg
            probe = ffmpeg.probe(filepath, v='quiet')
            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
            return len(audio_streams) > 0
        except Exception:
            # If we can't probe, assume it might have audio
            return True

    def _extract_audio_from_video(self, filepath):
        """Extract audio from video file using multiple fallback methods."""
        try:
            # Method 1: Use ffmpeg to extract audio first (most reliable for MP4)
            try:
                import ffmpeg
                import tempfile
                import warnings
                
                # Create temporary audio file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    temp_audio_path = temp_audio.name
                
                try:
                    # Check if video has audio streams first
                    probe = ffmpeg.probe(filepath)
                    audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
                    
                    if not audio_streams:
                        logging.debug(f"No audio streams found in video: {filepath}")
                        return None
                    
                    # Extract audio using ffmpeg (force PCM format for compatibility)
                    (
                        ffmpeg
                        .input(filepath)
                        .output(
                            temp_audio_path, 
                            acodec='pcm_s16le',  # Force PCM format
                            ac=1,                # Mono
                            ar=22050,           # Standard sample rate
                            t=30,               # First 30 seconds
                            loglevel='quiet'    # Suppress ffmpeg output
                        )
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True, quiet=True)
                    )
                    
                    # Load the extracted audio with suppressed warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        y, sr = librosa.load(temp_audio_path, sr=22050)
                    
                    # Clean up temporary file
                    os.unlink(temp_audio_path)
                    
                    if len(y) > 0:
                        logging.debug(f"Successfully extracted audio using ffmpeg: {filepath}")
                        return y, sr
                    else:
                        logging.debug(f"Empty audio extracted from: {filepath}")
                        return None
                        
                except Exception as ffmpeg_error:
                    # Clean up temporary file if it exists
                    if os.path.exists(temp_audio_path):
                        os.unlink(temp_audio_path)
                    logging.debug(f"ffmpeg extraction failed for {filepath}: {ffmpeg_error}")
                    
            except ImportError:
                logging.debug("ffmpeg-python not available for audio extraction")
            
            # Method 2: Try librosa with audioread backend (suppress warnings)
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Force audioread backend and suppress all warnings
                    old_environ = os.environ.get('LIBROSA_CACHE_DIR')
                    os.environ['LIBROSA_CACHE_DIR'] = '/tmp'  # Use tmp for cache
                    
                    y, sr = librosa.load(filepath, duration=30, sr=22050, res_type='kaiser_fast')
                    
                    # Restore environment
                    if old_environ:
                        os.environ['LIBROSA_CACHE_DIR'] = old_environ
                    elif 'LIBROSA_CACHE_DIR' in os.environ:
                        del os.environ['LIBROSA_CACHE_DIR']
                    
                if len(y) > 0:
                    logging.debug(f"Successfully extracted audio using librosa+audioread: {filepath}")
                    return y, sr
            except Exception as e:
                logging.debug(f"librosa+audioread failed for {filepath}: {e}")
            
            # Method 3: Try with different librosa parameters
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Try with offset to skip potential problematic header
                    y, sr = librosa.load(filepath, duration=25, offset=2.0, sr=22050, mono=True)
                    
                if len(y) > 0:
                    logging.debug(f"Successfully extracted audio using librosa offset method: {filepath}")
                    return y, sr
            except Exception as e:
                logging.debug(f"librosa offset method failed for {filepath}: {e}")
            
            # All methods failed
            logging.debug(f"All audio extraction methods failed for: {filepath}")
            return None
            
        except Exception as e:
            logging.error(f"Error in audio extraction from {filepath}: {e}")
            return None
    
    def _detect_voice_activity(self, audio, sample_rate):
        """Detect voice activity in audio signal."""
        
        # PERFORMANCE ENHANCEMENT: Talking detection disabled for performance and accuracy reasons
        # Return False immediately to skip processing. Search for "TALKING_DETECTION_DISABLED" to re-enable.
        # TODO: Re-enable when more accurate voice activity detection algorithm is available
        return False  # TALKING_DETECTION_DISABLED
        
        # Original voice activity detection code (commented out for performance):
        # try:
        #     # Compute spectral features
        #     spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
        #     spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)[0]
        #     zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)[0]
        #     
        #     # Compute MFCC features (useful for voice detection)
        #     mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
        #     
        #     # Voice activity detection heuristics
        #     # Voice typically has:
        #     # - Moderate spectral centroid (300-3000 Hz)
        #     # - Regular patterns in MFCCs
        #     # - Moderate zero crossing rate
        #     
        #     avg_centroid = np.mean(spectral_centroids)
        #     avg_zcr = np.mean(zero_crossing_rate)
        #     mfcc_variance = np.var(mfccs, axis=1)
        #     
        #     # Heuristic thresholds for voice detection
        #     voice_detected = (
        #         300 < avg_centroid < 3000 and  # Typical voice frequency range
        #         0.01 < avg_zcr < 0.3 and       # Moderate zero crossing rate
        #         np.mean(mfcc_variance) > 50    # Sufficient MFCC variance
        #     )
        #     
        #     logging.debug(f"Voice detection - Centroid: {avg_centroid:.2f}, ZCR: {avg_zcr:.4f}, Voice: {voice_detected}")
        #     
        #     return voice_detected
        #     
        # except Exception as e:
        #     logging.error(f"Error detecting voice activity: {e}")
        #     return False
    
    def _aggregate_scenery_descriptions(self, descriptions):
        """Aggregate multiple scenery descriptions into a single description."""
        if not descriptions:
            return ""
        
        # Count occurrences of each scenery type
        scenery_counts = {}
        for desc in descriptions:
            scenery_counts[desc] = scenery_counts.get(desc, 0) + 1
        
        # Return the most common scenery type
        if scenery_counts:
            return max(scenery_counts.items(), key=lambda x: x[1])[0]
        return ""

    def _run_exiftool(self, filepath):
        """Run ExifTool to extract EXIF metadata from a file."""
        try:
            cmd = ['exiftool', '-j', '-n',
                   '-CreateDate', '-FileInodeChangeDate', 
                   '-GPSLatitude', '-GPSLongitude', '-UserComment', str(filepath)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                metadata_list = json.loads(result.stdout)
                if metadata_list and len(metadata_list) > 0:
                    metadata = metadata_list[0]
                    logger.debug(f"EXIF extracted for {filepath}: {metadata}")
                else:
                    logger.debug(f"No EXIF metadata found for {filepath}")
                    return {}
            else:
                logger.error(f"No Stdout from ExifTool for {filepath}")
                return {}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ExifTool error for {filepath}: {e}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {filepath}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error extracting EXIF from {filepath}: {e}")
            return {}
       
        # Ensure metadata exists and is a dictionary before processing
        if not metadata or not isinstance(metadata, dict):
            logger.warning(f"Invalid metadata format for {filepath}: {type(metadata)}")
            return {}
       
        # metadata is already the first element from metadata_list, not a list itself
        exif_data = metadata
        Latitude  = exif_data.get("GPSLatitude", "N/A")  if "GPSLatitude" in exif_data else None
        Longitude = exif_data.get("GPSLongitude", "N/A") if "GPSLongitude" in exif_data else None
        create_date = exif_data.get('CreateDate', '')
        inode_change_date = exif_data.get('FileInodeChangeDate', '')
        user_comment = exif_data.get('UserComment', '')

        # -----------------------------------------------------------
        # PreImport_exif_file_processor.py should update EXIF: Add UserComment (UTC Zulu)
        # from create_date & inode_change_date with calculate_creation_time() logic.
        # However, the update EXIF also update indoe_change_date to current time,
        # Therefore, we cannot re-calculate creation_time with inode_change_date again here.
        # So here we only calculate creation_time when UserComment is empty.

        # calculate_creation_time() return UTC with offset ISO 8601 format.
        # convert_to_utc_zulu() transfer to UTC Zulu format
        if user_comment == '':
            iso8601 = self.calculate_creation_time(create_date, inode_change_date)
            creation_time = self.convert_to_utc_zulu( iso8601 )
        else:
            creation_time = user_comment  # Preserve existing UserComment if present
        # -----------------------------------------------------------

        rc_exif_data = {
            "Latitude": Latitude,
            "Longitude": Longitude,
            "Creation_time": creation_time,
            'UserComment': user_comment       # This should be from UserComment or calculated
        }

        return rc_exif_data

    def calculate_creation_time(self, create_date_str, inode_change_date_str):
        """Calculate creation time using sophisticated logic - all timezone-naive.
        Returns: creation_time_str (in UTC Zulu format)
        """
        create_date = self.parse_exif_date(create_date_str) if create_date_str else None
        inode_date = self.parse_exif_date(inode_change_date_str) if inode_change_date_str else None
               
        # Case 2.0: CreateDate is missing (N/A case)
        if not create_date_str or create_date_str.strip() == '':
            # If FileInodeChangeDate has timezone offset, use it
            if inode_change_date_str and ('+' in inode_change_date_str or (len(inode_change_date_str) > 6 and '-' in inode_change_date_str[-6:])):
                return inode_change_date_str
            elif inode_date:
                return inode_change_date_str
            return 'N/A'
        
        # Case 2.1: CreateDate is 0000:00:00 (zero case)
        if create_date_str.startswith('0000:00:00'):
            # If FileInodeChangeDate has timezone offset, use it
            if inode_change_date_str and ('+' in inode_change_date_str or (len(inode_change_date_str) > 6 and '-' in inode_change_date_str[-6:])):
                return inode_change_date_str
            elif inode_date:
                return inode_change_date_str
            return '0000:00:00'
        
        # If no inode date, use create date
        if not inode_date:
            return create_date_str
        
        try:
            # Ensure both dates are timezone-naive before comparison
            if create_date.tzinfo is not None:
                create_date = create_date.replace(tzinfo=None)
            if inode_date.tzinfo is not None:
                inode_date = inode_date.replace(tzinfo=None)
            
            # Get date components (YYYY:MM:DD)
            create_date_only = create_date.replace(hour=0, minute=0, second=0, microsecond=0)
            inode_date_only = inode_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calculate difference in days
            date_diff = (inode_date_only - create_date_only).days
            
        except Exception as e:
            return create_date_str # Fallback to original create date
        
        # Case 2.1: FileInodeChangeDate is few days younger than CreateDate
        if date_diff > 1:
            try:
                # Use CreateDate YYYY:MM:DD hh:mm:ss but add timezone offset from FileInodeChangeDate
                creation_time_str = create_date.strftime('%Y:%m:%d %H:%M:%S')
                
                # Extract and append timezone offset from FileInodeChangeDate if it exists
                tz_offset = self.extract_timezone_offset(inode_change_date_str)
                if tz_offset:
                    creation_time_str += tz_offset
                
                return creation_time_str
            except Exception as e:
                return create_date_str
        
        # Case 2.2: Same day or one day difference - use FileInodeChangeDate
        elif abs(date_diff) <= 1:
            return inode_change_date_str
        
        # Fallback to CreateDate
        else:
            return create_date_str

    # ------------------------------ #
    def parse_exif_date(self, date_string):
        """Parse EXIF date string to timezone-naive datetime object."""
        if not date_string or date_string.strip() == '':
            return None
        
        # Clean the date string first to remove timezone info
        clean_date = date_string.strip()
        
        # Remove timezone information to ensure all datetimes are timezone-naive
        import re
        
        # Handle positive timezone (e.g., "2024:03:15 14:23:45+08:00")
        if '+' in clean_date:
            clean_date = clean_date.split('+')[0].strip()
        
        # Handle negative timezone (e.g., "2024:03:15 14:23:45-05:00")
        timezone_pattern = r'-\d{2}:\d{2}$'
        if re.search(timezone_pattern, clean_date):
            clean_date = re.sub(timezone_pattern, '', clean_date).strip()
        
        # Remove 'Z' timezone indicator if present
        if clean_date.endswith('Z'):
            clean_date = clean_date[:-1].strip()
        
        # Handle various EXIF date formats (all timezone-naive now)
        formats = [
            '%Y:%m:%d %H:%M:%S',
            '%Y:%m:%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y:%m:%d',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(clean_date, fmt)
                # Ensure the result is timezone-naive
                if parsed_date.tzinfo is not None:
                    parsed_date = parsed_date.replace(tzinfo=None)
                return parsed_date
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def convert_to_utc_zulu(self, datetime_str):
        """Convert datetime string to UTC Zulu format (%Y-%m-%dT%H:%M:%SZ)."""
        if not datetime_str or datetime_str in ['N/A', '0000:00:00']:
            return 'N/A'
        
        # Extract timezone offset if present
        tz_offset = self.extract_timezone_offset(datetime_str)
        
        # Parse the datetime string (timezone-naive for calculations)
        parsed_date = self.parse_exif_date(datetime_str)
        if parsed_date:
            # If there was a timezone offset, adjust to UTC
            if tz_offset:
                try:
                    from datetime import timedelta
                    # Parse offset (e.g., "+08:00" or "-05:00")
                    sign = 1 if tz_offset.startswith('+') else -1
                    hours, minutes = map(int, tz_offset[1:].split(':'))
                    offset_minutes = sign * (hours * 60 + minutes)
                    
                    # Subtract offset to get UTC (if local time is +08:00, subtract 8 hours to get UTC)
                    utc_date = parsed_date - timedelta(minutes=offset_minutes)
                    return utc_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                except Exception as e:
                    logger.warning(f"Error converting timezone offset {tz_offset}: {e}")
            
            # No timezone offset, assume already UTC
            return parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return 'N/A'
    
    def extract_timezone_offset(self, datetime_str):
        """Extract timezone offset from datetime string."""
        if not datetime_str:
            return ''
        
        import re
        # Look for timezone patterns like +08:00 or -05:00
        positive_tz = re.search(r'\+\d{2}:\d{2}$', datetime_str)
        if positive_tz:
            return positive_tz.group()
        
        negative_tz = re.search(r'-\d{2}:\d{2}$', datetime_str)
        if negative_tz:
            return negative_tz.group()
        
        return ''
    
    # ------------------------------ #
    def extract_metadata(self, filepath):
        mediaType = 'Undefined'
        extension = os.path.splitext(filepath)[1].upper()
        if extension in [".JPG", ".JPEG", ".PNG", ".HEIC"]:
            mediaType = 'Image'
        elif extension in [".MP4", ".MOV"]:
            mediaType = 'Video'
        else:
            logging.warning(f"Unsupported file type for {filepath}. Skipping.")
            return None
        
        exif_data = self._run_exiftool(filepath)
        if not exif_data:
            return None

        creation_time = exif_data.get("Creation_time", None)
        user_comment = exif_data.get("UserComment", None)

        if not self.is_utc_zulu_format(user_comment):
            logger.info(f"*** Error: {filepath} UserComment '{user_comment}' is not UTC Zulu format, Creation_time '{creation_time}'.")

        stat_info = os.stat(filepath)
        base_metadata = {
            "filepath": os.path.abspath(filepath),
            "filename": os.path.basename(filepath),
            "file_extension": os.path.splitext(filepath)[1].lstrip(".").upper(),
            "size": stat_info.st_size,
            "media_type": mediaType,
            "latitude": exif_data.get("Latitude", None),
            "longitude": exif_data.get("Longitude", None),
            "creation_time": creation_time,
            "UserComment": user_comment
        }
        return base_metadata

    def is_utc_zulu_format(self, date_string):
        """Check if a string is in UTC Zulu format (YYYY-MM-DDTHH:MM:SSZ)."""
        if not date_string or date_string.strip() == '':
            return False
        
        date_string = date_string.strip()
        
        # UTC Zulu format should end with 'Z' and match the pattern YYYY-MM-DDTHH:MM:SSZ
        if not date_string.endswith('Z'):
            return False
        
        # Try to parse as UTC Zulu format
        try:
            # Remove the 'Z' and try to parse
            date_part = date_string[:-1]
            datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
            return True
        except ValueError:
            return False

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def get_geo_from_coordinates(self, latitude, longitude):
        if not self.geo_data:
            return None
        try:
            # Use ExifTool to reverse-geocode using the geo.list file
            # This requires a properly formatted geo.list file.
            # The command is hypothetical and depends on ExifTool's capabilities with custom geo files.
            # A more direct approach might be to parse geo.list in Python and do a nearest-neighbor search.
            # For this example, we simulate the expected output.
            # In a real scenario, one would parse geo.list and find the closest location.

            # This is a placeholder for what would be a call to a geo lookup function.
            # e.g., return self._find_location_in_geolist(latitude, longitude)
            logging.debug(f"Looking up geo data for lat={latitude}, lon={longitude}")
            closest = min(self.geo_data, key=lambda g: self.haversine(latitude, longitude, g[0], g[1]))
            logging.debug(f"Closest geo data found: {closest}")

            # 0:lat, 1:lon, 2:city_en, 3:city_zn, 4:region_en, 5:region_zn, 6:subregion_en, 7:subregion_zn, 8:country_code, 9:country_en, 10:country_zn, 11:timezone
            return {
                "latitude": latitude,   # closest[0],
                "longitude": longitude, # closest[1],
                "city_en": closest[2],
                "city_zh": closest[3],
                "region_en": closest[4],
                "region_zh": closest[5],
                "subregion_en": closest[6],
                "subregion_zh": closest[7],
                "country_code": closest[8],
                "country_en": closest[9],
                "country_zh": closest[10],
                "timezone": closest[11],
                "distance_km": round(self.haversine(latitude, longitude, closest[0], closest[1]), 2)
            }
        except Exception as e:
            logging.error(f"Error getting geo from coordinates: {e}")
            return None