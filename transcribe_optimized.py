#!/usr/bin/env python3
"""
Optimized Faster-Whisper-XXL transcription script for i9-9000K CPU, RTX 2080 GPU, 32GB RAM

Settings optimized for:
- Large model for better quality
- CUDA GPU acceleration with RTX 2080
- Float16 precision for optimal GPU performance
- 12 CPU threads for i9-9000K utilization
- Batched inference for 2x-4x speed increase
- Batch size 16 for optimal GPU utilization
"""

import subprocess
import sys
import os
from pathlib import Path
import yaml

def load_config(config_name="default"):
    """Load configuration from config.yaml file"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"Error: Configuration file {config_path} not found!")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f)

        if config_name not in configs:
            print(f"Error: Configuration '{config_name}' not found in config.yaml!")
            print(f"Available configurations: {list(configs.keys())}")
            sys.exit(1)

        return configs[config_name]
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def collect_audio_files(input_paths):
    """Collect all WAV files from provided paths (files or folders)"""
    audio_files = []

    if not input_paths:
        # No arguments provided, use default wav folder
        wav_folder = Path("wav")
        if wav_folder.exists():
            audio_files = list(wav_folder.glob("*.wav"))
        return [str(f) for f in audio_files]

    for path_str in input_paths:
        path = Path(path_str)
        if not path.exists():
            continue

        if path.is_dir():
            # It's a folder, get all WAV files recursively
            audio_files.extend(path.rglob("*.wav"))
        elif path.is_file() and path.suffix.lower() == '.wav':
            # It's a WAV file
            audio_files.append(path)

    return [str(f) for f in audio_files]

def main(config_name="default"):
    # Load configuration from YAML file
    config = load_config(config_name)

    # Language configuration for display
    language_options = {
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "vn": "Vietnamese",
        "th": "Thai"
    }
    language_name = language_options.get(config.get("language", "en"), "Unknown")

    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    exe_path = script_dir / "faster-whisper-xxl.exe"

    if not exe_path.exists():
        print(f"Error: {exe_path} not found!")
        sys.exit(1)

    # Collect audio files from command line arguments or default folder
    input_paths = sys.argv[1:] if len(sys.argv) > 1 else []
    audio_files = collect_audio_files(input_paths)

    if not audio_files:
        print("No WAV files found to process!")
        print("\nUsage: python transcribe_optimized.py [config_name] [folder_path] [audio_file1] [audio_file2] ...")
        print("\nAvailable configs: default, english_1920s_drama")
        print("If no config specified, uses 'default'")
        print("If no arguments provided, will automatically process all WAV files in the 'wav' folder.")
        print("\nOptimized settings for i9-9000K CPU, RTX 2080 GPU, 32GB RAM:")
        print("- Large model for better quality")
        print("- CUDA GPU acceleration")
        print("- Float16 precision for RTX 2080")
        print("- 12 CPU threads for i9-9000K")
        print("- Batched inference for 2x-4x speed increase")
        print("- Batch size 16 for optimal GPU utilization")
        sys.exit(1)

    print(f"Starting optimized transcription with config: {config_name}")
    print(f"Model: {config.get('model', 'large-v2')}")
    print(f"Language: {language_name}")
    print(f"Device: {config.get('device', 'cuda').upper()}")
    print(f"Compute type: {config.get('compute_type', 'float16')}")
    print(f"Threads: {config.get('threads', 12)}")
    print(f"Batched inference: {'enabled' if config.get('batched', True) else 'disabled'}")
    print(f"Batch size: {config.get('batch_size', 8)}")
    print(f"Beam size: {config.get('beam_size', 1)}")
    temperature = config.get('temperature', 0.2)
    if isinstance(temperature, list):
        print(f"Temperature: {temperature} (using first value: {temperature[0]})")
        temperature = temperature[0]  # Use first value for faster-whisper-xxl.exe
    else:
        print(f"Temperature: {temperature}")
    if 'best_of' in config:
        print(f"Best of: {config.get('best_of', 5)}")
    print(f"Compression ratio threshold: {config.get('compression_ratio_threshold', 2.0)}")
    print(f"VAD filter: {'enabled' if config.get('vad_filter', True) else 'disabled'}")
    if 'vad_speech_pad_ms' in config:
        print(f"VAD speech padding: {config.get('vad_speech_pad_ms', 250)}ms")
    if 'vad_method' in config:
        print(f"VAD method: {config.get('vad_method', 'silero_v3')}")
    if 'chunk_length' in config:
        print(f"Chunk length: {config.get('chunk_length', 20)} seconds")
    print(f"No speech threshold: {config.get('no_speech_threshold', 0.5)}")
    if 'task' in config:
        print(f"Task: {config.get('task', 'transcribe')}")
    if config.get('standard', False):
        print("Standard: enabled")
    if config.get('standard_asia', False):
        print("Standard Asia: enabled")
    if config.get('sentence', False):
        print("Sentence splitting: enabled")
    print(f"Processing {len(audio_files)} file(s)...")
    print()

    # Build the command dynamically from config
    cmd = [str(exe_path)]

    # Define which parameters are flags (don't take values) vs parameters that take values
    flag_parameters = {
        'batched', 'standard', 'standard_asia', 'sentence', 'batch_recursive',
        'check_files', 'print_progress', 'beep_off'
    }

    # Add all config parameters as command line arguments
    for key, value in config.items():
        if key == 'output_format' and isinstance(value, list):
            # Handle output_format as multiple arguments
            cmd.extend([f"--{key}", *value])
        elif key in flag_parameters:
            # These are flag parameters - only add if True
            if value:
                cmd.append(f"--{key}")
        elif isinstance(value, dict):
            # Handle nested dictionaries (like vad_parameters)
            # Flatten them to individual parameters (e.g., vad_parameters_threshold -> --vad_threshold)
            for sub_key, sub_value in value.items():
                param_name = f"--{key.replace('_parameters', '')}_{sub_key}"
                if isinstance(sub_value, bool):
                    if sub_value:
                        cmd.append(param_name)
                else:
                    cmd.append(param_name)
                    cmd.append(str(sub_value))
        elif key == 'temperature' and isinstance(value, list):
            # Handle temperature arrays - use first value
            cmd.extend([f"--{key}", str(value[0])])
        else:
            # For parameters that take values, add both key and value
            cmd.extend([f"--{key}", str(value)])

    # Add audio files
    cmd.extend(audio_files)

    try:
        # Run the command
        result = subprocess.run(cmd, cwd=script_dir)

        if result.returncode == 0:
            print("\nTranscription completed successfully!")
        else:
            print(f"\nTranscription failed with return code: {result.returncode}")
            sys.exit(result.returncode)

    except KeyboardInterrupt:
        print("\nTranscription interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during transcription: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if config name is provided as first argument
    if len(sys.argv) > 1 and not sys.argv[1].endswith('.wav') and not Path(sys.argv[1]).exists():
        # First argument is config name
        config_name = sys.argv[1]
        # Remove config name from sys.argv for collect_audio_files
        sys.argv.pop(1)
    else:
        config_name = "default"

    main(config_name)
