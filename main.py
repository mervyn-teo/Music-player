import sys
import os
import datetime
import json
from yt_dlp import YoutubeDL  # yt-dlp docs: https://github.com/yt-dlp/yt-dlp/blob/c54ddfba0f7d68034339426223d75373c5fc86df/yt_dlp/YoutubeDL.py#L457
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *


class Worker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)

    def __init__(self, url, mode="download_and_play"):
        super().__init__()
        self.url = url
        self.mode = mode

    def run(self):
        result = None
        try:
            if self.mode == "download_and_play":
                result = self._download_and_play()
            elif self.mode == "download_audio":
                result = self._download_audio()
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
        self.finished.emit(result)

    def _download_and_play(self):
        youtube_dl_opts = {}
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            is_playlist = info_dict.get('_type', None) == 'playlist'
            if is_playlist:
                playlist = []
                for entry in info_dict['entries']:
                    playlist.append({'name': entry.get('fulltitle', ''), 'ID': entry.get('display_id', '')})
                return {'is_playlist': True, 'playlist': playlist, 'info_dict': info_dict}
            else:
                return {'is_playlist': False, 'info_dict': info_dict}

    def _download_audio(self):
        ydl_opts = {'outtmpl': f'./temp/%(id)s.%(ext)s', 'format': 'bestaudio', 'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3'
        }]}
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        return None


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.threads = []  # Track running threads
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

    def closeEvent(self, event):
        # Gracefully stop all running threads
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait()
        event.accept()

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

            def after_download():
                audio_file = f'./temp/{ID}.mp3'
                self.play_music(audio_file)
                self.queue.insert(0, {"name": f"{self.song_name}", "ID": f"{self.filename}"})
                self.refresh_queue()

            thread = QThread()
            worker = Worker(ID, mode="download_audio")
            worker.moveToThread(thread)
            thread.started.connect(worker.run)
            worker.finished.connect(lambda _: after_download())
            worker.progress.connect(self._on_worker_progress)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.start()
            self.threads.append(thread)

        return ret_func

    def get_song_file_name(self, youtube_url):
        youtube_dl_opts = {}
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            ext = info_dict.get("ext", None)
            filename = info_dict.get("id", None)
            song_name = info_dict.get('title', None)
            is_playlist = info_dict.get('_type', None) == 'playlist'
            print(filename)
            return song_name, filename, ext, is_playlist, info_dict

    def download_audio(self, youtube_url):  # TODO: separate permanent download and on-the-spot play
        # remove suffixes
        if youtube_url.find('&') >= 0:
            youtube_url = youtube_url[:youtube_url.index('&')]
        print(youtube_url)

        # read temp folder
        self.setWindowTitle("Loading music...")
        for fn in os.listdir("./temp"):
            os.remove(os.path.join("./temp", fn))
            print("temp file exists, deleting...")
        res = self.get_song_file_name(youtube_url)

        self.song_name = res[0]
        self.filename = res[1]
        self.ext = res[2]
        self.is_playlist = res[3]
        if self.is_playlist:
            self.add_url_to_queue()
            self.play_pause()
        else:
            print(f"file name: {self.filename}")
            print(f"song name: {self.song_name}")

            try:
                self.download_only(self.filename)
            except Exception as e:
                print(f"Download error: {e}")
            # return os.path.join("./temp/", self.filename + ".mp3")

    def download_only(self, ID):
        ydl_opts = {'outtmpl': f'./temp/{ID}.%(ext)s', 'format': 'bestaudio', 'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3'
        }]}
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([ID])
        except Exception as e:
            print(f"Download error: {e}")
        # return os.path.join(f"./temp/{ID}.mp3")

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

        self.thread = QThread()
        self.worker = Worker(url, mode="download_and_play")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_download_finished)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.threads.append(self.thread)

    def _on_worker_progress(self, message):
        self.setWindowTitle(message)

    def _on_download_finished(self, result):
        if result is None:
            self.setWindowTitle("Download failed")
            return

        if result.get('is_playlist'):
            playlist = result.get('playlist', [])
            self.queue.extend(playlist)
            self.refresh_queue()
            self.play_pause()
        else:
            info_dict = result.get('info_dict')
            audio_file = os.path.join(f"./temp/{info_dict['id']}.mp3")
            # download audio in background thread
            self._download_audio_async(info_dict['webpage_url'], audio_file, info_dict)
    
    def _download_audio_async(self, url, audio_file, info_dict):
        self.thread2 = QThread()
        self.worker2 = Worker(url, mode="download_audio")
        self.worker2.moveToThread(self.thread2)
        self.thread2.started.connect(self.worker2.run)
        self.worker2.finished.connect(lambda _: self._on_audio_downloaded(audio_file, info_dict))
        self.worker2.progress.connect(self._on_worker_progress)
        self.worker2.finished.connect(self.thread2.quit)
        self.worker2.finished.connect(self.worker2.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        self.thread2.start()
        self.threads.append(self.thread2)

    def _on_audio_downloaded(self, audio_file, info_dict):
        self.song_name = info_dict.get('title', '')
        self.filename = info_dict.get('id', '')
        self.playing = True
        self.play_button.setIcon(self.pause_icon)
        self.play_music(audio_file)
        self.buffer_next()
        self.queue.insert(0, {"name": self.song_name, "ID": self.filename})
        self.refresh_queue()

    def refresh_queue(self):
        count = self.queue_box.count()
        for i in reversed(range(count)):
            item = self.queue_box.itemAt(i)
            widget = item.widget()
            if widget is not None and widget != self.queue_label:
                widget.setParent(None)

        for idx, song in enumerate(self.queue):
            label = QLabel(f"{idx + 1}: {song['name']}")
            if idx == 0:
                label.setStyleSheet(self.highlight_text_style)
            else:
                label.setStyleSheet(self.text_style)
            self.queue_box.addWidget(label)

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
        # Remove all playlist items except the label at index 0
        count = self.playlist_box.count()
        for i in reversed(range(1, count)):
            item = self.playlist_box.itemAt(i)
            layout = item.layout()
            if layout is not None:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
                self.playlist_box.removeItem(layout)

        # Rebuild playlist entries
        for idx, song in enumerate(self.playlist.get("songs", [])):
            temp_box = QHBoxLayout()
            btn = QPushButton(f"{idx + 1}: {song['name']}")
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet(self.playlist_list_style)
            btn.clicked.connect(self.play_from_playlist(song['ID']))

            up_btn = QPushButton('↑')
            down_btn = QPushButton('↓')
            up_btn.setStyleSheet(self.playlist_up_down_style)
            down_btn.setStyleSheet(self.playlist_up_down_style)
            up_btn.clicked.connect(self.rank_up(idx))
            down_btn.clicked.connect(self.rank_down(idx))

            temp_box.addWidget(up_btn)
            temp_box.addWidget(down_btn)
            temp_box.addWidget(btn, Qt.AlignLeft)
            self.playlist_box.addLayout(temp_box)

            # Set visibility based on current toggle state
            visible = self.playlist_shown
            btn.setVisible(visible)
            up_btn.setVisible(visible)
            down_btn.setVisible(visible)

    def show_playlist(self):
        index = self.playlist_box.count()
        while index > 1:
            layout = self.playlist_box.itemAt(index - 1).layout()
            if layout is not None:
                for j in range(layout.count()):
                    widget = layout.itemAt(j).widget()
                    if widget:
                        widget.setVisible(not self.playlist_shown)
            index -= 1

        # toggle label visibility
        label_widget = self.playlist_box.itemAt(0).widget()
        if label_widget:
            label_widget.setVisible(not self.playlist_shown)

        self.playlist_shown = not self.playlist_shown

        if self.playlist_shown:
            self.show_playlist_button.setText('Hide playlist')
        else:
            self.show_playlist_button.setText('Show playlist')
        self.show_playlist_button.setStyleSheet(self.normal_button_style)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
