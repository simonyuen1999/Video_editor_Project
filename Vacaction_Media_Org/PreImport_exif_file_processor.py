#!/usr/bin/env python3
"""
EXIF File Processor

This script traverses directories and performs comprehensive file processing:
1. Deletes dot files and LRF files
2. Extracts EXIF metadata using exiftool
3. Corrects file extensions based on EXIF FileType
4. Calculates creation time using sophisticated date logic
5. Extracts GPS coordinates
6. Generates CSV report and detailed log file

Usage:
    python exif_file_processor.py /path/to/directory
    
Requirements:
    - exiftool must be installed and accessible in PATH
    - Python 3.6+
"""

import os
import sys
import csv
import logging
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil


class ExifFileProcessor:
    def __init__(self, root_directory):
        self.root_directory = Path(root_directory)
        self.processed_files = []
        self.deleted_files = []
        self.renamed_files = []
        self.error_files = []
        
        # Setup logging
        self.setup_logging()
        
        # EXIF FileType to extension mapping - ALL UPPERCASE EXTENSIONS
        self.filetype_extensions = {
            'JPEG': '.JPG',
            'TIFF': '.TIF',
            'PNG': '.PNG',
            'GIF': '.GIF',
            'BMP': '.BMP',
            'WebP': '.WEBP',
            'HEIC': '.HEIC',
            'HEIF': '.HEIF',
            'MOV': '.MOV',
            'MP4': '.MP4',
            'AVI': '.AVI',
            'MKV': '.MKV',
            'WMV': '.WMV',
            'FLV': '.FLV',
            'M4V': '.M4V',
            'MPG': '.MPG',
            'MPEG': '.MPG',
            'CR2': '.CR2',
            'NEF': '.NEF',
            'ARW': '.ARW',
            'DNG': '.DNG',
            'RAW': '.RAW',
            'ORF': '.ORF',
            'RAF': '.RAF',
            'RW2': '.RW2',
            'PEF': '.PEF'
        }
    
    def setup_logging(self):
        """Setup comprehensive logging for all operations."""
        log_filename = f"exif_processor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.log_file = log_filename
        
        # Log session start
        self.logger.info("="*80)
        self.logger.info("EXIF File Processor Session Started")
        self.logger.info(f"Processing directory: {self.root_directory}")
        self.logger.info(f"Log file: {log_filename}")
        self.logger.info("="*80)
        
        print(f"📝 Log file: {log_filename}")
    
    def check_exiftool_available(self):
        """Check if exiftool is available in PATH."""
        try:
            result = subprocess.run(['exiftool', '-ver'], 
                                  capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            self.logger.info(f"ExifTool version {version} detected")
            print(f"✅ ExifTool version {version} available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.error("ExifTool not found in PATH")
            print("❌ ExifTool not found. Please install ExifTool and ensure it's in your PATH")
            return False
    
    def is_dot_file(self, filepath):
        """Check if file is a dot file (hidden file)."""
        return filepath.name.startswith('.')
    
    def is_lrf_file(self, filepath):
        """Check if file is an LRF file."""
        return filepath.suffix.upper() == '.LRF'
    
    def delete_unwanted_files(self):
        """Delete dot files and LRF files."""
        deleted_count = 0
        
        for root, dirs, files in os.walk(self.root_directory):
            root_path = Path(root)
            
            # Remove dot directories from traversal
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                filepath = root_path / filename
                
                if self.is_dot_file(filepath):
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        self.deleted_files.append(('dot_file', str(filepath)))
                        self.logger.info(f"Deleted dot file: {filepath}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete dot file {filepath}: {e}")
                
                elif self.is_lrf_file(filepath):
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        self.deleted_files.append(('lrf_file', str(filepath)))
                        self.logger.info(f"Deleted LRF file: {filepath}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete LRF file {filepath}: {e}")
        
        self.logger.info(f"Deleted {deleted_count} unwanted files")
        print(f"🗑️  Deleted {deleted_count} unwanted files (dot files + LRF files)")
    
    def get_exif_metadata(self, filepath):
        """Extract EXIF metadata using exiftool."""
        try:
            cmd = ['exiftool', '-j', '-n', '-CreateDate', '-FileInodeChangeDate', 
                   '-FileType', '-GPSAltitude', '-GPSLatitude', '-UserComment', str(filepath)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                metadata_list = json.loads(result.stdout)
                if metadata_list:
                    metadata = metadata_list[0]
                    self.logger.debug(f"EXIF extracted for {filepath}: {metadata}")
                    return metadata
            
            return {}
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ExifTool error for {filepath}: {e}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {filepath}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error extracting EXIF from {filepath}: {e}")
            return {}
    
    def correct_file_extension(self, filepath, exif_filetype):
        """Correct file extension based on EXIF FileType - Always use UPPERCASE extensions."""
        if not exif_filetype:
            # If no EXIF FileType, still convert to uppercase if needed
            return self._ensure_uppercase_extension(filepath)
        
        expected_extension = self.filetype_extensions.get(exif_filetype.upper())
        if not expected_extension:
            self.logger.warning(f"Unknown EXIF FileType '{exif_filetype}' for {filepath}")
            return self._ensure_uppercase_extension(filepath)
        
        current_extension = filepath.suffix.upper()  # Compare with uppercase
        
        # Always rename to uppercase extension, even if it matches the FileType but wrong case
        if current_extension != expected_extension or filepath.suffix != expected_extension:
            new_filepath = filepath.with_suffix(expected_extension)  # Use uppercase extension
            
            # Handle case-insensitive filesystem issue with two-step rename
            try:
                # Check if this is just a case change (same name, different case)
                if filepath.name.lower() == new_filepath.name.lower() and filepath.name != new_filepath.name:
                    # Two-step rename for case-insensitive filesystems
                    # Step 1: Rename to temporary name
                    temp_filepath = filepath.parent / (f"_{filepath.name}")
                    
                    # Ensure temp name doesn't exist
                    counter = 1
                    while temp_filepath.exists():
                        temp_filepath = filepath.parent / (f"_{counter}_{filepath.name}")
                        counter += 1
                    
                    # Step 1: Original → Temporary
                    filepath.rename(temp_filepath)
                    self.logger.debug(f"Step 1: {filepath} → {temp_filepath}")
                    
                    # Step 2: Temporary → Final
                    temp_filepath.rename(new_filepath)
                    self.logger.debug(f"Step 2: {temp_filepath} → {new_filepath}")
                    
                    self.renamed_files.append((str(filepath), str(new_filepath), f"Extension correction: {exif_filetype} (2-step)"))
                    self.logger.info(f"Renamed {filepath} → {new_filepath} (EXIF FileType: {exif_filetype}, 2-step)")
                    return new_filepath
                
                else:
                    # Regular rename (different filename)
                    # Check if target file already exists
                    if new_filepath.exists():
                        self.logger.warning(f"Cannot rename {filepath} to {new_filepath}: target exists")
                        return filepath
                    
                    filepath.rename(new_filepath)
                    self.renamed_files.append((str(filepath), str(new_filepath), f"Extension correction: {exif_filetype}"))
                    self.logger.info(f"Renamed {filepath} → {new_filepath} (EXIF FileType: {exif_filetype})")
                    return new_filepath
                    
            except Exception as e:
                self.logger.error(f"Failed to rename {filepath} to {new_filepath}: {e}")
                # Try to cleanup temp file if it exists
                try:
                    if 'temp_filepath' in locals() and temp_filepath.exists():
                        temp_filepath.rename(filepath)  # Restore original name
                        self.logger.info(f"Restored original filename after failed rename: {filepath}")
                except:
                    pass  # Best effort cleanup
                return filepath
        
        return filepath
    
    def _ensure_uppercase_extension(self, filepath):
        """Ensure file extension is uppercase."""
        if filepath.suffix and filepath.suffix != filepath.suffix.upper():
            new_filepath = filepath.with_suffix(filepath.suffix.upper())
            
            # On case-insensitive filesystems, abc.heic and abc.HEIC are considered the same
            # Use two-step rename: abc.heic → _abc.heic → abc.HEIC
            try:
                # Step 1: Rename to temporary name with underscore prefix
                temp_filepath = filepath.parent / (f"_{filepath.name}")
                
                # Ensure temp name doesn't exist
                counter = 1
                while temp_filepath.exists():
                    temp_filepath = filepath.parent / (f"_{counter}_{filepath.name}")
                    counter += 1
                
                # Step 1: Original → Temporary
                filepath.rename(temp_filepath)
                self.logger.debug(f"Step 1: {filepath} → {temp_filepath}")
                
                # Step 2: Temporary → Final uppercase
                final_filepath = filepath.parent / (filepath.stem + filepath.suffix.upper())
                temp_filepath.rename(final_filepath)
                self.logger.debug(f"Step 2: {temp_filepath} → {final_filepath}")
                
                self.renamed_files.append((str(filepath), str(final_filepath), "Extension case correction"))
                self.logger.info(f"Renamed {filepath} → {final_filepath} (uppercase extension, 2-step)")
                return final_filepath
                
            except Exception as e:
                self.logger.error(f"Failed to rename {filepath} to uppercase extension: {e}")
                # Try to cleanup temp file if it exists
                try:
                    if 'temp_filepath' in locals() and temp_filepath.exists():
                        temp_filepath.rename(filepath)  # Restore original name
                        self.logger.info(f"Restored original filename after failed rename: {filepath}")
                except:
                    pass  # Best effort cleanup
                return filepath
        
        return filepath
    
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
        
        self.logger.warning(f"Could not parse date: {date_string}")
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
                    self.logger.warning(f"Error converting timezone offset {tz_offset}: {e}")
            
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
    
    def calculate_creation_time(self, create_date_str, inode_change_date_str, filename=None):
        """Calculate creation time using sophisticated logic - all timezone-naive.
        
        Returns:
            tuple: (creation_time_str, method_code)
            method_code: 'FICD' = FileInodeChangeDate, 'CDOF' = CreateDate+Offset, 'FBCD' = Fallback CreateDate
        """
        create_date = self.parse_exif_date(create_date_str) if create_date_str else None
        inode_date = self.parse_exif_date(inode_change_date_str) if inode_change_date_str else None
        
        log_prefix = f"[{filename}] " if filename else ""
        
        # Case 2.0: CreateDate is missing (N/A case)
        if not create_date_str or create_date_str.strip() == '':
            self.logger.info(f"{log_prefix}CreateDate is missing, checking FileInodeChangeDate")
            # If FileInodeChangeDate has timezone offset, use it
            if inode_change_date_str and ('+' in inode_change_date_str or (len(inode_change_date_str) > 6 and '-' in inode_change_date_str[-6:])):
                self.logger.info(f"{log_prefix}Using FileInodeChangeDate with offset: {inode_change_date_str}")
                return inode_change_date_str, 'FICD'
            elif inode_date:
                self.logger.info(f"{log_prefix}Using FileInodeChangeDate: {inode_change_date_str}")
                return inode_change_date_str, 'FICD'
            return 'N/A', 'N/A'
        
        # Case 2.1: CreateDate is 0000:00:00 (zero case)
        if create_date_str.startswith('0000:00:00'):
            self.logger.info(f"{log_prefix}CreateDate is 0000:00:00, checking FileInodeChangeDate")
            # If FileInodeChangeDate has timezone offset, use it
            if inode_change_date_str and ('+' in inode_change_date_str or (len(inode_change_date_str) > 6 and '-' in inode_change_date_str[-6:])):
                self.logger.info(f"{log_prefix}Using FileInodeChangeDate with offset: {inode_change_date_str}")
                return inode_change_date_str, 'FICD'
            elif inode_date:
                self.logger.info(f"{log_prefix}Using FileInodeChangeDate: {inode_change_date_str}")
                return inode_change_date_str, 'FICD'
            return '0000:00:00', 'ZERO'
        
        # If no inode date, use create date
        if not inode_date:
            self.logger.info(f"{log_prefix}No FileInodeChangeDate available, using CreateDate: {create_date_str}")
            return create_date_str, 'FBCD'
        
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
            self.logger.error(f"{log_prefix}Error comparing dates - CreateDate: {create_date_str}, InodeDate: {inode_change_date_str}, Error: {e}")
            return create_date_str, 'FBCD'  # Fallback to original create date string
        
        # Case 2.1: FileInodeChangeDate is few days younger than CreateDate
        if date_diff > 1:
            try:
                # Use CreateDate YYYY:MM:DD hh:mm:ss but add timezone offset from FileInodeChangeDate
                creation_time_str = create_date.strftime('%Y:%m:%d %H:%M:%S')
                
                # Extract and append timezone offset from FileInodeChangeDate if it exists
                tz_offset = self.extract_timezone_offset(inode_change_date_str)
                if tz_offset:
                    creation_time_str += tz_offset
                
                self.logger.info(f"{log_prefix}Applied timezone offset to CreateDate: {create_date_str} + {tz_offset} → {creation_time_str}")
                return creation_time_str, 'CDOF'
            except Exception as e:
                self.logger.error(f"{log_prefix}Error applying timezone offset: {e}, falling back to CreateDate")
                return create_date_str, 'FBCD'
        
        # Case 2.2: Same day or one day difference - use FileInodeChangeDate
        elif abs(date_diff) <= 1:
            self.logger.info(f"{log_prefix}Using FileInodeChangeDate (same/1-day diff): {inode_change_date_str}")
            return inode_change_date_str, 'FICD'
        
        # Fallback to CreateDate
        else:
            self.logger.info(f"{log_prefix}Using CreateDate as fallback: {create_date_str}")
            return create_date_str, 'FBCD'
    
    def process_files(self):
        """Process all files in the directory tree."""
        processed_count = 0
        
        for root, dirs, files in os.walk(self.root_directory):
            root_path = Path(root)
            
            # Skip dot directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                filepath = root_path / filename
                
                # Skip remaining dot files and LRF files (in case cleanup missed some)
                if self.is_dot_file(filepath) or self.is_lrf_file(filepath):
                    continue
                
                try:
                    # Extract EXIF metadata
                    exif_data = self.get_exif_metadata(filepath)
                    
                    if not exif_data:
                        self.logger.warning(f"No EXIF data found for {filepath}")
                        continue
                    
                    # Correct file extension based on EXIF FileType
                    corrected_filepath = self.correct_file_extension(filepath, exif_data.get('FileType'))
                    
                    # Extract required EXIF fields
                    file_type = exif_data.get('FileType', 'N/A')
                    create_date = exif_data.get('CreateDate', '')
                    inode_change_date = exif_data.get('FileInodeChangeDate', '')
                    gps_altitude = exif_data.get('GPSAltitude', 'N/A')
                    gps_latitude = exif_data.get('GPSLatitude', 'N/A')
                    user_comment = exif_data.get('UserComment', '')
                    
                    bUpdateUserComment = False

                    # If user_comment is not present or not in UTC Zulu format, then use calculate_creation_time() to create creation_time
                    if user_comment.strip() == '' or not self.is_utc_zulu_format(user_comment):
                        # Calculate creation time using sophisticated logic
                        creation_time, creation_method = self.calculate_creation_time(create_date, inode_change_date, corrected_filepath.name)

                        # Convert creation time to UTC Zulu format
                        utc_time = self.convert_to_utc_zulu(creation_time)
                        user_comment = utc_time
                        bUpdateUserComment = True

                    else:
                        creation_time = user_comment
                        creation_method = 'IPUC'    # Import process and from UserComment
                        utc_time = user_comment

                    # Handle CreateDate (from media file EXIF) display logic for reporting
                    create_date_display = create_date if create_date else 'N/A'
                    if create_date and create_date.startswith('0000:00:00'):
                        create_date_display = '0000:00:00'
                    
                    # Store processed file information
                    file_info = {
                        'FileType': file_type,
                        'filename': corrected_filepath.name,
                        'CreateDate': create_date_display,
                        'FileInodeChangeDate': inode_change_date if inode_change_date else 'N/A',
                        'Creation_Method': creation_method,
                        # ------- Creation_time is either from calculation or from UserComment -------
                        'Creation_time': creation_time,
                        'UTC': utc_time,
                        'UserComment': user_comment,
                        # -----------------------------------------------
                        'GPSAltitude': gps_altitude,
                        'GPSLatitude': gps_latitude,
                    }
                    
                    # ------------------------------------------------------
                    # When EXIF of media file is updated (by update Geo info or other),
                    # 1. FileInodeChangeDate and FileModifyDate will be updated with the current time.
                    # 2. CreateDate remains unchanged.
                    # - - - - - - - - - - - - - - - - - - -
                    # During testing of updating Geo info, FileInodeChangeDate is updated, so the calculate_creation_time() is not working.
                    # We cannot re-execute the import process again.
                    # To avoid confusion, use UserComment to keep UTC (Zulu) creation time.
                    # 1. If UserComment is empty, we populate it with the calculated UTC time logic from calculate_creation_time().
                    # 2. If UserComment already has a value, we leave it unchanged.   That will be used in the import process.
                    # The Import process will prioritize UserComment for creation time if present.
                    # ------------------------------------------------------
                    if bUpdateUserComment:
                        try:
                            # Update UserComment using exiftool
                            cmd_update = ['exiftool', '-overwrite_original', 
                                          f'-UserComment={user_comment}', str(corrected_filepath)]
                            subprocess.run(cmd_update, capture_output=True, text=True, check=True)
                            self.logger.info(f">> For {corrected_filepath}, update UserComment to '{user_comment}' from '{inode_change_date}' and '{create_date}'")
                        except subprocess.CalledProcessError as e:
                            self.logger.error(f"Failed to update UserComment for {corrected_filepath}: {e}")
                    else:
                        self.logger.info(f">> For {corrected_filepath}, UserComment already has value '{user_comment}', so not updating the media file.")
                    # ------------------------------------------------------

                    self.processed_files.append(file_info)
                    processed_count += 1

                    if processed_count % 100 == 0:
                        print(f"📊 Processed {processed_count} files...")
                        
                except Exception as e:
                    self.error_files.append((str(filepath), str(e)))
                    self.logger.error(f"Error processing {filepath}: {e}")
        
        self.logger.info(f"Successfully processed {processed_count} files")
        print(f"✅ Processed {processed_count} files successfully")
    
    def generate_csv_report(self, output_filename='exif_report.csv'):
        """Generate CSV report with processed file information."""
        csv_path = self.root_directory.parent / output_filename
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['FileType', 'filename', 'CreateDate', 'FileInodeChangeDate', 
                             'Creation_Method', 'Creation_time', 'UTC', 'UserComment', 'GPSAltitude', 'GPSLatitude']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for file_info in self.processed_files:
                    writer.writerow(file_info)
            
            self.logger.info(f"CSV report generated: {csv_path}")
            print(f"📄 CSV report: {csv_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV report: {e}")
            print(f"❌ Failed to generate CSV report: {e}")
    
    def generate_summary_report(self):
        """Generate summary of processing results."""
        summary = f"""
EXIF File Processor Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Directory Processed: {self.root_directory}

Files Processed:
- Successfully processed: {len(self.processed_files)}
- Files deleted: {len(self.deleted_files)}
- Files renamed: {len(self.renamed_files)}
- Errors encountered: {len(self.error_files)}

Deleted Files Breakdown:
"""
        
        dot_files = sum(1 for item in self.deleted_files if item[0] == 'dot_file')
        lrf_files = sum(1 for item in self.deleted_files if item[0] == 'lrf_file')
        
        summary += f"- Dot files: {dot_files}\n"
        summary += f"- LRF files: {lrf_files}\n\n"
        
        if self.renamed_files:
            summary += "File Renames:\n"
            for old_name, new_name, reason in self.renamed_files:
                summary += f"- {Path(old_name).name} → {Path(new_name).name} ({reason})\n"
        
        if self.error_files:
            summary += f"\nErrors ({len(self.error_files)}):\n"
            for filepath, error in self.error_files[:10]:  # Show first 10 errors
                summary += f"- {Path(filepath).name}: {error}\n"
            if len(self.error_files) > 10:
                summary += f"... and {len(self.error_files) - 10} more errors (see log file)\n"
        
        self.logger.info("Processing Summary:\n" + summary)
        print("\n" + summary)
    
    def run(self):
        """Main processing workflow."""
        print(f"🚀 Starting EXIF File Processor")
        print(f"📁 Processing directory: {self.root_directory}")
        
        # Check if exiftool is available
        if not self.check_exiftool_available():
            return False
        
        try:
            # Step 1: Delete unwanted files
            print("🗑️  Cleaning up unwanted files...")
            self.delete_unwanted_files()
            
            # Step 2: Process remaining files
            print("🔍 Processing files with EXIF analysis...")
            self.process_files()
            
            # Step 3: Generate reports
            print("📊 Generating reports...")
            self.generate_csv_report()
            self.generate_summary_report()
            
            # Log session completion
            self.logger.info("="*80)
            self.logger.info("EXIF File Processor Session Completed Successfully")
            self.logger.info(f"Total files processed: {len(self.processed_files)}")
            self.logger.info(f"Log file: {self.log_file}")
            self.logger.info("="*80)
            
            print("✅ Processing completed successfully!")
            return True
            
        except Exception as e:
            self.logger.critical(f"Critical error during processing: {e}")
            print(f"❌ Critical error: {e}")
            return False


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) == 2:
        directory_path = sys.argv[1]
    else:
        # Prompt user for directory path if not provided
        print("Usage: python exif_file_processor.py <directory_path>")
        print("\nExample:")
        print("  python exif_file_processor.py /path/to/photos")
        print("\n" + "="*50)
        
        try:
            directory_path = input("Please enter the directory path to process: ").strip()
            if not directory_path:
                print("❌ No directory path provided.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user.")
            sys.exit(1)
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory does not exist: {directory_path}")
        sys.exit(1)
    
    if not os.path.isdir(directory_path):
        print(f"❌ Path is not a directory: {directory_path}")
        sys.exit(1)
    
    # Initialize and run processor
    processor = ExifFileProcessor(directory_path)
    success = processor.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()