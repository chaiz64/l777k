import os
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import google.colab.files
import time
import shutil # For checking if ffprobe is installed
from .utils import format_duration, format_bytes, get_video_info
from .ui import ColabDownloaderUI # Import the UI class

# --- Setup and Initialization ---
# Path to your download folder
# Initial default path, user can change this via UI
default_download_dir = "/content/DouyinLiveRecorder/downloads/抖音直播/" # Example folder path
download_limit_per_batch = 1 # Limit downloads per batch (can be adjusted)
# List of common video file extensions to support
video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.ogg', '.3gp', '.ts')
# List of common document/data file extensions to support
document_extensions = ('.csv', '.json', '.md')

# File name for saving downloaded URLs
download_links_file = "downloaded_links.txt"

# Ensure the download links file exists
if not os.path.exists(download_links_file):
    with open(download_links_file, "w") as f:
        f.write("") # Create an empty file

# --- Helper Functions ---

class ColabVideoDownloader:
    def __init__(self, download_dir, download_limit_per_batch, video_extensions, document_extensions, download_links_file):
        self.download_dir = download_dir
        self.download_limit_per_batch = download_limit_per_batch
        self.video_extensions = video_extensions
        self.document_extensions = document_extensions
        self.download_links_file = download_links_file
        self.video_files_info = []
        self.document_files_info = []
        self.skip_checkboxes = []
        self.checkbox_file_map = {}
        self.current_filter_text = ""
        self.ffprobe_available = bool(shutil.which('ffprobe'))
        self.cancel_batch_download_flag = False # New flag for cancellation
        self.cancel_all_downloads_flag = False # New flag for cancelling all downloads

        # Initialize UI
        self.ui = ColabDownloaderUI(self.download_dir, self.download_limit_per_batch)
        self.output_area = self.ui.output_area # Reference the output area from UI
        self.dir_input = self.ui.dir_input
        self.refresh_button = self.ui.refresh_button
        self.clear_links_button = self.ui.clear_links_button
        self.filter_input = self.ui.filter_input
        self.url_input = self.ui.url_input
        self.download_url_button = self.ui.download_url_button
        self.single_download_container = self.ui.single_download_container
        self.batch_download_container = self.ui.batch_download_container
        self.document_files_container = self.ui.document_files_container
        self.download_history_output = self.ui.download_history_output

        self._setup_event_handlers()
        if not self.ffprobe_available:
            self.ui.update_status("⚠️ <b>Warning:</b> `ffprobe` not found. Video duration simulation will be used, which may not be accurate.", color='orange')
        else:
            self.ui.update_status("✅ `ffprobe` is available for accurate video duration.", color='green')

        self._scan_files()
        self._update_ui_display()
        self._display_download_history()

    def _setup_event_handlers(self):
        self.ui.refresh_button.on_click(self._on_refresh_button_click)
        self.ui.clear_links_button.on_click(self._on_clear_links_button_click)
        self.ui.filter_input.observe(self._on_filter_input_change, names='value')
        self.ui.dir_input.observe(self._on_dir_input_change, names='value')
        self.ui.download_url_button.on_click(self._on_download_url_click)
        self.ui.cancel_download_button.on_click(self._on_cancel_download_click)
        self.ui.cancel_all_downloads_button.on_click(self._on_cancel_all_downloads_click) # New event handler

    def _on_dir_input_change(self, change):
        self.download_dir = change['new']
        self.ui.clear_output_area()
        self.ui.print_output(f"Download folder changed to: {self.download_dir}")
        self._scan_files()
        self._update_ui_display()

    def _on_refresh_button_click(self, b):
        self.ui.clear_output_area()
        self.ui.print_output("🔄 Refreshing file list...")
        self._scan_files()
        self._update_ui_display()
        self.ui.print_output("✅ File list refreshed!")


    def _on_clear_links_button_click(self, b):
        self.ui.clear_output_area()
        try:
            with open(self.download_links_file, "w") as f:
                f.write("")
            self.ui.print_output("✅ Download history cleared!")
            self._display_download_history() # Refresh history display
        except Exception as e:
            self.ui.print_output(f"❌ Error clearing history: {e}")

    def _on_filter_input_change(self, change):
        self.current_filter_text = change['new'].lower()
        self._update_ui_display()

    def _scan_files(self):
        self.video_files_info = []
        self.document_files_info = [] # Clear document files info
        if not os.path.exists(self.download_dir):
            self.ui.print_output(f"⚠️ Folder {self.download_dir} not found!")
            return

        if not os.listdir(self.download_dir): # Check if directory is empty
            self.ui.print_output(f"ℹ️ Folder {self.download_dir} is empty.")
            return

        video_files_found_for_scan = []
        document_files_found_for_scan = []

        for root, _, files in os.walk(self.download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(self.video_extensions):
                    video_files_found_for_scan.append(file_path)
                elif file.lower().endswith(self.document_extensions): # New: collect document files
                    document_files_found_for_scan.append(file_path)

        self.ui.print_output(f"🔍 Found {len(video_files_found_for_scan)} potential video files and {len(document_files_found_for_scan)} potential document files. Retrieving info (this may take a moment)...")
        if not self.ffprobe_available:
            self.ui.print_output("    (ffprobe not found, video duration will be simulated)")

        # Process video files
        temp_video_list = []
        for i, file_path in enumerate(video_files_found_for_scan):
            info = get_video_info(file_path)
            if info and info.get("raw_duration_sec", 0) >= 600:
                temp_video_list.append(info)
            elif info:
                self.ui.print_output(f"    ⏩ Skipping video file {info['name']} (Duration: {info['formatted_duration']} - too short)")

        self.video_files_info = sorted(temp_video_list, key=lambda x: x['name'])
        self.ui.print_output(f"🎬 Found {len(self.video_files_info)} video files (length >= 10 minutes) ready for download:")
        if not self.video_files_info:
            self.ui.print_output("    ❌ No video files matching criteria in the specified folder.")

        # Process document files (new)
        temp_document_list = []
        for file_path in document_files_found_for_scan:
            file_name = os.path.basename(file_path)
            try:
                file_size = os.path.getsize(file_path)
                temp_document_list.append({
                    "name": file_name,
                    "path": file_path,
                    "size_bytes": file_size,
                    "formatted_size": format_bytes(file_size)
                })
            except Exception as e:
                self.ui.print_output(f"❌ Error getting info for document file {file_name}: {e}")

        self.document_files_info = sorted(temp_document_list, key=lambda x: x['name'])
        self.ui.print_output(f"📄 Found {len(self.document_files_info)} document/data files ready for download:")
        if not self.document_files_info:
            self.ui.print_output("    ❌ No document/data files matching criteria in the specified folder.")

    def _update_ui_display(self):
        """Updates the displayed file lists based on current filters and scan results."""
        self.checkbox_file_map.clear() # Clear map before repopulating
        self.skip_checkboxes = [] # Clear old checkbox widget instances

        # Filter video files
        filtered_video_files = [
            file_info for file_info in self.video_files_info
            if self.current_filter_text in file_info['name'].lower()
        ]

        # Filter document files
        filtered_document_files = [
            file_info for file_info in self.document_files_info
            if self.current_filter_text in file_info['name'].lower()
        ]

        # --- Update Single File Download section (Videos) ---
        single_video_widgets_children = []
        if not filtered_video_files:
            single_video_widgets_children.append(widgets.HTML("<p>🚫 No video files for single download.</p>"))
        else:
            for video in filtered_video_files:
                single_video_widgets_children.append(self.ui.create_single_download_widget(video, self._on_single_download_click))
        self.ui.update_single_download_container(single_video_widgets_children)

        # --- Update Batch Download section (Videos) ---
        batch_checkbox_widgets = []
        if not filtered_video_files:
            self.ui.update_batch_download_container([widgets.HTML("<p>🚫 No video files for batch download.</p>")])
        else:
            for video in filtered_video_files:
                checkbox = self.ui.create_batch_checkbox_widget(video)
                self.skip_checkboxes.append(checkbox) # Add to list of widget instances
                self.checkbox_file_map[id(checkbox)] = video # Map widget ID to file_info
                batch_checkbox_widgets.append(checkbox)

            # Scrollable area for checkboxes
            skip_selection_vbox = widgets.VBox(children=batch_checkbox_widgets)
            scrollable_checkbox_area = widgets.Box(
                children=[skip_selection_vbox],
                layout=widgets.Layout(
                    max_height='300px', # Adjust height as needed
                    overflow_y='auto',
                    border='1px solid #ccc',
                    padding='5px',
                    width='100%' # Take full width of its container
                )
            )

            download_buttons_hbox = self.ui.create_batch_download_buttons(self._on_download_batch_click, self._on_download_all_click)

            self.ui.update_batch_download_container([
                scrollable_checkbox_area,
                download_buttons_hbox
            ])

        # --- Update Document Files section (New) ---
        document_widgets_children = []
        if not filtered_document_files:
            document_widgets_children.append(widgets.HTML("<p>🚫 No document/data files found.</p>"))
        else:
            for doc_file in filtered_document_files:
                document_widgets_children.append(self.ui.create_single_document_download_widget(doc_file, self._on_single_document_download_click))
        self.ui.update_document_files_container(document_widgets_children)

    def _on_single_download_click(self, b, file_info):
        """Handles single video file download button click."""
        b.disabled = True # Disable button during download attempt
        self.ui.clear_output_area() # Clear previous messages in output area
        self.ui.print_output(f"⏳ Preparing to download: {file_info['name']}...")
        try:
            google.colab.files.download(file_info['path'])
            # Record download after initiation
            with open(self.download_links_file, "a") as f:
                f.write(f"{file_info['path']}\n")
            self.ui.print_output(f"✅ Download of {file_info['name']} initiated! (Path saved)")
            self._display_download_history() # Update history display
        except Exception as e:
            self.ui.print_output(f"❌ Error downloading {file_info['name']}: {e}")
        finally:
            b.disabled = False # Re-enable button

    def _on_single_document_download_click(self, b, file_info):
        """Handles single document file download button click."""
        b.disabled = True
        self.ui.clear_output_area()
        self.ui.print_output(f"⏳ Preparing to download: {file_info['name']}...")
        try:
            google.colab.files.download(file_info['path'])
            with open(self.download_links_file, "a") as f:
                f.write(f"{file_info['path']}\n")
            self.ui.print_output(f"✅ Download of {file_info['name']} initiated! (Path saved)")
            self._display_download_history()
        except Exception as e:
            self.ui.print_output(f"❌ Error downloading {file_info['name']}: {e}")
        finally:
            b.disabled = False

    def _on_cancel_download_click(self, b):
        """Handles the cancel download button click."""
        self.cancel_batch_download_flag = True
        self.ui.print_output("🛑 Batch download cancellation requested. Current download will finish, subsequent downloads will be skipped.")

    def _on_cancel_all_downloads_click(self, b):
        """Handles the cancel all downloads button click."""
        self.cancel_all_downloads_flag = True
        self.cancel_batch_download_flag = True # Also set batch flag to stop current batch
        self.ui.print_output("❌ All pending downloads cancellation requested. No more downloads will be initiated.")

    def _on_download_batch_click(self, b):
        """Handles the batch download button click (skipping selected)."""
        b.disabled = True # Disable button during operation
        self.cancel_batch_download_flag = False # Reset flag for new batch

        files_to_download = []
        # Iterate through the current skip_checkboxes and use the map to get corresponding file_info
        for checkbox in self.skip_checkboxes:
            if not checkbox.value: # If checkbox is NOT checked (i.e., not skipped)
                file_info = self.checkbox_file_map.get(id(checkbox))
                if file_info:
                    files_to_download.append(file_info)

        self.ui.clear_output_area()
        if not files_to_download:
            self.ui.print_output("🚫 No files selected for download (or all files marked 'Skip').")
            b.disabled = False # Re-enable button
            return

        self._initiate_batch_download(files_to_download, b)


    def _on_download_all_click(self, b):
        """Handles the 'Download All Displayed' button click."""
        b.disabled = True

        # Download all currently filtered files, ignoring skip checkboxes for this action
        # This means we need to re-evaluate filtered_files as _update_ui_display might have changed since last call
        files_to_download = [
            file_info for file_info in self.video_files_info
            if self.current_filter_text in file_info['name'].lower()
        ]

        self.ui.clear_output_area()
        if not files_to_download:
            self.ui.print_output("🚫 No files available for download in the current view.")
            b.disabled = False
            return
        self._initiate_batch_download(files_to_download, b)


    def _initiate_batch_download(self, files_to_download_list, button_widget):
        """Initiates the batch download process."""
        # This function assumes files_to_download_list is already prepared
        self.ui.print_output(f"📦 Preparing {len(files_to_download_list)} files for batch download...")

        downloaded_this_session = 0
        files_actually_triggered_for_download = []

        try:
            for i, file_info in enumerate(files_to_download_list):
                if self.cancel_batch_download_flag or self.cancel_all_downloads_flag:
                    self.ui.print_output("\n🛑 Batch download cancelled by user.")
                    # If cancel_all_downloads_flag is set, reset it for future operations
                    if self.cancel_all_downloads_flag:
                        self.cancel_all_downloads_flag = False
                        self.ui.print_output("    All pending downloads have been stopped.")
                    break # Exit the loop if cancellation is requested

                if downloaded_this_session >= self.download_limit_per_batch:
                    self.ui.print_output(f"\n⚠️ Batch download limit reached ({self.download_limit_per_batch} files).")
                    self.ui.print_output("    Please complete the pending downloads, then click the download button again for the next batch.")
                    break # Stop processing more files in this batch

                self.ui.print_output(f"\n({downloaded_this_session + 1}/{min(len(files_to_download_list), self.download_limit_per_batch)}) Downloading: {file_info['name']}...")
                try:
                    google.colab.files.download(file_info['path'])
                    with open(self.download_links_file, "a") as f:
                        f.write(f"{file_info['path']}\n")
                    self.ui.print_output(f"✅ Download of {file_info['name']} initiated! (Path saved)")
                    files_actually_triggered_for_download.append(file_info['path'])
                    self._display_download_history() # Update history display immediately
                    downloaded_this_session += 1
                    # Add a small delay to allow browser to catch up if multiple downloads are rapid
                    if downloaded_this_session < self.download_limit_per_batch and (i + 1) < len(files_to_download_list):
                        time.sleep(1.5) # Slightly longer delay for user to manage download prompts
                except Exception as e:
                    self.ui.print_output(f"❌ Error downloading {file_info['name']}: {e}")

            # --- After loop summary ---
            remaining_in_selection = len(files_to_download_list) - len(files_actually_triggered_for_download)
            if self.cancel_batch_download_flag: # This flag is set by both cancel buttons
                self.ui.print_output(f"\nPartial batch download completed. {len(files_actually_triggered_for_download)} files initiated before cancellation.")
            elif not files_actually_triggered_for_download and files_to_download_list:
                self.ui.print_output("\n🚫 No downloads occurred in this batch (check errors above or limit).")
            elif remaining_in_selection > 0 :
                self.ui.print_output(f"\n🎉 Batch download of {len(files_actually_triggered_for_download)} files initiated! {remaining_in_selection} files remaining in selected list.")
                if downloaded_this_session >= self.download_limit_per_batch:
                    self.ui.print_output("    Click the download button again for the next batch.")
            else: # All selected files processed (or attempted)
                self.ui.print_output(f"\n🎉 All selected files ({len(files_actually_triggered_for_download)} files) have been processed for download!")

        finally:
            button_widget.disabled = False # Re-enable the button that triggered this
            self.cancel_batch_download_flag = False # Reset for next batch

    def _display_download_history(self):
        """Displays the content of the downloaded links file."""
        self.ui.clear_download_history_output()
        try:
            with open(self.download_links_file, "r") as f:
                history_content = f.read().strip()
            if history_content:
                # Display only unique file basenames for brevity and clarity
                history_paths = history_content.split('\n')
                unique_downloaded_files = sorted(list(set([os.path.basename(p) for p in history_paths if p.strip()])))

                if unique_downloaded_files:
                    display_text = "Files previously initiated for download (filenames):\n- " + "\n- ".join(unique_downloaded_files)
                    self.ui.update_download_history_output(display_text)
                else:
                    self.ui.update_download_history_output("No files in download history yet.")
            else:
                self.ui.update_download_history_output("No files in download history yet.")
        except FileNotFoundError:
            self.ui.update_download_history_output("Download history file not found (will be created on first download).")
        except Exception as e:
            self.ui.update_download_history_output(f"❌ An error occurred in history display: {e}")

    def _on_download_url_click(self, b):
        """Handles direct URL download button click."""
        url = self.ui.url_input.value.strip()
        if not url:
            self.ui.clear_output_area()
            self.ui.print_output("❌ Please enter a URL to download.")
            return

        b.disabled = True # Disable button during download
        self.ui.clear_output_area()
        self.ui.print_output(f"⏳ Attempting to download from URL: {url}...")
        try:
            import requests # Import requests here to avoid circular dependency ifutils also imports it

            # Determine a filename from the URL
            filename = os.path.basename(url.split('?')[0])
            if not filename: # Fallback if URL doesn't have a clear filename
                filename = "downloaded_file" + str(int(time.time()))

            local_filepath = os.path.join(self.download_dir, filename)
            os.makedirs(self.download_dir, exist_ok=True) # Ensure download directory exists

            with requests.get(url, stream=True) as r:
                r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                with open(local_filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # Optional: print progress
                        # self.ui.print_output(f"\r    Downloading... {format_bytes(downloaded_size)} / {format_bytes(total_size)}", end="")
            # self.ui.print_output("\n") # Newline after progress

            google.colab.files.download(local_filepath) # Trigger browser download
            # Record download after initiation
            with open(self.download_links_file, "a") as f:
                f.write(f"{local_filepath}\n") # Save local path, not URL
            self.ui.print_output(f"✅ Download of {filename} initiated from URL! (Path saved)")
            self._display_download_history()
            self.ui.url_input.value = "" # Clear input after initiating download
        except requests.exceptions.RequestException as e:
            self.ui.print_output(f"❌ Network or HTTP error downloading from URL {url}: {e}")
        except Exception as e:
            self.ui.print_output(f"❌ General error downloading from URL {url}: {e}")
        finally:
            b.disabled = False # Re-enable button

# Instantiate and display the app
app = ColabVideoDownloader(default_download_dir, download_limit_per_batch, video_extensions, document_extensions, download_links_file)
display(app.main_layout)
