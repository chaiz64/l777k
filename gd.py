from google.colab import drive
import os
import shutil
import subprocess
from datetime import timedelta
import pandas as pd
import logging
from tqdm.notebook import tqdm # Use tqdm.notebook for Google Colab
import hashlib # For checksum verification

# --- Configuration ---
# Source directory path where your videos are located
SOURCE_DIR = '/content/DouyinLiveRecorder/downloads/抖音直播'
# Target directory path in Google Drive where backups will be stored
TARGET_DIR = '/content/drive/MyDrive/8888/ColabDL' # Can be modified as needed

# Advanced Configuration
ENABLE_CHECKSUM_VERIFICATION = True # Set to True to verify file integrity after copying
LOG_TO_FILE = True # Set to True to save logs to a file in the target directory
LOG_FILE_NAME = 'backup_log.log' # Name of the log file if LOG_TO_FILE is True
# --------------------

# Set up logging
# Remove any existing handlers to prevent duplicate logs if the cell is run multiple times
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to install FFmpeg if not present
def install_ffmpeg():
    """
    Checks if ffprobe is installed and installs FFmpeg if it's not found.
    FFmpeg includes ffprobe, which is necessary for getting video durations.
    """
    try:
        subprocess.run(['ffprobe', '-h'], check=True, capture_output=True)
        logging.info("FFmpeg (ffprobe) is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.warning("FFmpeg (ffprobe) not found. Attempting to install FFmpeg...")
        try:
            # Update apt-get and install ffmpeg
            subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
            subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], check=True, capture_output=True)
            logging.info("FFmpeg installed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install FFmpeg: {e.stderr.decode()}. Please install it manually.")
            raise RuntimeError("FFmpeg installation failed.")

# Function to calculate MD5 checksum of a file
def calculate_md5(file_path, chunk_size=8192):
    """
    Calculates the MD5 checksum of the given file.

    Args:
        file_path (str): The path to the file.
        chunk_size (int): The size of chunks to read from the file.

    Returns:
        str: The MD5 checksum in hexadecimal format, or None if an error occurs.
    """
    try:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating MD5 for {file_path}: {e}")
        return None

# Modified section: Check and mount Google Drive
logging.info("Mounting Google Drive...")
try:
    drive.mount('/content/drive')
    logging.info("Google Drive mounted successfully.")
except AttributeError as e:
    # This error typically occurs when not running in Google Colab
    error_message = (
        "Failed to mount Google Drive. This script is designed to run in a Google Colab environment. "
        "The error 'NoneType' object has no attribute 'kernel' indicates that the necessary "
        "Colab environment components are not available. Please run this script in a Colab notebook."
    )
    logging.error(error_message)
    print(f"❌ {error_message}")
    # Stop the script
    raise RuntimeError("This script must be run in a Google Colab notebook.")
except Exception as e:
    logging.error(f"Failed to mount Google Drive: {e}")
    raise

# Ensure FFmpeg is installed
install_ffmpeg()

# Check if source directory exists
if not os.path.exists(SOURCE_DIR):
    logging.error(f"Source directory not found: {SOURCE_DIR}")
    raise FileNotFoundError(f"Source directory not found: {SOURCE_DIR}")
logging.info(f"Source directory found: {SOURCE_DIR}")

# Create target directory (if it doesn't exist)
try:
    os.makedirs(TARGET_DIR, exist_ok=True)
    logging.info(f"Checked and created target directory: {TARGET_DIR}")
except Exception as e:
    logging.error(f"Failed to create target directory: {e}")
    raise

# Configure file logging if enabled
if LOG_TO_FILE:
    log_file_path = os.path.join(TARGET_DIR, LOG_FILE_NAME)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    logging.info(f"Logging to file enabled: {log_file_path}")

# Get video file duration (using ffprobe)
def get_video_duration(file_path):
    """
    Retrieves the duration of a video file using ffprobe.

    Args:
        file_path (str): The path to the video file.

    Returns:
        str: The duration in HH:MM:SS format, or "N/A" if an error occurs.
    """
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of',
            'default=noprint_wrappers=1:nokey=1', file_path
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        duration_str = result.stdout.strip()
        duration = float(duration_str)
        return duration # Return duration in seconds
    except (subprocess.CalledProcessError, ValueError) as e:
        logging.warning(f"Could not get duration for file {file_path}: {e}. Returning 0.0.")
        return 0.0 # Return 0.0 for error cases to allow filtering
    except FileNotFoundError:
        # This error should ideally be caught by install_ffmpeg, but kept for robustness
        logging.error(" 'ffprobe' not found. Please ensure FFmpeg is installed.")
        return 0.0

def format_duration(seconds):
    """
    Formats a duration in seconds into HH:MM:SS string format, without milliseconds.
    """
    total_seconds = int(seconds) # Convert to integer seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Scan video files and return as DataFrame
def scan_video_files(directory):
    """
    Scans a directory for video files (.mp4, .ts) and collects their information.

    Args:
        directory (str): The directory to scan.

    Returns:
        pd.DataFrame: A DataFrame containing video file information.
    """
    logging.info(f"Scanning video files in: {directory}")
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.mp4', '.ts')):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path) / (1024 * 1024) # MB
                    duration_seconds = get_video_duration(file_path)
                    video_files.append({
                        "File Name": file,
                        "Path": file_path,
                        "Size (MB)": round(size, 2),
                        "DurationSeconds": duration_seconds, # Store raw seconds
                        "Duration": format_duration(duration_seconds) # Store formatted duration for display
                    })
                except OSError as e:
                    logging.warning(f"Could not access file {file_path}: {e}. Skipping this file.")
    logging.info(f"Scan complete. Found {len(video_files)} video files.")
    return pd.DataFrame(video_files)

# Scan and display file information
df_raw = scan_video_files(SOURCE_DIR)

# Filter out files shorter than 10 minutes (600 seconds)
MIN_DURATION_SECONDS = 600
df = df_raw[df_raw['DurationSeconds'] >= MIN_DURATION_SECONDS].copy()

if len(df_raw) > 0:
    logging.info(f"Found {len(df_raw)} video files in total. {len(df)} files meet the minimum duration requirement (>= {MIN_DURATION_SECONDS/60} minutes).")
else:
    print("❌ No MP4/TS video files found in the source directory.") # Keep print for user visibility

# Select files to copy
copied_count = 0
skipped_count = 0
failed_count = 0
verified_count = 0
checksum_mismatch_count = 0

if len(df) > 0:
    print("\nAvailable video files (Index, File Name, Size (MB), Duration):")

    # Fixed column widths based on user's example
    idx_col_width = 9
    name_col_width = 50
    size_col_width = 12
    duration_col_width = 12

    # Print header
    print(f"|{'-'*idx_col_width}|{'-'*name_col_width}|{'-'*size_col_width}|{'-'*duration_col_width}|")
    print(f"|{'Index'.center(idx_col_width)}|{'File Name'.center(name_col_width)}|{'Size (MB)'.center(size_col_width)}|{'Duration'.center(duration_col_width)}|")
    print(f"|{'-'*idx_col_width}|{'-'*name_col_width}|{'-'*size_col_width}|{'-'*duration_col_width}|")

    # Print data rows by iterating through the DataFrame
    for index, row in df.iterrows():
        idx_val = str(index)
        file_name_val = str(row['File Name'])
        size_val = f"{row['Size (MB)']:.2f}"
        duration_val = str(row['Duration'])

        # Truncate file name if too long
        if len(file_name_val) > name_col_width:
            file_name_val = file_name_val[:name_col_width-3] + "..."

        # Pad each value to its column width, centering them
        idx_padded = idx_val.center(idx_col_width)
        name_padded = file_name_val.center(name_col_width)
        size_padded = size_val.center(size_col_width)
        duration_padded = duration_val.center(duration_col_width)

        print(f"|{idx_padded}|{name_padded}|{size_padded}|{duration_padded}|")

    # Print footer
    print(f"|{'-'*idx_col_width}|{'-'*name_col_width}|{'-'*size_col_width}|{'-'*duration_col_width}|")

    print("\n🔄 Please select files to copy (enter Index numbers, comma-separated, or 'all' to copy all):")
    logging.info("Prompting user for file selection.")
    choice = input("Your choice: ").strip()

    selected_files_paths = []
    if choice.lower() == 'all':
        selected_files_paths = df['Path'].tolist()
    else:
        processed_indices = set() # To store unique valid indices
        for item in choice.split(','):
            try:
                idx = int(item.strip())
                if 0 <= idx < len(df):
                    if idx not in processed_indices: # Avoid adding duplicates if user enters same index multiple times
                        selected_files_paths.append(df.iloc[idx]['Path'])
                        processed_indices.add(idx)
                else:
                    print(f"⚠️ Invalid Index number {idx}. It will be skipped.")
                    logging.warning(f"User entered invalid Index: {idx}")
            except ValueError:
                print(f"❌ Invalid input '{item.strip()}'. Please enter Index numbers or 'all'.")
                logging.error(f"User entered invalid input part: {item.strip()}")

    if selected_files_paths:
        logging.info(f"Starting copy of {len(selected_files_paths)} files.")
        print(f"\nCopying {len(selected_files_paths)} files...") # Keep print for user visibility
        for src in tqdm(selected_files_paths, desc="Copying"):
            file_name = os.path.basename(src)
            dst = os.path.join(TARGET_DIR, file_name)

            if os.path.exists(dst):
                logging.info(f"Skipping existing file: {file_name}")
                print(f"⏩ Skipping: '{file_name}' already exists in the target.") # Keep print for user visibility
                skipped_count += 1
                continue

            try:
                shutil.copy2(src, dst)
                logging.info(f"Successfully copied: {file_name}")
                copied_count += 1

                if ENABLE_CHECKSUM_VERIFICATION:
                    src_md5 = calculate_md5(src)
                    dst_md5 = calculate_md5(dst)

                    if src_md5 and dst_md5 and src_md5 == dst_md5:
                        logging.info(f"Checksum verified for {file_name}: MD5 Match.")
                        print(f"✅ Copied and Verified: '{file_name}' (MD5 Match)") # Keep print for user visibility
                        verified_count += 1
                    else:
                        logging.warning(f"Checksum mismatch for {file_name}. Source MD5: {src_md5}, Dest MD5: {dst_md5}")
                        print(f"⚠️ Copied but Checksum Mismatch: '{file_name}' (Source MD5: {src_md5}, Dest MD5: {dst_md5})") # Keep print for user visibility
                        checksum_mismatch_count += 1
                else:
                    print(f"✅ Copied: '{file_name}'") # Keep print for user visibility

            except Exception as e:
                logging.error(f"Failed to copy: {file_name} - {e}")
                print(f"❌ Failed to copy: '{file_name}' - {e}") # Keep print for user visibility
                failed_count += 1
    else:
        logging.info("No files selected for copying.")
        print("No files selected for copying.") # Keep print for user visibility

    # Option to delete source files
    if copied_count > 0:
        print("\n❓ Do you want to delete the successfully copied source files? (y/n)")
        logging.info("Prompting user for source file deletion choice.")
        delete_choice = input("Your choice: ").strip().lower()
        if delete_choice == 'y':
            deleted_count = 0
            logging.info("User chose to delete source files. Starting deletion...")
            print("\nDeleting source files...") # Keep print for user visibility
            # Filter selected_files_paths to only include those that were successfully copied
            files_to_delete = [
                src for src in selected_files_paths
                if os.path.exists(os.path.join(TARGET_DIR, os.path.basename(src)))
            ]

            for src in tqdm(files_to_delete, desc="Deleting"):
                file_name = os.path.basename(src)
                try:
                    os.remove(src)
                    logging.info(f"Successfully deleted source file: {file_name}")
                    print(f"🗑️ Deleted: '{file_name}'") # Keep print for user visibility
                    deleted_count += 1
                except Exception as e:
                    logging.warning(f"Failed to delete source file: {file_name} - {e}")
                    print(f"⚠️ Failed to delete: '{file_name}' - {e}") # Keep print for user visibility
            logging.info(f"Deletion summary: Deleted {deleted_count} files.")
            print(f"\n🗑️ Deleted {deleted_count} source files.") # Keep print for user visibility
        else:
            logging.info("User chose not to delete source files.")
            print("Source files were not deleted.") # Keep print for user visibility

# Summary Report
logging.info(f"Operation Summary: Copied={copied_count}, Verified={verified_count}, Mismatch={checksum_mismatch_count}, Skipped={skipped_count}, Failed={failed_count}")
print("\n--- Summary Report ---") # Keep print for user visibility
print(f"✅ Successfully copied: {copied_count} files") # Keep print for user visibility
if ENABLE_CHECKSUM_VERIFICATION:
    print(f"✔️ Successfully verified (MD5 Match): {verified_count} files") # Keep print for user visibility
    print(f"❗ Checksum Mismatch (copied but not verified): {checksum_mismatch_count} files") # Keep print for user visibility
print(f"⏩ Skipped (already exists in target): {skipped_count} files") # Keep print for user visibility
print(f"❌ Failed to copy: {failed_count} files") # Keep print for user visibility

# Unmount Google Drive (optional)
logging.info("Unmounting Google Drive...")
try:
    drive.flush_and_unmount()
    logging.info("Google Drive unmounted successfully.")
except Exception as e:
    logging.error(f"Failed to unmount Google Drive: {e}")

print("\n🎉 Operation complete!")
