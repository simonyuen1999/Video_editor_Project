#!python
import os
import re

def clean_and_rename_videos():
    # Regex pattern for DJI filenames
    pattern = re.compile(r"^DJI_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_\d+_D\.MP4$", re.IGNORECASE)

    for filename in os.listdir("."):
        # Remove .LRF files
        if filename.lower().endswith(".lrf"):
            print(f"Deleting: {filename}")
            os.remove(filename)
            continue

	# Remove any file with "- Copy" in its name
        if "- Copy" in filename:
            print(f"Deleting (copy file): {filename}")
            os.remove(filename)
            continue

        # Rename .MP4 files
        match = pattern.match(filename)
        if match:
            year, month, day, hour, minute, second = match.groups()
            new_name = f"{year}-{month}-{day}_{hour}-{minute}-{second}.MP4"

            if not os.path.exists(new_name):  # avoid overwrite
                print(f"Renaming: {filename} -> {new_name}")
                os.rename(filename, new_name)
            else:
                print(f"Skipped (already exists): {new_name}")

if __name__ == "__main__":
    clean_and_rename_videos()

