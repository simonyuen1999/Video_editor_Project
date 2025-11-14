#!python
import os
import datetime
import exiftool
import json
import subprocess

# --- Logging Setup ---
log_file = "Fix_Media_to_UTC.log"

def log_print(message):
    """Print to console and write to log file."""
    print(message)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# Initialize log file (overwrite existing)
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"=== Fix Media to UTC Log - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

dry_run = False   # Change to False after testing!

# --- Configuration ---
directory = input("Enter the directory path to process HEIC files: ").strip()
if not directory:
    log_print("❌ No directory specified. Exiting.")
    exit(1)

if not os.path.exists(directory):
    log_print(f"❌ Directory '{directory}' does not exist. Exiting.")
    exit(1)

log_print(f"📁 Processing directory: {directory}")
log_print(f"🔧 Dry run mode: {'ON' if dry_run else 'OFF'}")

def get_metadata(filepath):
    """Call exiftool and return metadata as a Python dict."""
    result = subprocess.run(
        ["exiftool", "-j", "-n", filepath],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    return data[0] if data else {}

# --- Helper function ---
def to_utc(local_time_str, offset_str):
    """
    Convert local time + offset to UTC datetime string.
    Handles cases where the time is already in UTC (ending with 'Z').
    """
    if not local_time_str:
        return None

    # If time already marked as UTC, just normalize and return
    if local_time_str.endswith("Z"):
        # Remove 'Z' and return as-is (already UTC)
        clean = local_time_str.replace("Z", "")
        try:
            datetime.datetime.strptime(clean, "%Y:%m:%d %H:%M:%S")
            return clean
        except ValueError:
            # If parsing fails, return original
            return clean

    # Try parsing normal EXIF datetime (e.g. 2024:06:20 15:42:11)
    try:
        local_time = datetime.datetime.strptime(local_time_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        log_print(f"⚠️ Skipping unparsable time: {local_time_str}")
        return None

    # Apply offset if available
    if offset_str and len(offset_str) == 6 and offset_str[1:].replace(':','').isdigit():
        sign = 1 if offset_str[0] == '+' else -1
        hours, minutes = map(int, offset_str[1:].split(':'))
        offset = datetime.timedelta(hours=hours, minutes=minutes)
        local_time = local_time - sign * offset  # Convert to UTC

    return local_time.strftime("%Y:%m:%d %H:%M:%S")

def parse_datetime_with_offset(dt_str):
    """Parse strings like 2024:06:20 15:42:11+08:00 → UTC datetime."""
    if not dt_str:
        return None
    # Remove fractional seconds if present
    if "." in dt_str:
        dt_str = dt_str.split(".")[0] + dt_str.split(".")[1][-6:] if "+" in dt_str else dt_str.split(".")[0]
    # Normalize separators (QuickTime sometimes uses space or T)
    dt_str = dt_str.replace("T", " ")

    # Handle UTC already (ending with Z)
    if dt_str.endswith("Z"):
        try:
            return datetime.datetime.strptime(dt_str[:-1], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.datetime.fromisoformat(dt_str[:-1])
            except ValueError:
                return None

    # Try standard EXIF-like format with offset
    try:
        if "+" in dt_str[10:] or "-" in dt_str[10:]:
            # Handles +08:00 or -05:00 offsets
            # Replace ":" in offset for Python <3.11 compatibility
            main, offset = dt_str[:-6], dt_str[-6:]
            offset = offset.replace(":", "")
            t = datetime.datetime.strptime(main, "%Y:%m:%d %H:%M:%S")
            sign = 1 if dt_str[-6] == "+" else -1
            hours = int(offset[1:3])
            minutes = int(offset[3:5])
            delta = datetime.timedelta(hours=hours, minutes=minutes)
            return t - sign * delta
        else:
            return datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None

def format_exif(dt):
    """Return datetime string in EXIF UTC format."""
    return dt.strftime("%Y:%m:%d %H:%M:%S")

def check_and_rename_misnamed_files(filepath, metadata):
    """
    Check if file extension matches actual file type for ANY file type.
    Renames misnamed files using pattern: XXXX_OLDEXT.CORRECTEXT
    Returns the new filepath if renamed, otherwise returns original filepath
    """
    # Get actual file type from metadata
    file_type = metadata.get("FileType") or metadata.get("MIMEType", "").split("/")[-1].upper()
    filename = os.path.basename(filepath)
    directory = os.path.dirname(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    current_ext = os.path.splitext(filename)[1].upper()
    
    # Define mapping of file types to expected extensions
    file_type_extensions = {
        "JPEG": ".JPEG", "JPG": ".JPEG", "PNG": ".PNG", "TIFF": ".TIFF", "TIF": ".TIFF",
        "HEIF": ".HEIC", "HEIC": ".HEIC", "MOV": ".MOV", "MP4": ".MP4", "AVI": ".AVI",
        "GIF": ".GIF", "BMP": ".BMP", "WEBP": ".WEBP"
    }
    
    # Get the correct extension for this file type
    correct_ext = file_type_extensions.get(file_type)
    
    # Check if extension doesn't match the actual file type
    if correct_ext and current_ext != correct_ext and current_ext != "":
        old_ext_clean = current_ext.lstrip(".")
        new_filename = f"{name_without_ext}_{old_ext_clean}{correct_ext}"
        new_filepath = os.path.join(directory, new_filename)
        
        try:
            if os.path.exists(new_filepath):
                log_print(f"⚠️ Skip rename - target exists: {new_filename}")
                return filepath
            
            os.rename(filepath, new_filepath)
            log_print(f"🔄 RENAMED: {filename} → {new_filename} ({current_ext}→{file_type})")
            return new_filepath
            
        except Exception as e:
            log_print(f"❌ Rename failed: {filename} - {e}")
            return filepath
    
    # No mismatch found - file extension matches file type
    return filepath

# --- Main process ---
renamed_files = []
processed_files = 0
updated_files = 0

with exiftool.ExifTool() as et:
    for root, _, files in os.walk(directory):
        for file in files:

            bUpdate = False

            # DJI .MP4 is using UTC already, skip it.
            if file.lower().endswith(".mp4"):
                continue

            date_local = ''
            offset = ''

            filepath = os.path.join(root, file)
            metadata = get_metadata(filepath)

            # Check and rename misnamed files first
            original_filepath = filepath
            filepath = check_and_rename_misnamed_files(filepath, metadata)
            
            # If file was renamed, get updated metadata and filename
            if filepath != original_filepath:
                renamed_files.append((original_filepath, filepath))
                metadata = get_metadata(filepath)
                file = os.path.basename(filepath)

            processed_files += 1

            if file.lower().endswith(".mov"):
                dtog = metadata.get("DateTimeOriginal")
                cred = metadata.get("CreateDate")
                crnd = metadata.get("CreationDate")
                # print(f"DEBUG: {file} | DateTimeOriginal: {dtog}, CreateDate: {cred}, CreationDate: {crnd}")

                # Some MOV files CreationDate is None
                if crnd and crnd.endswith("Z"):
                    log_print(f"{file} | CreationDate (used by PhotoPrism) already in UTC format {crnd}")
                    continue

                date_local = dtog or cred or crnd

                if not date_local:
                    log_print(f"❌ No DateTimeOriginal/CreateDate/CreationDate found for {file}")
                    continue

                utc_dt = parse_datetime_with_offset(date_local)
                if not utc_dt:
                    log_print(f"❌ Unable to parse datetime for {file}: {date_local}")
                    continue

                utc_time = format_exif(utc_dt)
                log_print(f"{file} | Local: {date_local} → CreationDate to UTC: {utc_time}")
                bUpdate = True

            elif file.lower().endswith((".heic",".heif",".jpeg",".jpg",".png",".tiff",".tif")):

                date_local = metadata.get("DateTimeOriginal")
                offset = metadata.get("OffsetTimeOriginal") or metadata.get("OffsetTime")

                if date_local is None:
                    log_print(f"❌ No DateTimeOriginal found for {file}")
                    continue

                # Check if already in UTC - different methods for different file types
                actual_file_type = metadata.get("FileType", "").upper()
                
                # For HEIC/HEIF/MOV/MP4: Check for "Z" suffix
                if actual_file_type in ["HEIC", "HEIF", "MOV", "MP4"] and date_local.endswith("Z"):
                    continue  # Skip - already UTC
                
                # For JPEG/TIFF/PNG: Check offset fields for +00:00 (UTC indicator)
                elif actual_file_type in ["JPEG", "JPG", "TIFF", "PNG"]:
                    if offset == "+00:00" or offset == "Z":
                        continue  # Skip - already UTC
                
                # Process the file if not already in UTC
                utc_time = to_utc(date_local, offset)
                if not utc_time:
                    log_print(f"❌ Could not convert to UTC for {file}")
                    continue
                log_print(f"📅 {file} | {date_local} {offset or ''} → UTC: {utc_time}")
                bUpdate = True

            if not dry_run and bUpdate:
                # Check file permissions and properties
                #try:
                #    stat_info = os.stat(filepath)
                #    log_print(f"📋 File permissions: {oct(stat_info.st_mode)}")
                #    log_print(f"📏 File size: {stat_info.st_size} bytes")
                #    log_print(f"🔒 File writable: {os.access(filepath, os.W_OK)}")
                #except Exception as stat_e:
                #    log_print(f"⚠️ Could not get file stats: {stat_e}")

                try:
                    # Get file type and check for Reconyx metadata
                    actual_file_type = metadata.get("FileType", "").upper()
                    has_reconyx = any(key.startswith('Reconyx') for key in metadata.keys())
                    
                    # Prepare ExifTool command with warning suppression
                    # The Reconyx warning is a Perl warning that needs to be suppressed at stderr level
                    cmd = ["exiftool", "-overwrite_original"]
                    
                    # Add appropriate verbosity and warning suppression
                    if has_reconyx:
                        cmd.extend(["-q", "-m"])  # Quiet mode + ignore minor errors
                    else:
                        cmd.extend(["-verbose2"])  # Keep verbose for non-Reconyx files
                    
                    # Handle timezone differently for different file types
                    if actual_file_type in ["HEIC", "HEIF", "MOV", "MP4"]:
                        # These formats support Z suffix for UTC
                        log_print(f"📋 Using Z suffix for {actual_file_type} format")
                        cmd.extend([
                            f"-DateTimeOriginal={utc_time}Z",
                            f"-CreationDate={utc_time}Z", 
                            f"-CreateDate={utc_time}Z",
                            f"-ModifyDate={utc_time}Z"
                        ])
                    elif actual_file_type in ["JPEG", "JPG", "TIFF", "PNG"]:
                        # JPEG/EXIF formats don't support Z suffix, use offset fields
                        log_print(f"📋 Using offset fields for {actual_file_type} format")
                        
                        # For Reconyx files, use EXIF-specific fields
                        if has_reconyx:
                            cmd.extend([
                                f"-EXIF:DateTimeOriginal={utc_time}", f"-EXIF:CreateDate={utc_time}",
                                f"-EXIF:ModifyDate={utc_time}", "-EXIF:OffsetTimeOriginal=+00:00",
                                "-EXIF:OffsetTime=+00:00", "-EXIF:OffsetTimeDigitized=+00:00", "-ignoreMinorErrors"
                            ])
                        else:
                            cmd.extend([
                                f"-DateTimeOriginal={utc_time}", f"-CreateDate={utc_time}", f"-ModifyDate={utc_time}",
                                "-OffsetTimeOriginal=+00:00", "-OffsetTime=+00:00", "-OffsetTimeDigitized=+00:00"
                            ])
                    else:
                        # Default handling - try Z suffix first
                        cmd.extend([
                            f"-DateTimeOriginal={utc_time}Z", f"-CreationDate={utc_time}Z", 
                            f"-CreateDate={utc_time}Z", f"-ModifyDate={utc_time}Z"
                        ])
                    
                    cmd.append(filepath)
                    
                    # Set environment to suppress Perl warnings
                    env = os.environ.copy()
                    env['PERL_NOWARN'] = '1'
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                    
                    # Filter out Reconyx warnings and only show important errors
                    if result.stderr:
                        stderr_lines = [line for line in result.stderr.split('\n') 
                                      if line.strip() and not ("Use of uninitialized value" in line and "Reconyx:DateTimeOriginal" in line)]
                        if stderr_lines:
                            log_print(f"❌ {file}: {stderr_lines[0]}")  # Show only first error
                    
                    if result.returncode == 0:
                        log_print(f"✅ {file}: Updated")
                        updated_files += 1
                    else:
                        log_print(f"❌ {file}: Failed (code {result.returncode})")
                        
                except Exception as e:
                    log_print(f"❌ {file}: Error - {e}")
            elif dry_run and bUpdate:
                log_print(f"🔸 DRY RUN: {file} → {utc_time}")

# Log completion summary
log_print(f"\n" + "="*60)
log_print(f"📊 PROCESSING SUMMARY")
log_print(f"="*60)
log_print(f"📁 Directory: {directory}")
log_print(f"🔢 Total files processed: {processed_files}")
log_print(f"✅ Files successfully updated: {updated_files}")
log_print(f"🔄 Files renamed: {len(renamed_files)}")

if renamed_files:
    log_print(f"\n📝 RENAMED FILES:")
    for old_path, new_path in renamed_files:
        old_name = os.path.basename(old_path)
        new_name = os.path.basename(new_path)
        log_print(f"   {old_name} → {new_name}")

log_print(f"\n✅ Process completed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log_print(f"📄 Log saved to: {os.path.abspath(log_file)}")

