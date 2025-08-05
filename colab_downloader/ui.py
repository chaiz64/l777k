import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

class ColabDownloaderUI:
    def __init__(self, download_dir, download_limit_per_batch):
        self.download_dir = download_dir
        self.download_limit_per_batch = download_limit_per_batch

        # UI Elements
        self.output_area = widgets.Output()
        self.dir_input = widgets.Text(
            value=self.download_dir,
            placeholder='Enter your download folder path',
            description='Folder:',
            layout=widgets.Layout(width='auto')
        )
        self.refresh_button = widgets.Button(
            description="🔄 Refresh Files",
            button_style='primary',
            tooltip="Scan the download folder again"
        )
        self.clear_links_button = widgets.Button(
            description="🗑️ Clear Download History",
            button_style='danger',
            tooltip="Clear downloaded_links.txt file"
        )
        self.filter_input = widgets.Text(
            value="",
            placeholder='Search filename...',
            description='Search:',
            layout=widgets.Layout(width='auto')
        )
        self.status_label = widgets.HTML(value="")
        self.url_input = widgets.Text(
            value="",
            placeholder='Enter video/document URL to download (e.g., from YouTube, raw file link)',
            description='URL:',
            layout=widgets.Layout(width='auto')
        )
        self.download_url_button = widgets.Button(
            description="🌐 Download URL",
            button_style='success',
            tooltip="Download file from the provided URL"
        )
        self.cancel_download_button = widgets.Button(
            description="🛑 Cancel Current Batch",
            button_style='danger',
            tooltip="Stop the current batch download process",
            layout=widgets.Layout(width='auto')
        )
        # New: Cancel All Downloads Button
        self.cancel_all_downloads_button = widgets.Button(
            description="❌ Cancel All Downloads",
            button_style='danger',
            tooltip="Stop all pending downloads and clear the queue",
            layout=widgets.Layout(width='auto')
        )
        self.single_download_container = widgets.VBox([])
        self.batch_download_container = widgets.VBox([])
        self.document_files_container = widgets.VBox([])
        self.download_history_output = widgets.Output(layout=widgets.Layout(max_height='150px', overflow_y='auto'))

        self.main_layout = self._setup_main_layout()

    def _setup_main_layout(self):
        """Sets up the main UI layout."""
        header = widgets.HTML("<h1>🚀 Colab Video Downloader (Epic MVP + FFprobe)</h1>")
        instructions = widgets.HTML("""
            <p>Welcome to the advanced video downloader! You can:</p>
            <ul>
                <li><b>Specify Download Folder:</b> Enter the path to your video folder.</li>
                <li><b>Refresh Files:</b> Scan for new video files (duration from ffprobe if available).</li>
                <li><b>Download Single File:</b> Click the download button for each video.</li>
                <li><b>Batch Download:</b> Select files to skip and download the rest.</li>
                <li><b>Search:</b> Filter the video list by name.</li>
                <li><b>View Download History:</b> Check which files have already been downloaded.</li>
            </ul>
            <p><b>Note:</b> Videos shorter than 10 minutes (600 seconds) are skipped by default.</p>
        """)

        dir_control_box = widgets.HBox([self.dir_input, self.refresh_button])
        filter_box = widgets.HBox([self.filter_input, self.clear_links_button])
        # Updated: Include the new cancel all button in the URL download box
        url_download_box = widgets.HBox([self.url_input, self.download_url_button, self.cancel_download_button, self.cancel_all_downloads_button])

        return widgets.VBox([
            header,
            instructions,
            self.status_label,
            dir_control_box,
            filter_box,
            widgets.HTML("<h2>--- 🔗 Direct URL Download ---</h2>"),
            url_download_box,
            widgets.HTML("<h2>--- ⬇️ Single File Download (Videos) ---</h2>"),
            self.single_download_container,
            widgets.HTML("<h2>--- 📦 Batch Download (Videos) ---</h2>"),
            self.batch_download_container,
            widgets.HTML("<h2>--- 📄 Document/Data Files (.csv, .json, .md) ---</h2>"),
            self.document_files_container,
            widgets.HTML("<h2>--- 📜 Download History ---</h2>"),
            self.download_history_output,
            self.output_area
        ])

    def display_ui(self):
        display(self.main_layout)

    def update_status(self, message, color='black'):
        self.status_label.value = f"<p style='color:{color};'>{message}</p>"

    def clear_output_area(self):
        with self.output_area:
            clear_output(wait=True)

    def print_output(self, message):
        with self.output_area:
            print(message)

    def update_single_download_container(self, children):
        self.single_download_container.children = children

    def update_batch_download_container(self, children):
        self.batch_download_container.children = children

    def update_document_files_container(self, children):
        self.document_files_container.children = children

    def update_download_history_output(self, content):
        with self.download_history_output:
            clear_output(wait=True)
            print(content)

    def create_single_download_widget(self, file_info, on_click_handler):
        file_label_html = (f"<div style='padding-left: 5px; font-size:0.9em;'>"
                           f"📁 <b>{file_info['name']}</b><br>"
                           f"    <small>Size: {file_info['formatted_size']} | "
                           f"Duration: {file_info['formatted_duration']}"
                           f" ({file_info['raw_duration_sec']:.1f} seconds)</small>"
                           f"</div>")
        file_label = widgets.HTML(value=file_label_html)

        download_button = widgets.Button(description="⬇️ Download", button_style='info', layout=widgets.Layout(width='120px'))
        download_button.on_click(lambda b: on_click_handler(b, file_info))

        return widgets.HBox([download_button, file_label], layout=widgets.Layout(margin='2px 0'))

    def create_single_document_download_widget(self, file_info, on_click_handler):
        file_label_html = (f"<div style='padding-left: 5px; font-size:0.9em;'>"
                           f"📄 <b>{file_info['name']}</b><br>"
                           f"    <small>Size: {file_info['formatted_size']}</small>"
                           f"</div>")
        file_label = widgets.HTML(value=file_label_html)

        download_button = widgets.Button(description="⬇️ Download", button_style='info', layout=widgets.Layout(width='120px'))
        download_button.on_click(lambda b: on_click_handler(b, file_info))

        return widgets.HBox([download_button, file_label], layout=widgets.Layout(margin='2px 0'))

    def create_batch_checkbox_widget(self, video_info):
        display_name = video_info['name']
        if len(display_name) > 60:
            display_name = display_name[:57] + "..."

        tooltip_text = (f"Full Name: {video_info['name']}\n"
                        f"Size: {video_info['formatted_size']}\n"
                        f"Duration: {video_info['formatted_duration']} ({video_info['raw_duration_sec']:.1f} seconds)\n"
                        f"Path: {video_info['path']}")

        checkbox_description = f"Skip: {display_name} ({video_info['formatted_size']}, {video_info['formatted_duration']})"

        checkbox = widgets.Checkbox(
            value=False,
            description=checkbox_description,
            indent=False,
            tooltip=tooltip_text,
            layout=widgets.Layout(width='98%', margin='1px 0')
        )
        return checkbox

    def create_batch_download_buttons(self, on_batch_click, on_all_click):
        download_batch_button = widgets.Button(
            description=f"🚀 Start Selected Download ({self.download_limit_per_batch} files/batch)",
            button_style='success',
            tooltip=f"Download files *not* marked 'Skip', up to {self.download_limit_per_batch} files per click"
        )
        download_all_button = widgets.Button(
            description=f"⬇️ Download All Displayed ({self.download_limit_per_batch} files/batch)",
            button_style='warning',
            tooltip=f"Download *all* files currently displayed (ignores 'Skip' checkboxes), up to {self.download_limit_per_batch} files per click"
        )

        download_batch_button.on_click(on_batch_click)
        download_all_button.on_click(on_all_click)

        return widgets.HBox([download_batch_button, download_all_button], layout=widgets.Layout(margin='5px 0'))
