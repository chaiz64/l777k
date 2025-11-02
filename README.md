# Faster-Whisper-XXL Transcription Toolkit

## Overview
A comprehensive toolkit for audio/video transcription optimized for Japanese content using Faster-Whisper-XXL. Designed for i9-9000K CPU and RTX 2080 GPU with 32GB RAM.

## Features
- **High-Quality Transcription**: Uses large-v2 model for superior Japanese language recognition
- **GPU Acceleration**: CUDA-optimized for RTX 2080 GPU performance
- **Batch Processing**: Process multiple files simultaneously
- **Automated Workflow**: Extract audio from video, transcribe, and organize outputs
- **Flexible Input**: Support for individual files or entire folders
- **Multiple Output Formats**: SRT, JSON, and TEXT formats
- **Speaker Detection**: Configurable speaker diarization (2-4 speakers)
- **Clean SRT Processing**: Remove duplicates and renumber subtitles

## File Structure
```
├── faster-whisper-xxl.exe          # Main transcription executable
├── ffmpeg.exe                      # Audio extraction tool
├── Faster-Whisper-XXL-GUI.exe      # Standalone GUI application (no Python required)
├── config.yaml                     # Configuration file for different settings
├── main.py                         # Python GUI interface source code
├── transcribe_optimized.ps1        # PowerShell transcription script
├── transcribe_optimized.bat        # Batch transcription script
├── transcribe_optimized.py         # Python transcription script
├── transcribe_optimized_diarize.py # Python transcription with speaker diarization
├── extract_audio_optimized.ps1     # PowerShell audio extraction
├── extract_audio_optimized.bat     # Batch audio extraction
├── extract_audio_optimized.py      # Python audio extraction
├── clean_srt.py                    # SRT cleaning and deduplication
├── wav/                            # Audio files directory
├── sub/                            # Subtitle outputs directory
└── README.md                       # This documentation
```

## Quick Start

### Option 1: Standalone Executable (Easiest - No Python Required)
```bash
Faster-Whisper-XXL-GUI.exe
```
Double-click this executable to launch the full interface. **No Python installation needed!** Includes all features:
- **Animated Logo**: Beautiful ASCII art logo with color animation on startup
- **Loading Animation**: Smooth loading spinner while initializing
- **Color-Coded Menus**: Different colors for different interface elements
- **Intuitive Navigation**: Easy-to-use numbered menus for all functions
- **Fixed Menu Navigation**: Submenus stay open until you choose to go back

### Option 2: Python Interface
```bash
python main.py
```
Same interactive menu as the executable, but requires Python to be installed.

### Option 2: Command Line Usage

#### 1. Extract Audio from Video
```bash
# PowerShell
.\extract_audio_optimized.ps1 "video.mp4"

# Batch
extract_audio_optimized.bat "video.mp4"

# Python
python extract_audio_optimized.py "video.mp4"
```

#### 2. Transcribe Audio
```bash
# Process all WAV files in wav/ folder (default)
python transcribe_optimized.py

# Process specific folder
python transcribe_optimized.py "path/to/audio/folder"

# Process individual files
python transcribe_optimized.py audio1.wav audio2.wav
```

#### 3. Clean SRT Files
```bash
python clean_srt.py input.srt output_clean.srt
```

## Configuration System

The toolkit uses a YAML-based configuration system (`config.yaml`) that allows you to easily switch between different parameter sets optimized for various transcription scenarios.

### Available Configurations

#### Default Configuration (`default`)
- Optimized for general Asian language transcription
- Uses large-v2 model with standard settings
- Best for: Japanese, Chinese, Korean content

#### English 1880s Drama Configuration (`english_1880s_drama`)
- Optimized for historical English dialogue with speaker diarization
- Uses large-v3 model with moderate settings and reverb_v2 speaker detection
- Includes custom prompt for period-appropriate transcription
- Best for: Classic films, period dramas with multiple speakers

#### English 1920s Drama Configuration (`english_1920s_drama`)
- Optimized for historical English dialogue
- Uses large-v3 model with enhanced settings
- Includes custom prompt for period-appropriate transcription
- Best for: Classic films, period dramas, historical content

#### Japanese Drama Series Configuration (`japanese_drama`)
- Optimized for Japanese drama series dialogue
- Uses large-v3 model with enhanced settings
- Includes custom prompt for emotional nuance and character-driven tone
- Best for: Japanese TV dramas, anime series, character-focused content

#### Japanese Adult Films Configuration (`japanese_adult`)
- Optimized for soft-spoken Japanese dialogue from adult films
- Uses large-v3 model with enhanced settings
- Includes custom prompt for emotional nuance, natural rhythm, and gentle tone
- Best for: Adult films, intimate conversations, soft-spoken content

#### Chinese Drama Series Configuration (`chinese_drama`)
- Optimized for Chinese drama series dialogue
- Uses large-v3 model with enhanced settings
- Includes custom prompt for emotional depth, cultural nuance, and natural pacing
- Best for: Chinese TV dramas, films, culturally rich content

#### English Drama Series Configuration (`english_drama`)
- Optimized for modern English drama series dialogue
- Uses large-v3 model with enhanced settings
- Includes custom prompt for emotional nuance, natural pacing, and character-driven tone
- Best for: Modern TV dramas, films, character-focused English content

#### Japanese Anime Series Configuration (`japanese_anime`)
- Optimized for Japanese anime series dialogue
- Uses large-v3 model with enhanced settings
- Includes custom prompt for expressive emotion, varied pacing, and character-driven tone
- Best for: Anime series, animated content, expressive Japanese dialogue

#### Japanese Light Novels Configuration (`japanese_light_novel`)
- Optimized for Japanese light novel adaptations
- Uses large-v3 model with enhanced settings
- Includes custom prompt for poetic rhythm, emotional depth, and introspective tone
- Best for: Light novel adaptations, introspective Japanese dialogue

### Using Different Configurations

#### Python Scripts
```bash
# Use default configuration
python transcribe_optimized.py

# Use English 1920s drama configuration
python transcribe_optimized.py english_1920s_drama

# Use Japanese drama series configuration
python transcribe_optimized.py japanese_drama

# Use with specific files
python transcribe_optimized.py japanese_drama audio1.wav audio2.wav
```

#### Configuration File Structure
```yaml
# Example configuration entry
config_name:
  model: "large-v3"
  language: "en"
  device: "cuda"
  beam_size: 10
  best_of: 5
  temperature: 0.0
  initial_prompt: "Custom prompt for specific content type"
  # ... other parameters
```

### Adding Custom Configurations

1. Open `config.yaml` in a text editor
2. Add a new configuration section following the existing format
3. Save the file
4. Use the new configuration name with the scripts

Example custom configuration for modern English content:
```yaml
modern_english:
  model: "large-v3"
  language: "en"
  device: "cuda"
  compute_type: "float16"
  beam_size: 5
  temperature: 0.0
  compression_ratio_threshold: 2.0
  initial_prompt: "Transcribe modern English dialogue with contemporary tone"
```

## Detailed Usage

### Audio Extraction Scripts

#### PowerShell (`extract_audio_optimized.ps1`)
```powershell
# Extract from single video
.\extract_audio_optimized.ps1 "movie.mp4"

# Extract from multiple videos
.\extract_audio_optimized.ps1 "video1.mp4" "video2.mp4"

# Drag and drop videos onto the script
```

#### Batch (`extract_audio_optimized.bat`)
```batch
# Extract from single video
extract_audio_optimized.bat "movie.mp4"

# Extract from multiple videos
extract_audio_optimized.bat "video1.mp4" "video2.mp4"

# Drag and drop videos onto the batch file
```

#### Python (`extract_audio_optimized.py`)
```bash
# Extract from single video
python extract_audio_optimized.py "movie.mp4"

# Extract from multiple videos
python extract_audio_optimized.py "video1.mp4" "video2.mp4"
```

**Audio Output Settings:**
- Format: WAV (16-bit PCM)
- Sample Rate: 16kHz (Whisper native)
- Channels: Mono
- Codec: PCM signed 16-bit little-endian

### Transcription Scripts

#### PowerShell (`transcribe_optimized.ps1`)
```powershell
# Process all WAV files in wav/ folder
.\transcribe_optimized.ps1

# Process specific folder
.\transcribe_optimized.ps1 "C:\path\to\audio"

# Process individual files
.\transcribe_optimized.ps1 "audio1.wav" "audio2.wav"
```

#### Batch (`transcribe_optimized.bat`)
```batch
# Process all WAV files in wav/ folder
transcribe_optimized.bat

# Process specific folder
transcribe_optimized.bat "C:\path\to\audio"

# Process individual files
transcribe_optimized.bat "audio1.wav" "audio2.wav"
```

#### Python (`transcribe_optimized.py`)
```bash
# Process all WAV files in wav/ folder
python transcribe_optimized.py

# Process specific folder
python transcribe_optimized.py "path/to/audio/folder"

# Process individual files
python transcribe_optimized.py audio1.wav audio2.wav
```

#### Python with Speaker Diarization (`transcribe_optimized_diarize.py`)
```bash
# Process all WAV files in wav/ folder with speaker detection
python transcribe_optimized_diarize.py

# Process specific folder with speaker diarization
python transcribe_optimized_diarize.py "path/to/audio/folder"

# Process individual files with speaker labels
python transcribe_optimized_diarize.py audio1.wav audio2.wav
```

**Diarization Features:**
- Speaker identification and labeling
- 2-4 speakers detection range
- reverb_v2 diarization model
- Speaker-separated subtitle output

### SRT Cleaning Script

#### Python (`clean_srt.py`)
```bash
# Clean single SRT file
python clean_srt.py input.srt output_clean.srt

# Remove duplicates but keep them (show what would be removed)
python clean_srt.py input.srt output_clean.srt --keep-duplicates
```

**Cleaning Features:**
- Remove duplicate subtitle text
- Renumber subtitles sequentially
- Preserve timing information
- Handle multi-line subtitles

## Configuration Parameters

### Model Settings
- **Model**: `large-v2` - High-quality Japanese transcription
- **Language**: `ja` - Japanese language detection
- **Task**: `transcribe` - Speech-to-text transcription

### Hardware Optimization
- **Device**: `cuda` - RTX 2080 GPU acceleration
- **Compute Type**: `float16` - 16-bit floating point precision
- **Threads**: `12` - Optimized for i9-9000K CPU cores

### Processing Settings
- **Batch Size**: `8` - GPU memory optimized
- **Beam Size**: `1` - Focused decoding
- **Temperature**: `0.2` - Slight randomness for natural output

### Audio Processing
- **VAD Filter**: `True` - Voice activity detection enabled
- **VAD Method**: `silero_v3` - Advanced voice detection
- **Chunk Length**: `20` - 20-second audio chunks
- **Compression Ratio Threshold**: `2.0` - Audio quality filtering

### Speaker Detection
- **Min Speakers**: `2` - Minimum speakers to detect
- **Max Speakers**: `4` - Maximum speakers to detect

### Output Settings
- **Output Directory**: `sub/` - Subtitle output folder
- **Output Formats**: `srt`, `json`, `text` - Multiple format support
- **Standard Asia**: `enabled` - Asian language optimizations
- **Sentence Splitting**: `enabled` - Natural sentence breaks

## Output Organization

### Directory Structure
```
project/
├── wav/                    # Audio files
│   ├── video1.wav
│   ├── video2.wav
│   └── ...
├── sub/                    # Subtitle outputs
│   ├── video1.srt
│   ├── video1.json
│   ├── video1.text
│   ├── video2.srt
│   └── ...
└── scripts/               # Transcription scripts
```

### File Naming
- Audio files: `{original_filename}.wav`
- Subtitles: `{original_filename}.srt/json/text`

## Performance Optimization

### Hardware Requirements
- **CPU**: Intel i9-9000K or equivalent (12+ threads recommended)
- **GPU**: NVIDIA RTX 2080 or better (8GB+ VRAM)
- **RAM**: 32GB+ system memory
- **Storage**: SSD recommended for faster I/O

### Performance Tips
1. **Batch Processing**: Process multiple files together for efficiency
2. **GPU Memory**: Monitor GPU usage and adjust batch_size if needed
3. **File Organization**: Keep audio files in dedicated folders
4. **Regular Cleanup**: Use clean_srt.py to remove duplicates

### Troubleshooting

#### Common Issues
- **CUDA Errors**: Ensure NVIDIA drivers are up to date
- **Memory Issues**: Reduce batch_size or chunk_length
- **Audio Quality**: Check input audio format and quality
- **File Paths**: Use absolute paths for network drives

#### Error Codes
- `1`: No input files found
- `2`: Invalid command arguments
- `3`: FFmpeg/audio processing error
- `4`: CUDA/GPU error

## Advanced Usage

### Custom Parameters
You can modify the scripts to adjust parameters:

```python
# In transcribe_optimized.py, modify these values:
"--batch_size", "4",        # Reduce for lower VRAM
"--beam_size", "3",         # Faster processing
"--chunk_length", "15",     # Shorter chunks
```

### Integration with Other Tools
The scripts can be integrated into larger workflows:

```bash
# Example workflow
extract_audio.bat "input.mp4"
transcribe.py
clean_srt.py "sub/output.srt" "sub/clean_output.srt"
```

### Batch Processing Large Collections
```bash
# Process entire directory tree
python transcribe_optimized.py "D:\Videos\Japanese\Season1"
```

## Support and Updates

### Version History
- **v1.0**: Initial release with basic transcription
- **v1.1**: Added speaker diarization and SRT cleaning
- **v1.2**: Improved batch processing and folder handling

### Dependencies
- **faster-whisper-xxl.exe**: Main transcription engine
- **ffmpeg.exe**: Audio/video processing
- **Python 3.8+**: For Python scripts (optional)
- **PowerShell 5.1+**: For PowerShell scripts
- **CUDA 11.8+**: For GPU acceleration

### License
This toolkit is provided as-is for personal and educational use.

---

**Note**: Parameters are optimized for Japanese content transcription. Adjust settings based on your specific use case and hardware capabilities.
