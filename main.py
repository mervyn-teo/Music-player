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

    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.clearFocus()
        QMainWindow.mousePressEvent(self, event)

    def init_playlist(self):
        if len(self.playlist["songs"]) > 0:
            for i in range(len(self.playlist["songs"])):
                temp_box = QHBoxLayout()
                temp = QPushButton()

                # playlist titles
                temp.setFocusPolicy(Qt.NoFocus)
                f = self.play_from_playlist(self.playlist['songs'][i]['ID'])
                temp.clicked.connect(f)
                temp.setText(f"{i + 1}: {self.playlist['songs'][i]['name']}")
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
                up.setVisible(False)
                down.setVisible(False)

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

    def add_yt_playlist(self):
        youtube_url = self.url_entry.text()
        youtube_dl_opts = {}
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            print(info_dict)
            length = len(info_dict['entries'])
            playlist = []
            for i in range(length):
                temp = {'name': info_dict['entries'][i].get('fulltitle', None), 'ID': info_dict['entries'][i].get("display_id", None)}
                playlist.append(temp)
            return playlist

    def play_from_playlist(self, ID):
        def ret_func():
            print(ID)
            self.play_music(self.download_audio(ID))
            self.queue.insert(0, {"name": f"{self.song_name}", "ID": f"{self.filename}"})
            self.refresh_queue()

        return ret_func

    # get_song_file_name is now async, handled by MetadataWorker

    def download_audio(self, youtube_url):
        # remove suffixes
        if '&' in youtube_url:
            youtube_url = youtube_url.split('&')[0]

        self.setWindowTitle("Loading music...")

        # Clean temp folder safely
        try:
            for fn in os.listdir("./temp"):
                path = os.path.join("./temp", fn)
                if os.path.isfile(path):
                    os.remove(path)
        except Exception as e:
            print(f"Error cleaning temp: {e}")

        # Start metadata extraction in background
        self.meta_thread = QThread()
        self.meta_worker = MetadataWorker(youtube_url)
        self.meta_worker.moveToThread(self.meta_thread)
        self.meta_thread.started.connect(self.meta_worker.run)
        self.meta_worker.finished.connect(self.on_metadata_ready)
        self.meta_worker.error.connect(self.on_metadata_error)
        self.meta_worker.finished.connect(self.meta_thread.quit)
        self.meta_worker.finished.connect(self.meta_worker.deleteLater)
        self.meta_thread.finished.connect(self.meta_thread.deleteLater)
        self.meta_thread.start()

    def on_metadata_ready(self, info):
        try:
            self.song_name = info.get('title', '')
            self.filename = info.get('id', '')
            self.ext = info.get('ext', 'mp3')
            self.is_playlist = info.get('_type') == 'playlist'
            self.info_dict = info

            if self.is_playlist:
                self.add_url_to_queue()
                self.play_pause()
            else:
                print(f"file name: {self.filename}")
                print(f"song name: {self.song_name}")
                self.download_audio_file(self.filename)
        except Exception as e:
            print(f"Metadata processing error: {e}")
            self.setWindowTitle("Error loading metadata")

    def on_metadata_error(self, error_msg):
        print(f"Metadata error: {error_msg}")
        self.setWindowTitle("Error loading metadata")

    def download_audio_file(self, video_id):
        self.dl_thread = QThread()
        self.dl_worker = DownloadWorker(video_id)
        self.dl_worker.moveToThread(self.dl_thread)
        self.dl_thread.started.connect(self.dl_worker.run)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.error.connect(self.on_download_error)
        self.dl_worker.finished.connect(self.dl_thread.quit)
        self.dl_worker.finished.connect(self.dl_worker.deleteLater)
        self.dl_thread.finished.connect(self.dl_thread.deleteLater)
        self.dl_thread.start()

    def on_download_finished(self, video_id):
        audio_file = os.path.join("./temp", f"{video_id}.mp3")
        self.play_music(audio_file)

    def on_download_error(self, error_msg):
        print(f"Download error: {error_msg}")
        self.setWindowTitle("Error downloading audio")

    def download_only(self, ID):
        # Use background worker instead
        self.download_audio_file(ID)

    def keyPressEvent(self, event):  # keypress detection
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
        self.setWindowTitle("Loading...")
        if self.playing:
            self.play_stop()
        url = self.url_entry.text()
        if not url:
            self.setWindowTitle("YouTube Audio Player")
            return

        # Start metadata extraction in background
        self.meta_thread = QThread()
        self.meta_worker = MetadataWorker(url)
        self.meta_worker.moveToThread(self.meta_thread)
        self.meta_thread.started.connect(self.meta_worker.run)
        self.meta_worker.finished.connect(self.on_download_and_play_metadata_ready)
        self.meta_worker.error.connect(self.on_metadata_error)
        self.meta_worker.finished.connect(self.meta_thread.quit)
        self.meta_worker.finished.connect(self.meta_worker.deleteLater)
        self.meta_thread.finished.connect(self.meta_thread.deleteLater)
        self.meta_thread.start()

    def on_download_and_play_metadata_ready(self, info):
        try:
            is_playlist = info.get('_type') == 'playlist'
            if is_playlist:
                entries = info.get('entries', [])
                playlist = []
                for entry in entries:
                    playlist.append({
                        'name': entry.get('fulltitle', ''),
                        'ID': entry.get('display_id', '')
                    })
                self.queue.extend(playlist)
                self.refresh_queue()
                self.play_pause()
            else:
                video_id = info.get('id', '')
                self.song_name = info.get('title', '')
                self.filename = video_id
                self.download_audio_file(video_id)
                self.queue.insert(0, {"name": self.song_name, "ID": video_id})
                self.refresh_queue()
        except Exception as e:
            print(f"Error processing metadata: {e}")
            self.setWindowTitle("Error loading metadata")

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

    def play_music(self, file_path):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.player.play()
        self.volume_slider.setSliderPosition(self.volume)
        self.playing = True
        self.setWindowTitle(f"Now playing: {self.queue[0]['name']}")
        self.buffer_next()
        self.timer.start()

    def play_stop(self):
        if self.playing:
            self.player.stop()
            self.playing = False
            self.play_button.setText("play")

    def play_pause(self):
        if self.playing:
            self.player.pause()
            self.play_button.setIcon(self.play_icon)
            self.playing = False
            self.play_button.setStyleSheet(self.play_style)
        elif len(self.queue) > 0:
            if self.player.state() == 0:
                audio_file = f'./temp/{self.queue[0]["ID"]}.mp3'
                self.download_audio(self.queue[0]["ID"])
                self.playing = True
                self.play_button.setIcon(self.pause_icon)
                self.play_music(audio_file)
                print(f"queue dict: {self.queue}")
                self.refresh_queue()
            else:
                self.player.play()
                self.play_button.setIcon(self.pause_icon)
                self.playing = True
                self.play_button.setStyleSheet(self.pause_style)

    def add_playlist_to_queue(self):
        print(self.playlist['songs'])
        self.queue = self.queue + self.playlist['songs']
        self.refresh_queue()

    def add_url_to_queue(self):
        if self.url_entry.text():
            res = self.get_song_file_name(self.url_entry.text())
            is_playlist = res[3]
            if is_playlist:
                info_dict = res[4]
                length = len(info_dict['entries'])
                playlist = []
                for i in range(length):
                    temp = {'name': info_dict['entries'][i].get('fulltitle', None), 'ID': info_dict['entries'][i].get("display_id", None)}
                    playlist.append(temp)
                self.queue = self.queue + playlist
                self.refresh_queue()
            else:
                self.queue.append(
                    {"name": res[0], "ID": res[1]})
                self.refresh_queue()

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
        if self.player.state() != 0:
            self.player.stop()
        if len(self.queue) > 0:
            if self.next_song_downloaded:
                audio_file = self.next_song_filename
            else:
                audio_file = f'./temp/{self.queue[1]["ID"]}.mp3'
                self.download_audio(self.queue[1]["ID"])
            del self.queue[0]
            self.play_music(audio_file)
            self.playing = True
            self.play_button.setIcon(self.pause_icon)
            print(f"queue dict: {self.queue}")
            self.buffer_next()
        self.refresh_queue()

    def buffer_next(self):
        if self.buffer_option:
            if len(self.queue) > 1:
                self.next_song_filename = os.path.join(f"./temp/{self.queue[1]['ID']}.mp3")
                self.download_only(self.queue[1]['ID'])
                self.next_song_downloaded = True

    def set_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            value = position / 1000 * duration
            self.player.setPosition(int(value))

    def add_to_playlist(self):
        global added_in_playlist
        self.setWindowTitle("checking...")
        res = self.get_song_file_name(self.url_entry.text())
        is_playlist = res[3]
        info_dict = res[4]
        if is_playlist:
            length = len(info_dict['entries'])
            yt_playlist = []
            for i in range(length):
                temp = {'name': info_dict['entries'][i].get('fulltitle', None), 'ID': info_dict['entries'][i].get("display_id", None)}
                yt_playlist.append(temp)
            self.playlist["songs"] = self.playlist["songs"] + yt_playlist
            with open('playlist.json', 'w') as f2:
                json.dump(self.playlist, f2, indent=2)
            print(self.playlist)
            self.refresh_playlist()
            if self.playing:
                self.setWindowTitle(f"Now playing: self.queue[0]")
            else:
                self.setWindowTitle('YouTube Audio Player')
        else:
            if self.url_entry is not None:
                self.setWindowTitle(f"adding {self.song_name} ...")
                self.playlist["songs"].append({"name": self.song_name, "ID": self.filename})
                temp = QLabel(f"{self.playlist_box.count() + 1}: {self.song_name}")
                self.playlist_box.addWidget(temp)
                temp.setStyleSheet(self.text_style)
                with open('playlist.json', 'w') as f2:
                    json.dump(self.playlist, f2, indent=2)
                if self.playing:
                    self.setWindowTitle(f"Now playing: {self.song_name}")
                else:
                    self.setWindowTitle('YouTube Audio Player')
            else:
                print("nothing for me to add bruh")

    def refresh_playlist(self):

        r = self.playlist_box.count()
        if r > 1:
            for i in reversed(range(1, r)):
                temp = self.playlist_box.itemAt(i).layout()
                self.playlist_box.removeItem(temp)
        print("here")
        for i in range(len(self.playlist)):
            self.init_playlist()
            if self.playlist_shown:
                self.show_playlist()
                self.show_playlist()
            else:
                self.show_playlist()

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
