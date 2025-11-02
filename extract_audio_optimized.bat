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

:: Enable delayed variable expansion
setlocal enabledelayedexpansion

:: Check if arguments were provided
if "%~1"=="" (
    echo No arguments provided. Processing all video files in current directory...
    echo.
    goto :process_current_dir
)

:: Create wav directory if it doesn't exist
if not exist "wav" mkdir "wav"

:: Process each argument (could be files or folders)
set "total_processed=0"
for %%A in (%*) do (
    if exist "%%~A\" (
        echo Processing folder: %%~A
        call :process_folder "%%~A"
    ) else if exist "%%~A" (
        call :process_file "%%~A"
    ) else (
        echo Warning: %%~A not found, skipping...
    )
)
goto :done

:process_current_dir
:: Create wav directory if it doesn't exist
if not exist "wav" mkdir "wav"

:: Process all video files in current directory
set "total_processed=0"
for %%F in (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts) do (
    call :process_file "%%F"
)
goto :done

:process_folder
setlocal
set "folder_path=%~1"
echo Processing folder: %folder_path%
for /r "%folder_path%" %%F in (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts) do (
    call :process_file "%%F"
)
endlocal
goto :eof

:process_file
set "input_file=%~1"
set "output_file=wav\%~n1.wav"

echo Extracting audio from: !input_file!
echo Output: !output_file!
echo Settings: 16kHz, 16-bit PCM, Mono
echo.

:: FFmpeg command for optimized WAV extraction
ffmpeg.exe -i "!input_file!" -vn -acodec pcm_s16le -ar 16000 -ac 1 -y "!output_file!"

if !errorlevel! equ 0 (
    echo Successfully extracted audio to: !output_file!
    set /a total_processed+=1
) else (
    echo Error extracting audio from: !input_file!
)
echo.
goto :eof

:done

echo Audio extraction completed!
echo.

pause
color
exit /b
