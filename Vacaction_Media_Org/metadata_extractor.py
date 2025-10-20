
from importlib.metadata import metadata
from math import radians, sin, cos, sqrt, atan2
import os
import subprocess
import json
import logging
from datetime import datetime
import pickle
from pathlib import Path

# Optional imports for media analysis
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Visual analysis will be limited.")

try:
    import librosa
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
        logging.debug("HEIC support enabled via pillow-heif")
    except ImportError:
        HEIF_AVAILABLE = False
        logging.debug("pillow-heif not available, HEIC support may be limited")
        
except ImportError:
    PIL_AVAILABLE = False
    HEIF_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Image processing will be limited.")

class MetadataExtractor:
    def __init__(self, geo_list_path='geo_chinese_.list'):

        self.city_dict: dict[str, str] = {}

        self.geo_list_path = geo_list_path
        if not os.path.exists(self.geo_list_path):
            logging.warning(f"File {self.geo_list_path} not found. Geolocation enhancement will be disabled.")
            self.geo_list_path = None
        else:
            # Read and parse geo.list comma separator CSV file and store in memory as a list of tuples
            # This is the first line of the CSV file:
            #   City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
            self.geo_data = []
            with open(self.geo_list_path, 'r', encoding='utf-8') as f:
                # Skip header line
                next(f)
                for line in f:
                    # Each line is comma-separated values and values are
                    #  0:City_en,1:City_zn,2:Region_en,3:Region_zn,4:Subregion_en,5:Subregion_zn,6:CountryCode,7:Country_en,8:Country_zn,9:TimeZone,10:Latitude,11:Longitude
                    # logging.info(f"Parsing line in geo.list: {line.strip()}")
                    parts = line.strip().split(',')
                    try:
                        city_en = parts[0]
                        city_zn = parts[1]
                        region_en = parts[2]
                        region_zn = parts[3]
                        subregion_en = parts[4]
                        subregion_zn = parts[5]
                        country_code = parts[6]
                        country_en = parts[7]
                        country_zn = parts[8]
                        timezone = parts[9]
                        lat = float(parts[10])
                        lon = float(parts[11])
                        # Save city translation mapping with country for unique identification
                        # Key format: (city_en, country_en) -> city_zh
                        self.city_dict[(city_en, country_en)] = city_zn
                        self.geo_data.append((lat, lon, city_en, city_zn, region_en, region_zn, subregion_en, subregion_zn, country_code, country_en, country_zn, timezone))
                    except ValueError:
                        logging.error(f"Error parsing line in geo.list: {line}")
                        continue
            logging.info(f"Loaded {len(self.geo_data)} entries from {self.geo_list_path}")
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
                logging.debug(f"City translation found (exact): {city_name}, {country_name} -> {rc_city_zh}")
                return rc_city_zh
        
        # Fallback: try to find any match for the city name (less accurate)
        # This handles cases where country might be None or not matching exactly
        for (stored_city, stored_country), stored_translation in self.city_dict.items():
            if stored_city == city_name:
                logging.debug(f"City translation found (fallback): {city_name} -> {stored_translation} (from {stored_country})")
                return stored_translation
        
        logging.debug(f"No city translation found for: {city_name}" + (f" in {country_name}" if country_name else ""))
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
        
        extension = os.path.splitext(filepath)[1].lower()
        
        # Initialize results
        analysis_result = {
            'people_count': 0,
            'activities': [],
            'scenery': '',
            'talking_detected': False
        }
        
        try:
            if extension in ['.jpg', '.jpeg', '.png', '.heic']:
                # Analyze image file
                analysis_result.update(self._analyze_image(filepath))
            elif extension in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                # Analyze video file
                analysis_result.update(self._analyze_video(filepath))
            else:
                logging.warning(f"Unsupported file type for analysis: {extension}")
                
        except Exception as e:
            logging.error(f"Error analyzing media file {filepath}: {e}\n")
            logging.debug(f"Analysis result (partial) for {filepath}: {analysis_result}")

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
            
            # Analyze audio for talking detection
            if LIBROSA_AVAILABLE:
                audio_result = self._analyze_audio(filepath)
                result['talking_detected'] = audio_result.get('talking_detected', False)
                
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
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use Haar Cascade for face detection (proxy for people)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # Also try upper body detection
            body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
            bodies = body_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50))
            
            # Take the maximum of face or body detection
            people_count = max(len(faces), len(bodies))
            
            logging.debug(f"Detected {len(faces)} faces and {len(bodies)} bodies, count: {people_count}")
            return people_count
            
        except Exception as e:
            logging.error(f"Error detecting people in frame: {e}\n")
            return 0
    
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
            extension = os.path.splitext(filepath)[1].lower()
            
            # For video files, we need to be more careful with audio loading
            if extension in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
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
        try:
            # Compute spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)[0]
            
            # Compute MFCC features (useful for voice detection)
            mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
            
            # Voice activity detection heuristics
            # Voice typically has:
            # - Moderate spectral centroid (300-3000 Hz)
            # - Regular patterns in MFCCs
            # - Moderate zero crossing rate
            
            avg_centroid = np.mean(spectral_centroids)
            avg_zcr = np.mean(zero_crossing_rate)
            mfcc_variance = np.var(mfccs, axis=1)
            
            # Heuristic thresholds for voice detection
            voice_detected = (
                300 < avg_centroid < 3000 and  # Typical voice frequency range
                0.01 < avg_zcr < 0.3 and       # Moderate zero crossing rate
                np.mean(mfcc_variance) > 50    # Sufficient MFCC variance
            )
            
            logging.debug(f"Voice detection - Centroid: {avg_centroid:.2f}, ZCR: {avg_zcr:.4f}, Voice: {voice_detected}")
            
            return voice_detected
            
        except Exception as e:
            logging.error(f"Error detecting voice activity: {e}")
            return False
    
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
        result = subprocess.run(
            ['exifTool', '-n', '-j', filepath],
            capture_output=True, text=True
        )
        metadata = json.loads(result.stdout)
        # logging.debug(f"ExifTool output for {filepath}: {metadata}")

        if not metadata or 'Error' in metadata[0]:
            logging.error(f"Error reading metadata from {filepath}: {metadata[0].get('Error', 'Unknown error')}")
            return None

        # pretty print metadata for debugging
        # print(json.dumps(metadata, indent=3))
        # input("Paused for debugging. Press Enter to continue...")

        fileExt = os.path.splitext(filepath)[1].lstrip(".").lower()

        Latitude  = metadata[0].get("GPSLatitude", "N/A") if "GPSLatitude" in metadata[0] else None
        Longitude = metadata[0].get("GPSLongitude", "N/A") if "GPSLongitude" in metadata[0] else None

        CreateDate = None
        #if "CreationDate" in metadata[0]:
        #    # CreateDate format: 2023:10:05 14:30:00+08:00, we only want the date and time part
        #    CreateDate = metadata[0].get("CreationDate", "N/A").split("+")[0]

        #if "GPSDateTime" in metadata[0]:
        #    # GPSDateTime format: 2023:10:05 14:30:00Z, replace the 'Z'
        #    CreateDate = metadata[0].get("GPSDateTime", "N/A").replace("Z", "")

        #if "DateTimeOriginal" in metadata[0]:
        #    CreateDate = metadata[0].get("DateTimeOriginal", "N/A")

        if "CreateDate" in metadata[0]:
            raw_date = metadata[0].get("CreateDate", "N/A")
            # Convert YYYY:MM:DD HH:MM:SS format to YYYY-MM-DD HH:MM:SS format
            if raw_date and raw_date != "N/A":
                CreateDate = raw_date.replace(":", "-", 2)  # Replace only first 2 colons
            else:
                CreateDate = raw_date

        # if fileExt in ["mp4", "mov"]:
        #if CreateDate is None or CreateDate == "N/A":
        #    print(f"\nFile detected: {filepath} no CreateDate")
        #    print(json.dumps(metadata[0], indent=3))
        #    # input("Paused for debugging. Press Enter to continue...")

        dummy_exif_data = {
            "SourceFile": filepath,
            "FileName": os.path.basename(filepath),
            "FileTypeExtension": os.path.splitext(filepath)[1].lstrip(".").lower(),
            "Latitude": Latitude,
            "Longitude": Longitude,
            "CreateDate": CreateDate,
        }
        return dummy_exif_data

    def extract_metadata(self, filepath):
        fileType = 'Undefined'
        extension = os.path.splitext(filepath)[1].lower()
        if extension in [".jpg", ".jpeg", ".png", ".heic"]:
            fileType = 'Image'
        elif extension in [".mp4", ".mov"]:
            fileType = 'Video'
        else:
            logging.warning(f"Unsupported file type for {filepath}. Skipping.")
            return None
        
        exif_data = self._run_exiftool(filepath)
        if not exif_data:
            return None

        stat_info = os.stat(filepath)
        base_metadata = {
            "filepath": os.path.abspath(filepath),   # exif_data.get("SourceFile", filepath),
            "filename": os.path.basename(filepath),  # exif_data.get("FileName", os.path.basename(filepath)),
            "file_extension": exif_data.get("FileTypeExtension", extension),
            "file_type": fileType,
            "size": stat_info.st_size,
            "creation_time": exif_data.get("CreateDate", None),
            "latitude": exif_data.get("Latitude", None),
            "longitude": exif_data.get("Longitude", None),
        }
        return base_metadata

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def get_geo_from_coordinates(self, latitude, longitude):
        if not self.geo_list_path:
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
            logging.info(f"Closest geo data found: {closest}")

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