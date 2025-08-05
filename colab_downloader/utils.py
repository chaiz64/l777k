import os
import subprocess
import shutil
import json

def format_duration(seconds):
    """
    Converts duration from seconds into a human-readable format (e.g., 1h 2m 3s).
    """
    if seconds is None or seconds < 0:
        return "N/A"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or (hours > 0 and secs > 0):
        parts.append(f"{minutes}m")
    if secs > 0 or (hours == 0 and minutes == 0):
        parts.append(f"{secs}s")

    return " ".join(parts) if parts else "0s"

def format_bytes(bytes_value):
    """
    Converts file size from bytes into a human-readable format (KB, MB, GB, TB, PB).
    """
    if bytes_value is None or bytes_value < 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(bytes_value)

    for i in range(len(units)):
        if size < 1024:
            return f"{size:.2f} {units[i]}"
        size /= 1024
    return f"{size:.2f} {units[-1]}"

def _simulate_duration_fallback(file_name, file_path_for_size):
    """
    Helper function to simulate duration if ffprobe fails or is not found.
    This is a fallback mechanism.
    """
    duration_seconds = 0.0
    print(f"    [Fallback] Attempting to simulate duration for: {file_name}")
    try:
        duration_parts = [part for part in file_name.split('_') if 's' in part and part[:-1].isdigit()]
        if duration_parts:
            duration_match_str = duration_parts[-1]
            duration_seconds = float(duration_match_str.replace('s', ''))
            print(f"    [Fallback] Simulated duration from filename ('{duration_match_str}'): {duration_seconds:.2f}s")
            return duration_seconds

        if os.path.exists(file_path_for_size):
            file_size_bytes = os.path.getsize(file_path_for_size)
            estimated_duration = (file_size_bytes / (0.5 * 1024 * 1024))
            duration_seconds = max(600.0, estimated_duration)
            print(f"    [Fallback] Simulated duration from file size ({file_size_bytes} bytes): {duration_seconds:.2f}s")
            return duration_seconds
        else:
            print(f"    [Fallback] Cannot access file for size-based simulation. Defaulting duration.")
            duration_seconds = 600.0
            return duration_seconds
    except Exception as e:
        print(f"    [Fallback] Error during simulation for {file_name}: {e}. Defaulting duration.")
        duration_seconds = 600.0
    return duration_seconds

def get_video_info(file_path):
    """
    Function to retrieve video information (size and actual duration using ffprobe).
    """
    file_name = os.path.basename(file_path)
    file_size = 0
    duration_seconds = 0.0

    if not os.path.exists(file_path):
        print(f"⚠️ File not found during info retrieval: {file_path}")
        return None

    try:
        file_size = os.path.getsize(file_path)
        ffprobe_path = shutil.which('ffprobe')

        if not ffprobe_path:
            duration_seconds = _simulate_duration_fallback(file_name, file_path)
        else:
            command = [
                ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                file_path
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=20)

                if result.returncode == 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        if 'format' in data and 'duration' in data['format']:
                            duration_seconds = float(data['format']['duration'])
                            if duration_seconds < 0:
                                print(f"    ffprobe returned negative duration for {file_name}. Using fallback.")
                                duration_seconds = _simulate_duration_fallback(file_name, file_path)
                        else:
                            print(f"    ffprobe output for {file_name} missing duration field. Using fallback.")
                            duration_seconds = _simulate_duration_fallback(file_name, file_path)
                    except json.JSONDecodeError:
                        print(f"    ffprobe output for {file_name} was not valid JSON. Using fallback.")
                        duration_seconds = _simulate_duration_fallback(file_name, file_path)
                    except ValueError:
                        print(f"    ffprobe returned non-numeric duration for {file_name}. Using fallback.")
                        duration_seconds = _simulate_duration_fallback(file_name, file_path)
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown ffprobe error."
                    duration_seconds = _simulate_duration_fallback(file_name, file_path)
            except subprocess.TimeoutExpired:
                print(f"    ffprobe timed out processing {file_name}. Using fallback.")
                duration_seconds = _simulate_duration_fallback(file_name, file_path)
            except Exception as e:
                print(f"    Unexpected error using ffprobe for {file_name}: {e}. Using fallback.")
                duration_seconds = _simulate_duration_fallback(file_name, file_path)
    except FileNotFoundError:
        print(f"⚠️ File not found (getsize or other access): {file_path}")
        return None
    except Exception as e:
        print(f"⚠️ General error getting info for {file_path}: {e}. Using fallback.")
        duration_seconds = _simulate_duration_fallback(file_name, file_path if 'file_path' in locals() else "")

    if duration_seconds == 0.0 and file_name and file_path:
        duration_seconds = _simulate_duration_fallback(file_name, file_path)

    return {
        "name": file_name,
        "path": file_path,
        "size_bytes": file_size,
        "formatted_size": format_bytes(file_size),
        "duration_min": round(duration_seconds / 60, 2),
        "formatted_duration": format_duration(duration_seconds),
        "raw_duration_sec": duration_seconds
    }
