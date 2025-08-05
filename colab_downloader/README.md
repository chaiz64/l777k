# Colab Video and Document Downloader

This project provides a Google Colab-compatible interface for managing and downloading video and document files from a specified directory. It leverages `ipywidgets` for an interactive UI and `ffprobe` (if available) for accurate video metadata.

## Features

- **Dynamic Folder Scanning:** Specify any folder path to scan for video (`.mp4`, `.avi`, etc.) and document (`.csv`, `.json`, `.md`) files.
- **Video Metadata:** Retrieves video size and duration using `ffprobe`. Includes a fallback simulation if `ffprobe` is not installed.
- **Single File Download:** Download individual video or document files directly.
- **Batch Download (Videos):** Select multiple video files to download in batches, with an option to skip selected files or download all displayed.
- **Download History:** Keeps a record of all initiated downloads.
- **File Filtering:** Search and filter files by name.
- **User-Friendly Interface:** Interactive widgets for easy navigation and control.

## Setup and Usage in Google Colab

1.  **Upload `main.py`:** Upload the `main.py` file to your Google Colab environment.
2.  **Install Dependencies:** Run the following command in a Colab cell to install necessary libraries:
    ```bash
    !pip install -r requirements.txt
    ```
3.  **Install `ffmpeg` (for `ffprobe`):** For accurate video duration, `ffprobe` (part of `ffmpeg`) is highly recommended. Install it in Colab with:
    ```bash
    !apt-get update -qq && apt-get install -y ffmpeg
    ```
4.  **Run the Application:** Execute the `main.py` script in a Colab cell:
    ```python
    %run main.py
    ```
    The interactive UI will appear, allowing you to specify your download directory, refresh file lists, and initiate downloads.

## Project Structure

- `main.py`: The core application script containing the `ColabVideoDownloader` class and UI logic.
- `requirements.txt`: Lists Python dependencies.
- `README.md`: This documentation file.

## Future Enhancements (Epic Level)

- **Direct URL Input:** Allow users to paste direct video/document URLs for download.
- **Cloud Storage Integration:** Options to upload downloaded files directly to Google Drive, Dropbox, etc.
- **Advanced Filtering/Sorting:** More robust filtering options (by size, date, type) and sorting capabilities.
- **Download Progress Indicators:** More detailed progress bars for ongoing downloads.
- **Error Logging and Reporting:** Improved internal logging and user-facing error reports.
- **Modular Design:** Further refactor the codebase into smaller, more manageable modules (e.g., `ui.py`, `file_utils.py`, `downloader.py`).
- **Unit Tests:** Add comprehensive unit tests for core functionalities.
- **Configuration File:** Externalize configurable parameters (e.g., `download_limit_per_batch`, default paths) into a separate config file.
