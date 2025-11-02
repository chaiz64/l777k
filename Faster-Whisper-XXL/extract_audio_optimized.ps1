# Optimized FFmpeg settings for audio extraction to WAV format
# - 16kHz sample rate (Whisper's native rate)
# - 16-bit PCM
# - Mono channel
# - High quality extraction for speech transcription

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$InputPaths
)

$ffmpegPath = ".\ffmpeg.exe"

# Video file extensions to process
$videoExtensions = @('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts')

function Get-VideoFiles {
    param([string[]]$paths)

    $videoFiles = @()

    if ($paths.Count -eq 0) {
        # No arguments provided, use current directory
        Write-Host "No arguments provided. Processing all video files in current directory..." -ForegroundColor Yellow
        $currentDir = Get-Location
        foreach ($ext in $videoExtensions) {
            $files = Get-ChildItem -Path $currentDir -Filter "*$ext" -File
            $videoFiles += $files.FullName
        }
        return $videoFiles
    }

    foreach ($path in $paths) {
        if (!(Test-Path $path)) {
            Write-Host "Warning: Path '$path' not found, skipping..." -ForegroundColor Yellow
            continue
        }

        $item = Get-Item $path
        if ($item.PSIsContainer) {
            # It's a folder, get all video files recursively
            Write-Host "Processing folder: $path" -ForegroundColor Cyan
            foreach ($ext in $videoExtensions) {
                $files = Get-ChildItem -Path $path -Filter "*$ext" -File -Recurse
                $videoFiles += $files.FullName
            }
        } elseif ($item.Extension -in $videoExtensions) {
            # It's a video file
            $videoFiles += $item.FullName
        }
    }

    return $videoFiles
}

# Get all video files to process
$videoFiles = Get-VideoFiles -paths $InputPaths

if ($videoFiles.Count -eq 0) {
    Write-Host "No video files found to process!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage: .\extract_audio_optimized.ps1 [folder_path] [video_file1] [video_file2] ..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Supported video formats: .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm, .m4v, .3gp, .ts" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "If no arguments provided, will automatically process all video files in current directory." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Optimized FFmpeg settings for WAV extraction:" -ForegroundColor Green
    Write-Host "- 16kHz sample rate (Whisper's native rate)" -ForegroundColor Green
    Write-Host "- 16-bit PCM" -ForegroundColor Green
    Write-Host "- Mono channel" -ForegroundColor Green
    Write-Host "- High quality extraction for speech transcription" -ForegroundColor Green
    exit 1
}

Write-Host "Processing $($videoFiles.Count) video file(s)..." -ForegroundColor Green
Write-Host ""

foreach ($videoFile in $videoFiles) {
    $videoPath = [System.IO.Path]::GetFullPath($videoFile)
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($videoPath)
    $outputDir = Join-Path (Get-Location) "wav"
    if (!(Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }
    $outputPath = Join-Path $outputDir "$fileName.wav"

    if (!(Test-Path $videoPath)) {
        Write-Host "Error: Video file '$videoPath' not found!" -ForegroundColor Red
        continue
    }

    Write-Host "Extracting audio from: $videoPath" -ForegroundColor Green
    Write-Host "Output: $outputPath" -ForegroundColor Yellow
    Write-Host "Settings: 16kHz, 16-bit PCM, Mono" -ForegroundColor Cyan
    Write-Host ""

    # FFmpeg command for optimized WAV extraction
    $arguments = @(
        "-i", $videoPath,
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # 16-bit PCM
        "-ar", "16000",           # 16kHz sample rate
        "-ac", "1",               # Mono channel
        "-y",                     # Overwrite output
        $outputPath
    )

    try {
        & $ffmpegPath @arguments

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully extracted audio to: $outputPath" -ForegroundColor Green
        } else {
            Write-Host "Error extracting audio from: $videoPath" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error running FFmpeg: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
}

Write-Host "Audio extraction completed!" -ForegroundColor Green
