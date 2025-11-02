#!/usr/bin/env python3
"""
Faster-Whisper-XXL Main Interface
User-friendly menu-driven interface for the transcription toolkit
"""

import os
import sys
import subprocess
from pathlib import Path
import yaml
import time

def load_config(config_name="default"):
    """Load configuration from config.yaml file"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"Error: Configuration file {config_path} not found!")
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f)

        if config_name not in configs:
            print(f"Error: Configuration '{config_name}' not found!")
            return None

        return configs[config_name]
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None

def get_available_configs():
    """Get list of available configurations"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        return ["default"]

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f)
        return list(configs.keys())
    except:
        return ["default"]

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    """Print the application logo with animation"""
    logo_lines = [
        " ███████╗ █████╗ ███████╗████████╗███████╗██████╗",
        " ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗",
        " █████╗  ███████║███████╗   ██║   █████╗  ██████╔╝",
        " ██╔══╝  ██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗",
        " ██║     ██║  ██║███████║   ██║   ███████╗██║  ██║",
        " ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
        "",
        " ████████╗██████╗  █████╗ ███╗   ██╗███████╗ ██████╗██████╗ ██╗██████╗ ████████╗",
        " ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝",
        "    ██║   ██████╔╝███████║██╔██╗ ██║███████╗██║     ██████╔╝██║██████╔╝   ██║   ",
        "    ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██║     ██╔══██╗██║██╔══██╗   ██║   ",
        "    ██║   ██║  ██║██║  ██║██║ ╚████║███████║╚██████╗██║  ██║██║██║  ██║   ██║   ",
        "    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝   ╚═╝   ",
        "",
        " ███╗   ███╗ █████╗ ██╗███╗   ██╗    ██╗███╗   ██╗████████╗███████╗██████╗ ███████╗ █████╗  ██████╗███████╗",
        " ████╗ ████║██╔══██╗██║████╗  ██║    ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝",
        " ██╔████╔██║███████║██║██╔██╗ ██║    ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝█████╗  ███████║██║     █████╗  ",
        " ██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║██║     ██╔══╝  ",
        " ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ██║██║ ╚████║   ██║   ███████╗██║  ██║██║     ██║  ██║╚██████╗███████╗",
        " ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝"
    ]

    # Animated logo display
    for i, line in enumerate(logo_lines):
        if i < 6:  # First logo part
            print(f"\033[36m{line}\033[0m")  # Cyan color
            time.sleep(0.05)
        elif i < 12:  # Second logo part
            print(f"\033[32m{line}\033[0m")  # Green color
            time.sleep(0.05)
        else:  # Third logo part
            print(f"\033[33m{line}\033[0m")  # Yellow color
            time.sleep(0.05)

    # Loading animation
    print("\n\033[35mInitializing Faster-Whisper-XXL Toolkit...\033[0m")
    loading_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(20):
        print(f"\r\033[35m{loading_chars[i % len(loading_chars)]} Loading configurations...\033[0m", end="", flush=True)
        time.sleep(0.1)
    print(f"\r\033[32m✓ Toolkit ready!\033[0m{' ' * 30}")

    print("\n" + "=" * 80)
    print("                    Welcome to Faster-Whisper-XXL")
    print("                   Professional Transcription Suite")
    print("=" * 80)
    print()

def print_header():
    """Print the application header"""
    print("=" * 60)
    print("        Faster-Whisper-XXL Transcription Toolkit")
    print("              Main Interface v1.0")
    print("=" * 60)
    print()

def print_menu():
    """Print the main menu"""
    print("Main Menu:")
    print("1. Extract Audio from Video")
    print("2. Transcribe Audio Files")
    print("3. Clean SRT Subtitle Files")
    print("4. Batch Process (Extract + Transcribe)")
    print("5. Settings & Configuration")
    print("6. Exit")
    print()

def extract_audio_menu():
    """Audio extraction menu"""
    while True:
        clear_screen()
        print_header()
        print("Audio Extraction Menu:")
        print("1. Extract from single video file")
        print("2. Extract from multiple video files")
        print("3. Extract from all videos in folder")
        print("4. Back to main menu")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            video_file = input("Enter video file path: ").strip()
            if video_file:
                cmd = [sys.executable, "extract_audio_optimized.py", video_file]
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd)
                input("\nPress Enter to continue...")
            else:
                input("Invalid input. Press Enter to continue...")

        elif choice == "2":
            files_input = input("Enter video file paths (separated by spaces): ").strip()
            if files_input:
                files = files_input.split()
                cmd = [sys.executable, "extract_audio_optimized.py"] + files
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd)
                input("\nPress Enter to continue...")
            else:
                input("Invalid input. Press Enter to continue...")

        elif choice == "3":
            folder = input("Enter folder path: ").strip()
            if folder and Path(folder).exists():
                # Find all video files in folder
                video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
                video_files = []
                for ext in video_extensions:
                    video_files.extend(Path(folder).glob(f"**/*{ext}"))

                if video_files:
                    file_paths = [str(f) for f in video_files]
                    cmd = [sys.executable, "extract_audio_optimized.py"] + file_paths
                    print(f"Found {len(video_files)} video files. Running extraction...")
                    subprocess.run(cmd)
                else:
                    print("No video files found in the specified folder.")
            else:
                print("Invalid folder path.")
            input("\nPress Enter to continue...")

        elif choice == "4":
            break
        else:
            input("Invalid option. Press Enter to continue...")

def transcribe_menu():
    """Transcription menu"""
    while True:
        clear_screen()
        print_header()

        # Get available configurations
        configs = get_available_configs()

        print("Available Configurations:")
        for i, config in enumerate(configs, 1):
            print(f"{i}. {config}")
        print(f"{len(configs) + 1}. Back to main menu")
        print()

        try:
            config_choice = int(input(f"Select configuration (1-{len(configs)}): ").strip())
            if 1 <= config_choice <= len(configs):
                selected_config = configs[config_choice - 1]

                while True:
                    clear_screen()
                    print_header()
                    print(f"Selected Configuration: {selected_config}")
                    print()
                    print("Transcription Options:")
                    print("1. Transcribe all WAV files in wav/ folder")
                    print("2. Transcribe files from specific folder")
                    print("3. Transcribe specific audio files")
                    print("4. Back to configuration selection")
                    print()

                    trans_choice = input("Select option (1-4): ").strip()

                    if trans_choice == "1":
                        cmd = [sys.executable, "transcribe_optimized.py", selected_config]
                        print(f"Running: {' '.join(cmd)}")
                        subprocess.run(cmd)
                        input("\nPress Enter to continue...")

                    elif trans_choice == "2":
                        folder = input("Enter audio folder path: ").strip()
                        if folder:
                            cmd = [sys.executable, "transcribe_optimized.py", selected_config, folder]
                            print(f"Running: {' '.join(cmd)}")
                            subprocess.run(cmd)
                            input("\nPress Enter to continue...")
                        else:
                            input("Invalid folder path. Press Enter to continue...")

                    elif trans_choice == "3":
                        files_input = input("Enter audio file paths (separated by spaces): ").strip()
                        if files_input:
                            files = files_input.split()
                            cmd = [sys.executable, "transcribe_optimized.py", selected_config] + files
                            print(f"Running: {' '.join(cmd)}")
                            subprocess.run(cmd)
                            input("\nPress Enter to continue...")
                        else:
                            input("Invalid input. Press Enter to continue...")

                    elif trans_choice == "4":
                        break
                    else:
                        input("Invalid option. Press Enter to continue...")

            elif config_choice == len(configs) + 1:
                break
            else:
                input("Invalid configuration selection. Press Enter to continue...")

        except ValueError:
            input("Invalid input. Press Enter to continue...")

def clean_srt_menu():
    """SRT cleaning menu"""
    while True:
        clear_screen()
        print_header()
        print("SRT Subtitle Cleaning Menu:")
        print("1. Clean single SRT file")
        print("2. Clean SRT file (keep duplicates for review)")
        print("3. Back to main menu")
        print()

        choice = input("Select option (1-3): ").strip()

        if choice == "1":
            input_file = input("Enter input SRT file path: ").strip()
            output_file = input("Enter output SRT file path: ").strip()
            if input_file and output_file:
                cmd = [sys.executable, "clean_srt.py", input_file, output_file]
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd)
                input("\nPress Enter to continue...")
            else:
                input("Invalid input. Press Enter to continue...")

        elif choice == "2":
            input_file = input("Enter input SRT file path: ").strip()
            output_file = input("Enter output SRT file path: ").strip()
            if input_file and output_file:
                cmd = [sys.executable, "clean_srt.py", input_file, output_file, "--keep-duplicates"]
                print(f"Running: {' '.join(cmd)}")
                subprocess.run(cmd)
                input("\nPress Enter to continue...")
            else:
                input("Invalid input. Press Enter to continue...")

        elif choice == "3":
            break
        else:
            input("Invalid option. Press Enter to continue...")

def batch_process_menu():
    """Batch processing menu (extract + transcribe)"""
    while True:
        clear_screen()
        print_header()

        # Get available configurations
        configs = get_available_configs()

        print("Batch Processing: Extract Audio + Transcribe")
        print("Available Configurations:")
        for i, config in enumerate(configs, 1):
            print(f"{i}. {config}")
        print(f"{len(configs) + 1}. Back to main menu")
        print()

        try:
            config_choice = int(input(f"Select configuration (1-{len(configs)}): ").strip())
            if 1 <= config_choice <= len(configs):
                selected_config = configs[config_choice - 1]

                while True:
                    clear_screen()
                    print_header()
                    print(f"Batch Processing with Configuration: {selected_config}")
                    print()
                    print("Options:")
                    print("1. Process single video file")
                    print("2. Process all videos in folder")
                    print("3. Back to configuration selection")
                    print()

                    batch_choice = input("Select option (1-3): ").strip()

                    if batch_choice == "1":
                        video_file = input("Enter video file path: ").strip()
                        if video_file and Path(video_file).exists():
                            # Extract audio
                            print("Step 1: Extracting audio...")
                            cmd1 = [sys.executable, "extract_audio_optimized.py", video_file]
                            subprocess.run(cmd1)

                            # Transcribe
                            print("Step 2: Transcribing audio...")
                            cmd2 = [sys.executable, "transcribe_optimized.py", selected_config]
                            subprocess.run(cmd2)

                            print("Batch processing completed!")
                        else:
                            print("Invalid video file path.")
                        input("\nPress Enter to continue...")

                    elif batch_choice == "2":
                        folder = input("Enter folder containing video files: ").strip()
                        if folder and Path(folder).exists():
                            # Find all video files
                            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
                            video_files = []
                            for ext in video_extensions:
                                video_files.extend(Path(folder).glob(f"**/*{ext}"))

                            if video_files:
                                print(f"Found {len(video_files)} video files.")
                                print("Step 1: Extracting audio from all videos...")
                                file_paths = [str(f) for f in video_files]
                                cmd1 = [sys.executable, "extract_audio_optimized.py"] + file_paths
                                subprocess.run(cmd1)

                                print("Step 2: Transcribing all extracted audio...")
                                cmd2 = [sys.executable, "transcribe_optimized.py", selected_config]
                                subprocess.run(cmd2)

                                print("Batch processing completed!")
                            else:
                                print("No video files found in the specified folder.")
                        else:
                            print("Invalid folder path.")
                        input("\nPress Enter to continue...")

                    elif batch_choice == "3":
                        break
                    else:
                        input("Invalid option. Press Enter to continue...")

            elif config_choice == len(configs) + 1:
                break
            else:
                input("Invalid configuration selection. Press Enter to continue...")

        except ValueError:
            input("Invalid input. Press Enter to continue...")

def settings_menu():
    """Settings and configuration menu"""
    while True:
        clear_screen()
        print_header()
        print("Settings & Configuration:")
        print("1. View available configurations")
        print("2. View current configuration details")
        print("3. Edit config.yaml file")
        print("4. Back to main menu")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            configs = get_available_configs()
            print("Available Configurations:")
            for config in configs:
                print(f"  - {config}")
            print()
            input("Press Enter to continue...")

        elif choice == "2":
            configs = get_available_configs()
            print("Select configuration to view:")
            for i, config in enumerate(configs, 1):
                print(f"{i}. {config}")
            print()

            try:
                config_choice = int(input(f"Select configuration (1-{len(configs)}): ").strip())
                if 1 <= config_choice <= len(configs):
                    selected_config = configs[config_choice - 1]
                    config_data = load_config(selected_config)
                    if config_data:
                        print(f"\nConfiguration: {selected_config}")
                        print("-" * 40)
                        for key, value in config_data.items():
                            if isinstance(value, dict):
                                print(f"{key}:")
                                for sub_key, sub_value in value.items():
                                    print(f"  {sub_key}: {sub_value}")
                            else:
                                print(f"{key}: {value}")
                    else:
                        print("Failed to load configuration.")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input.")

            print()
            input("Press Enter to continue...")

        elif choice == "3":
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                print(f"Opening {config_path} in default editor...")
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(str(config_path))
                    else:  # Linux/Mac
                        subprocess.run(['xdg-open', str(config_path)])
                except:
                    print(f"Please manually open: {config_path}")
            else:
                print("Configuration file not found.")
            input("\nPress Enter to continue...")

        elif choice == "4":
            break
        else:
            input("Invalid option. Press Enter to continue...")

def main():
    """Main application loop"""
    # Show logo only on first run
    clear_screen()
    print_logo()

    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input("Select option (1-6): ").strip()

        if choice == "1":
            extract_audio_menu()
        elif choice == "2":
            transcribe_menu()
        elif choice == "3":
            clean_srt_menu()
        elif choice == "4":
            batch_process_menu()
        elif choice == "5":
            settings_menu()
        elif choice == "6":
            print("\n\033[32mThank you for using Faster-Whisper-XXL Toolkit!\033[0m")
            print("\033[36mHave a great day! 👋\033[0m")
            break
        else:
            print("\033[31mInvalid option. Please select 1-6.\033[0m")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
