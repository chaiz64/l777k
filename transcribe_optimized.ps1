param(
    [Parameter(Mandatory = $false, ValueFromRemainingArguments = $true)]
    [string[]]$InputPaths
)

# Language configuration - change this to support different languages
# Supported languages: en (English), zh (Chinese), ja (Japanese), ko (Korean), vn (Vietnamese), th (Thai)
$languageOptions = @{
    "en" = "English"
    "zh" = "Chinese"
    "ja" = "Japanese"
    "ko" = "Korean"
    "vn" = "Vietnamese"
    "th" = "Thai"
}

# Change this to switch languages: "en", "zh", "ja", "ko", "vn", "th"
$languageCode = "zh"  # Chinese
$languageName = $languageOptions[$languageCode]

# Optimized settings for i9-9000K CPU, RTX 2080 GPU, 32GB RAM
# - Large model for better quality
# - CUDA GPU acceleration
# - Float16 precision for RTX 2080
# - 12 CPU threads for i9-9000K
# - Batched inference for 2x-4x speed increase
# - Batch size 16 for optimal GPU utilization

$exePath = ".\faster-whisper-xxl.exe"

# Collect all audio files
$audioFiles = @()

if ($InputPaths.Count -eq 0) {
    # If no arguments provided, use default wav folder
    $wavFolder = ".\wav"
    if (Test-Path $wavFolder) {
        $audioFiles = Get-ChildItem -Path $wavFolder -Filter "*.wav" -File | Select-Object -ExpandProperty FullName
    }
} else {
    foreach ($path in $InputPaths) {
        if (Test-Path $path) {
            $item = Get-Item $path
            if ($item.PSIsContainer) {
                # It's a folder, get all WAV files
                $audioFiles += Get-ChildItem -Path $path -Filter "*.wav" -File -Recurse | Select-Object -ExpandProperty FullName
            } else {
                # It's a file, check if it's WAV
                if ($item.Extension -eq ".wav") {
                    $audioFiles += $item.FullName
                }
            }
        }
    }
}

if ($audioFiles.Count -eq 0) {
    Write-Host "No WAV files found to process!" -ForegroundColor Red
    Write-Host "Usage: .\transcribe_optimized.ps1 [folder_path] or drag and drop WAV files/folders" -ForegroundColor Yellow
    exit 1
}

$arguments = @(
    "--model", "large-v2",
    "--language", $languageCode,
    "--task", "transcribe",
    "--device", "cuda",
    "--compute_type", "float16",
    "--threads", "12",
    "--batched",
    "--batch_size", "8",
    "--beam_size", "5",
    "--temperature", "0.0",
    "--best_of", "5",
    "--compression_ratio_threshold", "2.0",
    "--vad_filter", "True",
    "--vad_speech_pad_ms", "250",
    "--vad_method", "silero_v3",
    "--chunk_length", "20",
    "--no_speech_threshold", "0.5",
    "--standard_asia",
    "--sentence",
    "--min_speakers", "2",
    "--max_speakers", "4",
    "--output_dir", "sub",
    "--output_format", "srt", "json", "text",
    "--batch_recursive",
    "--check_files",
    "--print_progress",
    "--beep_off"
)

# Add audio files to arguments
$arguments += $audioFiles

Write-Host "Starting optimized transcription with settings:" -ForegroundColor Green
Write-Host "Model: large-v2" -ForegroundColor Yellow
Write-Host "Language: $languageName" -ForegroundColor Yellow
Write-Host "Device: CUDA (RTX 2080)" -ForegroundColor Yellow
Write-Host "Compute type: float16" -ForegroundColor Yellow
Write-Host "Threads: 12" -ForegroundColor Yellow
Write-Host "Batched inference: enabled" -ForegroundColor Yellow
Write-Host "Batch size: 8" -ForegroundColor Yellow
Write-Host "Beam size: 5" -ForegroundColor Yellow
Write-Host "Temperature: 0.0" -ForegroundColor Yellow
Write-Host "Best of: 5" -ForegroundColor Yellow
Write-Host "Compression ratio threshold: 2.0" -ForegroundColor Yellow
Write-Host "VAD filter: enabled" -ForegroundColor Yellow
Write-Host "VAD speech padding: 250ms" -ForegroundColor Yellow
Write-Host "VAD method: silero_v3" -ForegroundColor Yellow
Write-Host "Chunk length: 20 seconds" -ForegroundColor Yellow
Write-Host "No speech threshold: 0.5" -ForegroundColor Yellow
Write-Host "Task: transcribe" -ForegroundColor Yellow
Write-Host "Standard Asia: enabled" -ForegroundColor Yellow
Write-Host "Sentence splitting: enabled" -ForegroundColor Yellow
Write-Host ""

# Execute the command
& $exePath @arguments

Write-Host "`nTranscription completed!" -ForegroundColor Green
