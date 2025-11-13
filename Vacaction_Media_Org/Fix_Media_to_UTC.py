#!python
import os
import datetime
import exiftool
import json
import subprocess

dry_run = False   # Change to False after testing!

# --- Configuration ---
directory = input("Enter the directory path to process HEIC files: ").strip()
if not directory:
    print("❌ No directory specified. Exiting.")
    exit(1)

if not os.path.exists(directory):
    print(f"❌ Directory '{directory}' does not exist. Exiting.")
    exit(1)

print(f"📁 Processing directory: {directory}")

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
        print(f"⚠️ Skipping unparsable time: {local_time_str}")
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

# --- Main process ---
with exiftool.ExifTool() as et:
    for root, _, files in os.walk(directory):
        for file in files:

            bUpdate = False

            # DJI .MP4 is using UTC already. Skip .jpg, .jpeg, .png as well
            # Only process .heic and .mov files
            if not file.lower().endswith((".heic",".mov")):
                continue

            date_local = ''
            offset = ''

            filepath = os.path.join(root, file)
            metadata = get_metadata(filepath)

            if file.lower().endswith(".mov"):
                dtog = metadata.get("DateTimeOriginal")
                cred = metadata.get("CreateDate")
                crnd = metadata.get("CreationDate")
                # print(f"DEBUG: {file} | DateTimeOriginal: {dtog}, CreateDate: {cred}, CreationDate: {crnd}")

                # Some MOV files CreationDate is None
                if crnd and crnd.endswith("Z"):
                    print(f"{file} | CreationDate (used by PhotoPrism) already in UTC format {crnd}")
                    continue

                date_local = dtog or cred or crnd

                if not date_local:
                    print(f"❌ No DateTimeOriginal/CreateDate/CreationDate found for {file}")
                    continue

                utc_dt = parse_datetime_with_offset(date_local)
                if not utc_dt:
                    print(f"❌ Unable to parse datetime for {file}: {date_local}")
                    continue

                utc_time = format_exif(utc_dt)
                print(f"{file} | Local: {date_local} → CreationDate to UTC: {utc_time}")
                bUpdate = True

            elif file.lower().endswith(".heic"):
                date_local = metadata.get("DateTimeOriginal")
                offset = metadata.get("OffsetTimeOriginal") or metadata.get("OffsetTime")

                if date_local.endswith("Z"):
                    clean = date_local.replace("Z", "")
                    print(f"{file} | already in UTC {date_local}")
                else:
                    utc_time = to_utc(date_local, offset)
                    if not utc_time:
                        print(f"❌ No DateTimeOriginal found for {file}")
                        continue
                    print(f"{file} | Local: {date_local} {offset or ''} → UTC: {utc_time}")
                    bUpdate = True

            if not dry_run and bUpdate:
                # Update DateTimeOriginal, CreateDate, ModifyDate to UTC (with 'Z')
                et.execute(
                    b"-overwrite_original",
                    b"-DateTimeOriginal=" + bytes(utc_time + "Z", "utf-8"),
                    b"-CreationDate=" + bytes(utc_time + "Z", "utf-8"),
                    b"-CreateDate=" + bytes(utc_time + "Z", "utf-8"),
                    b"-ModifyDate=" + bytes(utc_time + "Z", "utf-8"),
                    bytes(filepath, "utf-8")
                )

