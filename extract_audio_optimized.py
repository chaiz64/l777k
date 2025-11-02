#!/usr/bin/env python3
"""
Optimized FFmpeg audio extraction script for WAV format
Settings optimized for Whisper transcription:
- 16kHz sample rate (Whisper's native rate)
- 16-bit PCM
- Mono channel
- High quality extraction for speech transcription
"""

import subprocess
import sys
import os
from pathlib import Path

def collect_video_files(input_paths):
    """Collect all video files from provided paths (files or folders)"""
    video_files = []
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts'}

    if not input_paths:
        # No arguments provided, use current directory for video files
        current_dir = Path.cwd()
        video_files = [f for f in current_dir.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]
        return [str(f) for f in video_files]

    for path_str in input_paths:
        path = Path(path_str)
        if not path.exists():
            print(f"Warning: Path '{path}' not found, skipping...")
            continue

        if path.is_dir():
            # It's a folder, get all video files recursively
            for ext in video_extensions:
                video_files.extend(path.rglob(f"*{ext}"))
        elif path.is_file() and path.suffix.lower() in video_extensions:
            # It's a video file
            video_files.append(path)

    return [str(f) for f in video_files]

def extract_audio_to_wav(video_file):
    """Extract audio from video file to optimized WAV format"""
    video_path = Path(video_file)
    script_dir = Path(__file__).parent
    wav_dir = script_dir / "wav"
    wav_dir.mkdir(exist_ok=True)
    output_path = wav_dir / f"{video_path.stem}.wav"

    if not video_path.exists():
        print(f"Error: Video file '{video_path}' not found!")
        return False

    print(f"Extracting audio from: {video_path}")
    print(f"Output: {output_path}")
    print("Settings: 16kHz, 16-bit PCM, Mono")
    print()

    # FFmpeg command for optimized WAV extraction
    cmd = [
        "ffmpeg.exe",
        "-i", str(video_path),
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # 16-bit PCM
        "-ar", "16000",           # 16kHz sample rate
        "-ac", "1",               # Mono channel
        "-y",                     # Overwrite output
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if result.returncode == 0:
            print(f"Successfully extracted audio to: {output_path}")
            return True
        else:
            print(f"Error extracting audio from: {video_path}")
            print(f"FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error running FFmpeg: {e}")
        return False

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    ffmpeg_path = script_dir / "ffmpeg.exe"

    if not ffmpeg_path.exists():
        print(f"Error: {ffmpeg_path} not found!")
        sys.exit(1)

    # Collect video files from command line arguments or current directory
    input_paths = sys.argv[1:] if len(sys.argv) > 1 else []
    video_files = collect_video_files(input_paths)

    if not video_files:
        print("No video files found to process!")
        print("\nUsage: python extract_audio_optimized.py [folder_path] [video_file1] [video_file2] ...")
        print("\nSupported video formats: .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm, .m4v, .3gp, .ts")
        print("\nIf no arguments provided, will automatically process all video files in current directory.")
        print("\nOptimized FFmpeg settings for WAV extraction:")
        print("- 16kHz sample rate (Whisper's native rate)")
        print("- 16-bit PCM")
        print("- Mono channel")
        print("- High quality extraction for speech transcription")
        sys.exit(1)

    success_count = 0

    print(f"Processing {len(video_files)} video file(s)...")
    print()

    for video_file in video_files:
        if extract_audio_to_wav(video_file):
            success_count += 1
        print()

    print(f"Audio extraction completed! {success_count}/{len(video_files)} files processed successfully.")

if __name__ == "__main__":
    main()
