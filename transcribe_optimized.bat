@echo off
color 0A
echo.
echo.
echo      8""""                                    8   8  8                                       8   8 8   8 8
echo      8     eeeee eeeee eeeee eeee eeeee       8   8  8 e   e e  eeeee eeeee eeee eeeee        8 8   8 8  8
echo      8eeee 8   8 8   "   8   8    8   8       8e  8  8 8   8 8  8   " 8   8 8    8   8        eee   eee  8e
echo      88    8eee8 8eeee   8e  8eee 8eee8e eeee 88  8  8 8eee8 8e 8eeee 8eee8 8eee 8eee8e eeee 88  8 88  8 88
echo      88    88  8    88   88  88   88   8      88  8  8 88  8 88    88 88    88   88   8      88  8 88  8 88
echo      88    88  8 8ee88   88  88ee 88   8      88ee8ee8 88  8 88 8ee88 88    88ee 88   8      88  8 88  8 88eee
echo.
echo.

:: Language configuration - supported languages: en (English), zh (Chinese), ja (Japanese), ko (Korean), vn (Vietnamese), th (Thai)
:: To change language, update both the echo statement below and the --language parameter in the command
set "LANGUAGE_CODE=zh"
set "LANGUAGE_NAME=Chinese"

:: Enable delayed variable expansion
setlocal enabledelayedexpansion

:: Initialize file list
set "file_list="

:: Check if files/folders were provided
if "%~1"=="" (
    :: No arguments provided, use default wav folder
    if exist "wav" (
        for %%F in (wav\*.wav) do (
            set "file_list=!file_list! "%%~fF""
        )
    )
) else (
    :: Process provided arguments
    for %%F in (%*) do (
        if exist "%%~fF" (
            if exist "%%~fF\*" (
                :: It's a folder, get all WAV files recursively
                for /r "%%~fF" %%G in (*.wav) do (
                    set "file_list=!file_list! "%%~fG""
                )
            ) else (
                :: It's a file, check if it's WAV
                if /i "%%~xF"==".wav" (
                    set "file_list=!file_list! "%%~fF""
                )
            )
        )
    )
)

:: Check if we have any files to process
if "!file_list!"=="" (
    echo No WAV files found to process!
    echo.
    echo Usage: transcribe_optimized.bat [folder_path] or drag and drop WAV files/folders
    echo.
    echo If no arguments provided, will automatically process all WAV files in the 'wav' folder.
    echo.
    echo Optimized settings for i9-9000K CPU, RTX 2080 GPU, 32GB RAM:
    echo - Large model for better quality
    echo - CUDA GPU acceleration
    echo - Float16 precision for RTX 2080
    echo - 12 CPU threads for i9-9000K
    echo - Batched inference for 2x-4x speed increase
    echo - Batch size 16 for optimal GPU utilization
    echo.
    pause
    color
    exit /b
)

echo Starting optimized transcription with settings:
echo Model: large-v2
echo Language: %LANGUAGE_NAME%
echo Device: CUDA (RTX 2080)
echo Compute type: float16
echo Threads: 12
echo Batched inference: enabled
echo Batch size: 8
echo Beam size: 5
echo Temperature: 0.0
echo Best of: 5
echo Compression ratio threshold: 2.0
echo VAD filter: enabled
echo VAD speech padding: 250ms
echo VAD method: silero_v3
echo Chunk length: 20 seconds
echo No speech threshold: 0.5
echo Task: transcribe
echo Standard Asia: enabled
echo Sentence splitting: enabled
echo.

:: The optimized command for i9-9000K, RTX 2080, 32GB RAM
faster-whisper-xxl.exe --model large-v2 --language %LANGUAGE_CODE% --task transcribe --device cuda --compute_type float16 --threads 12 --batched --batch_size 8 --beam_size 5 --temperature 0.0 --best_of 5 --compression_ratio_threshold 2.0 --vad_filter True --vad_speech_pad_ms 250 --vad_method silero_v3 --chunk_length 20 --no_speech_threshold 0.5 --standard_asia --sentence --min_speakers 2 --max_speakers 4 --output_dir sub --output_format srt json text --batch_recursive --check_files --print_progress --beep_off %file_list%

echo.
echo Transcription completed!
echo.

pause
color
exit /b
