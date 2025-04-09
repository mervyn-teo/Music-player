import sys
import os
import datetime
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

from yt_worker import MetadataWorker, DownloadWorker


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        if not os.path.exists("temp"):
            os.makedirs("temp")
            print("found no temp folder, creating...")
        if not os.path.exists("playlist.json"):
            open("playlist.json", "x")
            print("found no playlist, creating...")
            with open("playlist.json", "w") as temp:
                json.dump({"songs": []}, temp, indent=2)
        self.player = QMediaPlayer()
        self.player.error.connect(self.handle_player_error)
        self.initUI()

    def initUI(self):
        self.playlist_shown = False
        self.playing = False
        self.filename = None
        self.queue = []
        self.now_playing_num = 0

        # style sheets
        self.text_style = "color: white;"
        self.playlist_list_style = "QPushButton{\
                                    background-color : #252729;\
                                    color: white;\
                                    border: none;\
                                    margin: 0px;\
                                    text-align: left;\
                                }\
                                QPushButton:pressed{\
                                    background-color: darkorange;\
                                    color: black;\
                                }\
                                QPushButton:hover:!pressed{\
                                    background-color: orange;\
                                    color: black;\
                                }"
        self.playlist_up_down_style = "QPushButton{\
                                            background-color : #252729;\
                                            color: white;\
                                            border: none;\
                                            margin: 0px;\
                                            width: 15px;\
                                            text-align: center;\
                                        }\
                                        QPushButton:pressed{\
                                            background-color: darkorange;\
                                            color: black;\
                                        }\
                                        QPushButton:hover:!pressed{\
                                            background-color: orange;\
                                            color: black;\
                                        }"
        self.highlight_text_style = "color: orange;"
        self.window_style = "background-color: #252729;"
        self.normal_button_style = "QPushButton{\
                                    background-color : #64d6d2;\
                                    color: black;\
                                    padding:8px;\
                                    border-radius: 2px;\
                                }\
                                QPushButton:pressed{\
                                    background-color: #59beba;\
                                }\
                                QPushButton:hover:!pressed{\
                                    background-color: #6feee9;\
                                    color: #214746;\
                                }"
        self.play_style = "QPushButton{\
                                    background-color: #a1d664;\
                                    color: black;\
                                    padding:8px;\
                                    border-radius: 2px;\
                                }\
                                QPushButton:pressed{ \
                                    background-color: #8fbe59;\
                                }\
                                QPushButton:hover:!pressed{\
                                    background-color: #b3ee6f;\
                                    color: #364721;\
                                }"
        self.pause_style = "QPushButton{\
                                    background-color : #d66468;\
                                    color: black;\
                                    padding:8px;\
                                    border-radius: 2px;\
                                }\
                                QPushButton:pressed{\
                                    background-color: #be595d;\
                                }\
                                QPushButton:hover:!pressed{\
                                    background-color: #ee6f74;\
                                    color: #472123;\
                                }"

        self.url_style = "QLineEdit, QLineEdit:focus{ \
                                border: 1px solid white;\
                                border-top-style: none;\
                                border-left-style: none;\
                                border-right-style: none;\
                                color: white;}"
        self.slider_style = "QSlider::groove:horizontal {\
                                border: 1px solid #999999;\
                                height: 1px; \
                                background: #B1B1B1;\
                            }\
                            QSlider::handle:horizontal {\
                                background: #a1d664;\
                                border: 1px solid #5c5c5c;\
                                width: 8px;\
                                margin: -4px -1px; \
                                border-radius: 4px;\
                            }"
        self.volume_slider_style = "QSlider::groove:horizontal {\
                                        border: 1px solid #999999;\
                                        height: 1px; \
                                        width:100px;\
                                        background: #B1B1B1;\
                                    }\
                                    QSlider::handle:horizontal {\
                                        background: #a1d664;\
                                        border: 1px solid #5c5c5c;\
                                        width: 8px;\
                                        margin: -4px 8px; \
                                        border-radius: 4px;\
                                    }"
        self.timer = QTimer(self)

        # buffer next song
        self.buffer_option = True
        self.next_song_downloaded = False
        self.next_song_filename = ''

        # load playlist
        with open('playlist.json', 'r', encoding='utf-8') as f:
            self.playlist = json.load(f)

        # Window
        self.setWindowTitle("YouTube Audio Player")
        self.setStyleSheet(self.window_style)

        self.setWindowOpacity(0.93)

        # self.setGeometry(300, 300, 300, 150)

        # layouts
        layout = QVBoxLayout()
        horizontal_button = QHBoxLayout()
        horizontal_slider = QHBoxLayout()
        self.playlist_box = QVBoxLayout()
        self.queue_box = QVBoxLayout()

        # overall layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        # URL
        self.url_entry = QLineEdit(self)
        self.url_entry.setStyleSheet(self.url_style)
        self.url_entry.setPlaceholderText("Enter YouTube URL")
        layout.addWidget(self.url_entry)

        # Download and play button
        self.download_play_button = QPushButton(self)
        self.download_play_button.setFocusPolicy(Qt.NoFocus)
        self.download_and_play_icon = self.style().standardIcon(getattr(QStyle, 'SP_ToolBarVerticalExtensionButton'))
        self.download_play_button.setIcon(self.download_and_play_icon)
        self.download_play_button.setStyleSheet(self.normal_button_style)
        self.download_play_button.clicked.connect(self.download_and_play)
        horizontal_button.addWidget(self.download_play_button)

        # play/pause button
        self.play_button = QPushButton(self)
        self.play_button.setFocusPolicy(Qt.NoFocus)
        self.pause_icon = self.style().standardIcon(getattr(QStyle, 'SP_MediaPause'))
        self.play_icon = self.style().standardIcon(getattr(QStyle, 'SP_MediaPlay'))
        self.play_button.setIcon(self.play_icon)
        self.play_button.setStyleSheet(self.play_style)
        self.play_button.clicked.connect(self.play_pause)
        horizontal_button.addWidget(self.play_button)

        # next song button
        self.next_song_button = QPushButton(self)
        self.next_song_button.setFocusPolicy(Qt.NoFocus)
        self.next_icon = self.style().standardIcon(getattr(QStyle, 'SP_MediaSkipForward'))
        self.next_song_button.setIcon(self.next_icon)
        self.next_song_button.setStyleSheet(self.normal_button_style)
        self.next_song_button.clicked.connect(self.next_song)
        horizontal_button.addWidget(self.next_song_button)

        # add playlist button
        self.add_playlist_button = QPushButton("add to playlist", self)
        self.add_playlist_button.setFocusPolicy(Qt.NoFocus)
        self.add_playlist_button.setStyleSheet(self.normal_button_style)
        self.add_playlist_button.clicked.connect(self.add_to_playlist)
        horizontal_button.addWidget(self.add_playlist_button)

        # show/hide play button
        self.show_playlist_button = QPushButton("show playlist", self)
        self.show_playlist_button.setFocusPolicy(Qt.NoFocus)
        self.show_playlist_button.setStyleSheet(self.normal_button_style)
        self.show_playlist_button.clicked.connect(self.show_playlist)
        horizontal_button.addWidget(self.show_playlist_button)

        # add song to queue
        self.add_url_to_queue_button = QPushButton("add to queue", self)
        self.add_url_to_queue_button.setFocusPolicy(Qt.NoFocus)
        self.add_url_to_queue_button.setStyleSheet(self.normal_button_style)
        self.add_url_to_queue_button.clicked.connect(self.add_url_to_queue)
        horizontal_button.addWidget(self.add_url_to_queue_button)

        # add playlist to song
        self.add_playlist_to_queue_button = QPushButton("add playlist to queue", self)
        self.add_playlist_to_queue_button.setFocusPolicy(Qt.NoFocus)
        self.add_playlist_to_queue_button.setStyleSheet(self.normal_button_style)
        self.add_playlist_to_queue_button.clicked.connect(self.add_playlist_to_queue)
        horizontal_button.addWidget(self.add_playlist_to_queue_button)

        # # add youtube playlist to playlist
        # self.add_yt_playlist_button = QPushButton("add youtube playlist to playlist", self)
        # self.add_yt_playlist_button.setStyleSheet(self.normal_button_style)
        # self.add_yt_playlist_button.clicked.connect(self.add_yt_playlist)
        # horizontal_button.addWidget(self.add_yt_playlist_button)

        # play queue
        self.queue_label = QLabel("Song queue:")
        self.queue_label.setStyleSheet(self.text_style)
        self.queue_box.addWidget(self.queue_label)
        layout.addLayout(self.queue_box)

        # initialise playlists
        self.playlist_label = QLabel("playlist:")
        self.playlist_label.setStyleSheet(self.text_style)
        self.playlist_label.setVisible(False)
        self.playlist_box.addWidget(self.playlist_label)
        self.init_playlist()
        layout.addLayout(self.playlist_box)

        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider)

        layout.addLayout(horizontal_button)

        # slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 1000)
        self.slider.setStyleSheet(self.slider_style)
        self.slider.sliderMoved.connect(self.set_position)
        horizontal_slider.addWidget(self.slider, Qt.AlignLeft)

        self.time_text = QLabel("00:00 / 00:00")
        self.time_text.setStyleSheet(self.text_style)
        horizontal_slider.addWidget(self.time_text)

        layout.addLayout(horizontal_slider)

        # volume
        self.volume = 30
        self.player.setVolume(self.volume)
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setStyleSheet(self.volume_slider_style)
        self.volume_slider.sliderMoved.connect(self.volume_adjust)

        self.volume_text = QLabel('Volume:')
        self.volume_text.setStyleSheet(self.text_style)
        horizontal_slider.addWidget(self.volume_text)
        horizontal_slider.addWidget(self.volume_slider)

    def handle_player_error(self, error):
        print(f"QMediaPlayer error: {self.player.errorString()}")
        self.setWindowTitle(f"Playback error: {self.player.errorString()}")

    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()
        QMainWindow.mousePressEvent(self, event)

    def start_metadata_worker(self, url, on_finish_slot, on_error_slot):
        """Starts the MetadataWorker for a given URL."""
        print(f"Starting metadata fetch for URL: {url}")
        self.setWindowTitle("Getting song info...")

        # Use distinct thread/worker instances for concurrent requests if needed
        # For simplicity here, reusing self.meta_thread, but ensure it's safe
        # If multiple metadata requests can happen, use unique instances like before
        meta_thread = QThread() # Create new instance each time
        meta_worker = MetadataWorker(url)
        meta_worker.moveToThread(meta_thread)

        # Connect signals
        meta_thread.started.connect(meta_worker.run)
        meta_worker.finished.connect(on_finish_slot)
        meta_worker.error.connect(on_error_slot)
        # Ensure cleanup
        meta_worker.finished.connect(meta_thread.quit)
        # Use lambda to capture worker and thread for deletion
        meta_worker.finished.connect(lambda w=meta_worker: w.deleteLater())
        meta_thread.finished.connect(lambda t=meta_thread: t.deleteLater())

        meta_thread.start()
        # Keep a reference if needed, e.g., self.current_meta_thread = meta_thread

    def init_playlist(self):
        if len(self.playlist["songs"]) > 0:
            for i in range(len(self.playlist["songs"])):
                temp_box = QHBoxLayout()
                temp = QPushButton()

                # playlist titles
                temp.setFocusPolicy(Qt.NoFocus)
                # Pass both ID and name
                song_id = self.playlist['songs'][i]['ID']
                song_name = self.playlist['songs'][i]['name']
                f = self.play_from_playlist(song_id, song_name)
                temp.clicked.connect(f)
                temp.setText(f"{i + 1}: {song_name}")
                temp.setVisible(False)
                temp.setStyleSheet(self.playlist_list_style)

                # playlist actions
                up = QPushButton('↑')
                down = QPushButton('↓')
                u = self.rank_up(i)
                d = self.rank_down(i)
                up.setStyleSheet(self.playlist_up_down_style)
                down.setStyleSheet(self.playlist_up_down_style)
                up.clicked.connect(u)
                down.clicked.connect(d)
                # Set initial visibility based on the current state
                is_visible = self.playlist_shown
                temp.setVisible(is_visible)
                up.setVisible(is_visible)
                down.setVisible(is_visible)

                temp_box.addWidget(up)
                temp_box.addWidget(down)
                temp_box.addWidget(temp, Qt.AlignLeft)  # add playlist to layout
                self.playlist_box.addLayout(temp_box)

    def rank_down(self, i):
        def ret_func():
            maxi = len(self.playlist['songs']) - 1
            if not i == maxi:
                temp = self.playlist['songs'][i]
                self.playlist['songs'][i] = self.playlist['songs'][i + 1]
                self.playlist['songs'][i + 1] = temp
                self.refresh_playlist()
                with open('playlist.json', 'w') as f2:
                    json.dump(self.playlist, f2, indent=2)
        return ret_func

    def rank_up(self, i):
        def ret_func():
            if not i == 0:
                print(i)
                temp = self.playlist['songs'][i]
                self.playlist['songs'][i] = self.playlist['songs'][i - 1]
                self.playlist['songs'][i - 1] = temp
                self.refresh_playlist()
                with open('playlist.json', 'w') as f2:
                    json.dump(self.playlist, f2, indent=2)
        return ret_func

    def volume_adjust(self):
        self.volume = self.volume_slider.sliderPosition()
        self.player.setVolume(self.volume)

    # This function is redundant now that add_to_playlist handles URLs directly
    # def add_yt_playlist(self):
    #     ... (removed) ...

    def play_from_playlist(self, video_id, song_name):
        """Plays a specific song from the playlist UI click."""
        def ret_func():
            print(f"Play from playlist requested: {song_name} ({video_id})")
            if self.playing:
                self.play_stop()

            # Add the selected song to the front of the queue
            # Find the song info (though we already have it)
            # This assumes song_name passed is reliable.
            self.queue.insert(0, {"name": song_name, "ID": video_id})
            self.refresh_queue()

            # Check if file exists locally first
            audio_file = os.path.join("./temp", f"{video_id}.mp3")
            if os.path.exists(audio_file):
                print("Playing existing file from playlist.")
                self.play_music(audio_file, song_name)
            else:
                # File doesn't exist, start download
                print("File not found locally, downloading...")
                self.start_download_worker(video_id, song_name)
                # Playback will start in on_download_finished

        return ret_func

    # get_song_file_name is now async, handled by MetadataWorker

    # download_audio is removed - logic moved to specific actions

    def on_metadata_error(self, error_msg):
        print(f"Metadata error: {error_msg}")
        # Reset title or show specific error
        self.setWindowTitle("Error getting song info")
        # Potentially disable buttons or show a message box here

    def start_download_worker(self, video_id, song_name=""):
        """Starts the DownloadWorker for a given video ID."""
        print(f"Starting download for ID: {video_id}, Name: {song_name}")
        self.setWindowTitle(f"Downloading: {song_name}...")

        # Check if already downloading this ID? (Optional complexity)

        self.dl_thread = QThread()
        # Pass video_id and potentially song_name if needed by worker/slot
        self.dl_worker = DownloadWorker(video_id)
        self.dl_worker.moveToThread(self.dl_thread)

        # Connect signals before starting
        self.dl_thread.started.connect(self.dl_worker.run)
        # Pass necessary info via lambda or functools.partial if slot needs it
        self.dl_worker.finished.connect(lambda vid=video_id, name=song_name: self.on_download_finished(vid, name))
        self.dl_worker.error.connect(self.on_download_error) # Re-use error handler
        # Ensure cleanup
        self.dl_worker.finished.connect(self.dl_thread.quit)
        self.dl_worker.finished.connect(self.dl_worker.deleteLater)
        self.dl_thread.finished.connect(self.dl_thread.deleteLater)

        self.dl_thread.start()

    # Renamed from download_audio_file for clarity
    # def download_audio_file(self, video_id): # Now use start_download_worker
    #     self.dl_thread = QThread()
    #     self.dl_worker = DownloadWorker(video_id)
    #     self.dl_worker.moveToThread(self.dl_thread)
    #     self.dl_thread.started.connect(self.dl_worker.run)
    #     self.dl_worker.finished.connect(self.on_download_finished) # Problem: Needs context (song name, ID)
    #     self.dl_worker.error.connect(self.on_download_error)
    #     self.dl_worker.finished.connect(self.dl_thread.quit)
    #     self.dl_worker.finished.connect(self.dl_worker.deleteLater)
    #     self.dl_thread.finished.connect(self.dl_thread.deleteLater)
    #     self.dl_thread.start()

    def on_download_finished(self, video_id, song_name):
        """Handles successful download completion."""
        print(f"Finished download for ID: {video_id}, Name: {song_name}")
        audio_file = os.path.join("./temp", f"{video_id}.mp3")

        if not os.path.exists(audio_file):
             print(f"Error: Download finished but file not found: {audio_file}")
             self.setWindowTitle(f"Error: File missing for {song_name}")
             # Handle error - maybe try redownload or skip?
             # If this was meant to play next, call next_song?
             return

        # Check if this song is still the one we intend to play
        if self.queue and self.queue[0]['ID'] == video_id:
            self.play_music(audio_file, song_name)
        else:
            # Download finished, but it's not the current song in the queue
            # This could be a buffered song, or the queue changed.
            print(f"Downloaded {song_name}, but it's not the current song to play.")
            # Check if it's the *next* song for buffering
            if len(self.queue) > 1 and self.queue[1]['ID'] == video_id:
                self.next_song_downloaded = True
                self.next_song_filename = audio_file
                print(f"Buffered next song: {song_name}")
            # Reset title if it was showing download progress
            if self.windowTitle().startswith("Downloading:"):
                 self.setWindowTitle("YouTube Audio Player")


    def on_download_error(self, error_msg):
        print(f"Download error: {error_msg}")
        self.setWindowTitle("Error downloading audio")
        # Handle the error appropriately, e.g., skip song, show message
        # If a song was supposed to play, maybe try the next one?
        # self.next_song() # Be careful with potential loops

    def download_only(self, ID, name=""):
        """Initiates a download without immediate playback (for buffering)."""
        audio_file = os.path.join("./temp", f"{ID}.mp3")
        if not os.path.exists(audio_file):
             print(f"Buffering: Starting download for {name} ({ID})")
             self.start_download_worker(ID, name)
        else:
             print(f"Buffering: File already exists for {name} ({ID})")
             self.next_song_downloaded = True
             self.next_song_filename = audio_file


    # Removed duplicate keyPressEvent and related download handlers from here.
    # The correct versions exist earlier in the class definition.

    def keyPressEvent(self, event):  # keypress detection (KEEP THIS ONE)
        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Space):
            self.play_pause()
        elif event.key() == Qt.Key_Up:
            if self.volume > 100:
                self.volume = 100
                self.player.setVolume(self.volume)
            else:
                self.volume += 5
                self.player.setVolume(self.volume)
                self.volume_slider.setSliderPosition(self.volume)
        elif event.key() == Qt.Key_Down:
            if self.volume < 0:
                self.volume = 0
                self.player.setVolume(self.volume)
            else:
                self.volume -= 5
                self.player.setVolume(self.volume)
                self.volume_slider.setSliderPosition(self.volume)

    def download_and_play(self):
        """Handles the 'Download and Play' button click."""
        url = self.url_entry.text()
        if not url:
            print("No URL entered.")
            return # Or show a message to the user

        print(f"Download and play requested for URL: {url}")
        # Stop current playback before starting new
        if self.playing:
            self.play_stop()

        # Start metadata fetching
        self.start_metadata_worker(url, self.on_download_and_play_metadata_ready, self.on_metadata_error)

    def on_download_and_play_metadata_ready(self, info):
        """Callback after metadata is fetched for download_and_play."""
        try:
            is_playlist = info.get('_type') == 'playlist'
            if is_playlist:
                # Handle playlist: Add all to queue and start first
                entries = info.get('entries', [])
                playlist_items = []
                for entry in entries:
                    video_id = entry.get('id')
                    song_name = entry.get('title', 'Unknown Title')
                    if video_id:
                        playlist_items.append({'name': song_name, 'ID': video_id})

                if not playlist_items:
                    print("Playlist found, but no valid songs to play.")
                    self.setWindowTitle("Empty or invalid playlist")
                    return

                print(f"Playlist detected, adding {len(playlist_items)} songs to queue.")
                self.queue = playlist_items # Replace queue with playlist
                self.refresh_queue()
                # Now play the first song from the newly populated queue
                first_song = self.queue[0]
                video_id = first_song['ID']
                song_name = first_song['name']
                audio_file = os.path.join("./temp", f"{video_id}.mp3")
                if os.path.exists(audio_file):
                    self.play_music(audio_file, song_name)
                else:
                    self.start_download_worker(video_id, song_name)

            else:
                # Handle single video
                video_id = info.get('id')
                song_name = info.get('title', 'Unknown Title')

                if not video_id:
                    print("Error: Could not get video ID from metadata.")
                    self.setWindowTitle("Error: Missing video ID")
                    return

                print(f"Metadata received: {song_name} ({video_id})")
                # Clear queue and add this song
                self.queue = [{'name': song_name, 'ID': video_id}]
                self.refresh_queue()

                # Check if file exists, play or download
                audio_file = os.path.join("./temp", f"{video_id}.mp3")
                if os.path.exists(audio_file):
                    print("Playing existing file.")
                    self.play_music(audio_file, song_name)
                else:
                    print("File not found locally, starting download...")
                    self.start_download_worker(video_id, song_name)

            # Clear URL entry after processing
            self.url_entry.clear()

        except Exception as e:
            print(f"Error processing metadata for download/play: {e}")
            self.setWindowTitle("Error processing song info")


    def refresh_queue(self):
        r = self.queue_box.count()
        if r > 0:
            for i in reversed(range(r)):
                temp = self.queue_box.itemAt(i).widget()
                if temp != self.queue_label:
                    self.queue_box.removeWidget(temp)
        for i in range(len(self.queue)):
            self.queue_box.addWidget(QLabel(f"{i + 1}: {self.queue[i]['name']}"))
            if i == 0:
                self.queue_box.itemAt(i + 1).widget().setStyleSheet(self.highlight_text_style)
            else:
                self.queue_box.itemAt(i + 1).widget().setStyleSheet(self.text_style)

    def play_music(self, file_path, song_name):
        """Sets the media source and starts playback."""
        print(f"Playing music: {song_name} from {file_path}")
        try:
            # Ensure the file path is absolute for QUrl
            abs_file_path = os.path.abspath(file_path)
            media_content = QMediaContent(QUrl.fromLocalFile(abs_file_path))

            # Check if media is valid before playing
            if media_content.isNull():
                 print(f"Error: Could not create valid QMediaContent for {abs_file_path}")
                 self.setWindowTitle(f"Error: Invalid media for {song_name}")
                 # Attempt to play next song?
                 # self.next_song() # Careful with loops
                 return

            self.player.setMedia(media_content)

            # Check player status before playing
            if self.player.isAvailable():
                self.player.play()
                self.playing = True
                self.play_button.setIcon(self.pause_icon)
                self.play_button.setStyleSheet(self.pause_style)
                self.setWindowTitle(f"Now playing: {song_name}")
                self.volume_slider.setSliderPosition(self.volume) # Set volume again
                self.timer.start() # Start slider updates
                # Trigger buffering for the *next* song only after playback starts
                self.buffer_next() # Ensure this call exists
            else:
                 print(f"Error: Player not available for {abs_file_path}")
                 self.setWindowTitle(f"Error: Player unavailable for {song_name}")
                 # Attempt to play next song?
                 # self.next_song()

        except Exception as e:
            print(f"Error setting/playing media: {e}")
            self.setWindowTitle(f"Error playing {song_name}")
            self.playing = False # Ensure state is correct
            self.play_button.setIcon(self.play_icon)
            self.play_button.setStyleSheet(self.play_style)
            # Attempt to play next song?
            # self.next_song()


    def play_stop(self):
        """Stops playback and resets UI elements."""
        if self.playing:
            current_song_id = self.queue[0]['ID'] if self.queue else None
            self.player.stop()
            self.playing = False
            self.play_button.setIcon(self.play_icon) # Use icon
            self.play_button.setStyleSheet(self.play_style) # Reset style
            self.setWindowTitle("YouTube Audio Player")
            self.time_text.setText("00:00 / 00:00") # Reset timer display
            self.slider.setValue(0) # Reset slider
            self.timer.stop()
            print("Playback stopped.")
            # Clean up the file that was just playing? Optional.
            # self.cleanup_previous_song_file(current_song_id) # Uncomment if desired

    def play_pause(self):
        if self.playing:
            self.player.pause()
            self.play_button.setIcon(self.play_icon)
            self.playing = False
            self.play_button.setStyleSheet(self.play_style)
        elif len(self.queue) > 0: # If queue has items and we are not playing
            current_state = self.player.state()
            if current_state == QMediaPlayer.PausedState:
                # Resume playback
                self.player.play()
                self.playing = True
                self.play_button.setIcon(self.pause_icon)
                self.play_button.setStyleSheet(self.pause_style)
                self.setWindowTitle(f"Now playing: {self.queue[0]['name']}")
            elif current_state == QMediaPlayer.StoppedState:
                # Start playback of the first song in the queue
                song_to_play = self.queue[0]
                video_id = song_to_play['ID']
                song_name = song_to_play['name']
                print(f"Play button pressed (stopped state): Playing {song_name} ({video_id})")

                audio_file = os.path.join("./temp", f"{video_id}.mp3")

                # Check if file exists
                if os.path.exists(audio_file):
                    print("Playing existing file from queue.")
                    self.play_music(audio_file, song_name)
                else:
                    # File doesn't exist, start download
                    print("File not found in queue, downloading...")
                    self.start_download_worker(video_id, song_name)
                    # Playback will start in on_download_finished
            # else: QMediaPlayer.PlayingState - do nothing if already playing

    # Removed duplicate add_playlist_to_queue method.
    # The correct version exists later in the class definition.


    def add_playlist_to_queue(self): # Keep this one
        print(self.playlist['songs'])
        self.queue = self.queue + self.playlist['songs']
        self.refresh_queue()

    def add_url_to_queue(self):
        url = self.url_entry.text()
        if not url:
            return

        self.setWindowTitle("Getting song info...")
        # Start metadata extraction in background
        self.meta_thread_queue = QThread() # Use a distinct thread/worker instance
        self.meta_worker_queue = MetadataWorker(url)
        self.meta_worker_queue.moveToThread(self.meta_thread_queue)
        self.meta_thread_queue.started.connect(self.meta_worker_queue.run)
        self.meta_worker_queue.finished.connect(self.on_metadata_for_queue)
        self.meta_worker_queue.error.connect(self.on_metadata_error) # Can reuse error handler
        self.meta_worker_queue.finished.connect(self.meta_thread_queue.quit)
        self.meta_worker_queue.finished.connect(self.meta_worker_queue.deleteLater)
        self.meta_thread_queue.finished.connect(self.meta_thread_queue.deleteLater)
        self.meta_thread_queue.start()

    def on_metadata_for_queue(self, info):
        try:
            is_playlist = info.get('_type') == 'playlist'
            if is_playlist:
                entries = info.get('entries', [])
                playlist = []
                for entry in entries:
                    playlist.append({
                        'name': entry.get('fulltitle', 'Unknown Title'),
                        'ID': entry.get('id', None) # Use 'id' consistently
                    })
                    # Filter out entries without an ID
                playlist = [item for item in playlist if item['ID']]
                self.queue.extend(playlist)
                print(f"Added playlist to queue: {len(playlist)} songs")
            else:
                video_id = info.get('id', None)
                song_name = info.get('title', 'Unknown Title')
                if video_id:
                    self.queue.append({"name": song_name, "ID": video_id})
                    print(f"Added to queue: {song_name}")
                else:
                    print("Could not add to queue: Missing video ID")

            self.refresh_queue()
            self.setWindowTitle("YouTube Audio Player") # Reset title
        except Exception as e:
            print(f"Error processing metadata for queue: {e}")
            self.setWindowTitle("Error adding to queue")


    def update_slider(self):
        duration = self.player.duration()
        dt = datetime.timedelta(milliseconds=duration / 2)
        disp_duration = "{:0=2}".format(dt.seconds // 60) + ":" + "{:0=2}".format(dt.seconds % 60)
        if duration > 0:
            position = self.player.position()
            self.slider.setValue(int((position / duration) * 1000))
            st = datetime.timedelta(milliseconds=position / 2)
            disp_runtime = "{:0=2}".format(st.seconds // 60) + ":" + "{:0=2}".format(st.seconds % 60)
            self.time_text.setText(disp_runtime + " / " + disp_duration)
            if position == duration:  # goto next song after all is played
                self.next_song()

    def next_song(self):
        """Plays the next song in the queue."""
        print("Next song requested.")
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop() # Stop current playback

        if len(self.queue) > 1: # Need at least two songs to play the *next* one
            # Get the ID of the song that just finished (or was skipped)
            previous_song_id = self.queue[0]['ID']

            # Remove the current song (at index 0)
            del self.queue[0]
            self.refresh_queue() # Update UI immediately

            # Clean up the file for the song that is now removed from the front
            self.cleanup_previous_song_file(previous_song_id)

            # Get the new first song
            next_song_info = self.queue[0]
            video_id = next_song_info['ID']
            song_name = next_song_info['name']
            print(f"Playing next: {song_name} ({video_id})")

            # Check if the *next* song was buffered
            expected_buffered_file = os.path.join("./temp", f"{video_id}.mp3")
            if self.next_song_downloaded and self.next_song_filename == expected_buffered_file:
                print("Playing buffered next song.")
                self.play_music(self.next_song_filename, song_name)
                # Reset buffer state *after* playing
                self.next_song_downloaded = False
                self.next_song_filename = ''
            else:
                # Not buffered or wrong file buffered, check if file exists anyway
                audio_file = os.path.join("./temp", f"{video_id}.mp3")
                if os.path.exists(audio_file):
                     print("Playing existing file (next song).")
                     self.play_music(audio_file, song_name)
                else:
                    # Need to download the next song
                    print("Next song not found locally, downloading...")
                    self.start_download_worker(video_id, song_name)
                    # Playback starts in on_download_finished

            # Trigger buffering for the *new* next song after this one
            self.buffer_next()

        elif len(self.queue) == 1: # Was playing the last song
             del self.queue[0]
             self.refresh_queue()
             self.play_stop() # Stop playback, clear title etc.
             self.setWindowTitle("Queue finished")
             print("Queue finished.")
        else:
            # Queue was already empty, do nothing? Or ensure player is stopped.
            self.play_stop()
            print("Queue empty, cannot play next.")


    def buffer_next(self):
        """Initiates download for the next song in the queue if buffering is enabled."""
        self.next_song_downloaded = False # Reset buffer state initially
        self.next_song_filename = ''
        if self.buffer_option and len(self.queue) > 1:
            next_song_info = self.queue[1]
            video_id = next_song_info['ID']
            song_name = next_song_info['name']
            print(f"Checking buffer for next song: {song_name} ({video_id})")
            # Call download_only which checks existence and starts worker if needed
            self.download_only(video_id, song_name)
            # Note: self.next_song_downloaded is set in download_only or on_download_finished

    def cleanup_previous_song_file(self, video_id):
        """Safely removes the audio file for the given video ID."""
        if not video_id:
            return
        try:
            file_path = os.path.join("./temp", f"{video_id}.mp3")
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up file for ID {video_id}: {e}")


    def set_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            value = position / 1000 * duration
            self.player.setPosition(int(value))

    def add_to_playlist(self):
        url = self.url_entry.text()
        if not url:
            print("No URL entered to add to playlist.")
            return

        self.setWindowTitle("Getting info to add to playlist...")
        # Start metadata extraction in background
        self.meta_thread_playlist = QThread() # Use a distinct thread/worker instance
        self.meta_worker_playlist = MetadataWorker(url)
        self.meta_worker_playlist.moveToThread(self.meta_thread_playlist)
        self.meta_thread_playlist.started.connect(self.meta_worker_playlist.run)
        self.meta_worker_playlist.finished.connect(self.on_metadata_for_playlist)
        self.meta_worker_playlist.error.connect(self.on_metadata_error) # Can reuse error handler
        self.meta_worker_playlist.finished.connect(self.meta_thread_playlist.quit)
        self.meta_worker_playlist.finished.connect(self.meta_worker_playlist.deleteLater)
        self.meta_thread_playlist.finished.connect(self.meta_thread_playlist.deleteLater)
        self.meta_thread_playlist.start()

    def on_metadata_for_playlist(self, info):
        try:
            added_songs = []
            is_playlist = info.get('_type') == 'playlist'

            if is_playlist:
                entries = info.get('entries', [])
                for entry in entries:
                    video_id = entry.get('id', None) # Use 'id' consistently
                    song_name = entry.get('title', 'Unknown Title')
                    if video_id:
                         # Avoid duplicates
                        if not any(song['ID'] == video_id for song in self.playlist['songs']):
                            added_songs.append({'name': song_name, 'ID': video_id})
                        else:
                            print(f"Skipping duplicate (playlist): {song_name}")
                    else:
                         print(f"Skipping entry, missing ID: {song_name}")

            else:
                video_id = info.get('id', None)
                song_name = info.get('title', 'Unknown Title')
                if video_id:
                     # Avoid duplicates
                    if not any(song['ID'] == video_id for song in self.playlist['songs']):
                        added_songs.append({'name': song_name, 'ID': video_id})
                    else:
                        print(f"Skipping duplicate (single): {song_name}")
                else:
                    print("Could not add to playlist: Missing video ID")

            if added_songs:
                self.playlist["songs"].extend(added_songs)
                with open('playlist.json', 'w', encoding='utf-8') as f2:
                    json.dump(self.playlist, f2, indent=2, ensure_ascii=False)
                print(f"Added {len(added_songs)} song(s) to playlist.json")
                self.refresh_playlist() # Update the UI
            else:
                 print("No new songs added to playlist (duplicates or errors).")

            self.setWindowTitle("YouTube Audio Player") # Reset title

        except Exception as e:
            print(f"Error processing metadata for playlist: {e}")
            self.setWindowTitle("Error adding to playlist")


    def refresh_playlist(self):
        # Clear existing playlist widgets (skip the label at index 0)
        while self.playlist_box.count() > 1:
            item = self.playlist_box.takeAt(1) # Take item at index 1
            if item is None:
                continue
            layout = item.layout()
            if layout is not None:
                # Recursively delete widgets within the layout
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                # Delete the layout itself
                del layout
            elif item.widget() is not None:
                 item.widget().deleteLater() # Should not happen with current structure, but good practice

        # Re-initialize playlist UI based on the current self.playlist data
        self.init_playlist()

        # Ensure visibility matches the current state
        is_visible = self.playlist_shown
        self.playlist_label.setVisible(is_visible) # Make sure label visibility is correct
        index = self.playlist_box.count()
        while index > 1: # Iterate through the newly added items
            my_layout = self.playlist_box.itemAt(index - 1).layout()
            if my_layout:
                wid_count = my_layout.count()
                while wid_count > 0:
                    my_widget = my_layout.itemAt(wid_count - 1).widget()
                    if my_widget:
                        my_widget.setVisible(is_visible)
                    wid_count -= 1
            index -= 1


    def show_playlist(self):
        index = self.playlist_box.count()
        while index > 1:
            my_layout = self.playlist_box.itemAt(index - 1).layout()
            wid_count = my_layout.count()
            while wid_count > 0:
                my_widget = my_layout.itemAt(wid_count - 1).widget()
                my_widget.setVisible(not self.playlist_shown)
                wid_count -= 1
            index -= 1
        self.playlist_box.itemAt(0).widget().setVisible(not self.playlist_shown)
        self.playlist_shown = not self.playlist_shown

        if self.playlist_shown:
            self.show_playlist_button.setText('Hide playlist')
            self.show_playlist_button.setStyleSheet(self.normal_button_style)
        else:
            self.show_playlist_button.setText('Show playlist')
            self.show_playlist_button.setStyleSheet(self.normal_button_style)

        # Adjust window size to fit content after toggling playlist
        self.adjustSize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
