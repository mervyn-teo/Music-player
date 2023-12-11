import sys
import os
import datetime
import shutil
import json
from yt_dlp import YoutubeDL # yt-dlp docs: https://github.com/yt-dlp/yt-dlp/blob/c54ddfba0f7d68034339426223d75373c5fc86df/yt_dlp/YoutubeDL.py#L457
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *


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
                json.dump({"songs": []}, temp)
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
        self.download_play_button = QPushButton("Download and Play", self)
        self.download_play_button.setStyleSheet(self.normal_button_style)
        self.download_play_button.clicked.connect(self.download_and_play)
        horizontal_button.addWidget(self.download_play_button)

        # play/pause button
        self.play_button = QPushButton("pause", self)
        self.play_button.setStyleSheet(self.pause_style)
        self.play_button.clicked.connect(self.play_pause)
        horizontal_button.addWidget(self.play_button)

        # next song button
        self.next_song_button = QPushButton("next", self)
        self.next_song_button.setStyleSheet(self.normal_button_style)
        self.next_song_button.clicked.connect(self.next_song)
        horizontal_button.addWidget(self.next_song_button)

        # add playlist button
        self.add_playlist_button = QPushButton("add to playlist", self)
        self.add_playlist_button.setStyleSheet(self.normal_button_style)
        self.add_playlist_button.clicked.connect(self.add_to_playlist)
        horizontal_button.addWidget(self.add_playlist_button)

        # show/hide play button
        self.show_playlist_button = QPushButton("show playlist", self)
        self.show_playlist_button.setStyleSheet(self.normal_button_style)
        self.show_playlist_button.clicked.connect(self.show_playlist)
        horizontal_button.addWidget(self.show_playlist_button)

        # add song to queue
        self.add_url_to_queue_button = QPushButton("add to queue", self)
        self.add_url_to_queue_button.setStyleSheet(self.normal_button_style)
        self.add_url_to_queue_button.clicked.connect(self.add_url_to_queue)
        horizontal_button.addWidget(self.add_url_to_queue_button)

        # add playlist to song
        self.add_playlist_to_queue_button = QPushButton("add playlist to queue", self)
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
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0,100)
        self.volume_slider.setStyleSheet(self.volume_slider_style)
        self.volume_slider.sliderMoved.connect(self.volume_adjust)

        self.volume_text = QLabel('Volume:')
        self.volume_text.setStyleSheet(self.text_style)
        horizontal_slider.addWidget(self.volume_text)
        horizontal_slider.addWidget(self.volume_slider)
    def init_playlist(self):
        if len(self.playlist["songs"]) > 0:
            for i in range(len(self.playlist["songs"])):
                temp = QPushButton()
                f = self.play_from_playlist(self.playlist['songs'][i]['ID'])
                temp.clicked.connect(f)
                temp.setText(f"{i + 1}: {self.playlist['songs'][i]['name']}")
                temp.setVisible(False)
                temp.setStyleSheet(self.playlist_list_style)
                self.playlist_box.addWidget(temp)

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
                temp = {'name': '', 'ID': ''}
                temp['ID'] = info_dict['entries'][i].get("display_id", None)
                temp['name'] = info_dict['entries'][i].get('fulltitle', None)
                playlist.append(temp)
            return playlist

    def play_from_playlist(self, ID):
        def ret_func():
            print(ID)
            self.play_music(self.download_audio(ID))
            self.queue.insert(0, {"name": f"{self.song_name}", "ID": f"{self.filename}"})
            self.refresh_queue()
        return ret_func

    def get_song_file_name(self, youtube_url, output_format="mp3"):
        youtube_dl_opts = {}
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            ext = info_dict.get("ext", None)
            filename = info_dict.get("id", None)
            song_name = info_dict.get('title', None)
            is_playlist = info_dict.get('_type', None) == 'playlist'
            print(filename)
            return song_name, filename, ext, is_playlist, info_dict

    def download_audio(self, youtube_url,
                       output_format='mp3'):  # TODO: separate permanent download and on-the-spot play
        # remove suffixes
        if youtube_url.find('&') >= 0:
            youtube_url = youtube_url[:youtube_url.index('&')]
        print(youtube_url)

        #read temp folder
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

            ydl_opts = {'outtmpl': f'{self.filename}.%(ext)s', 'format': 'bestaudio', 'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp3'
            }]}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(youtube_url)
            shutil.move(self.filename + ".mp3", os.path.join("./temp/", self.filename + ".mp3"))
            return os.path.join("./temp/", self.filename + ".mp3")

    def download_and_play(self):
        self.setWindowTitle("Loading...")
        if self.playing:
            self.play_stop()
        url = self.url_entry.text()
        if not url:
            return

        res = self.get_song_file_name(url)
        is_playlist = res[3]
        info_dict = res[4]

        if is_playlist:
            length = len(info_dict['entries'])
            playlist = []
            for i in range(length):
                temp = {'name': '', 'ID': ''}
                temp['ID'] = info_dict['entries'][i].get("display_id", None)
                temp['name'] = info_dict['entries'][i].get('fulltitle', None)
                playlist.append(temp)
            self.queue = self.queue + playlist
            self.refresh_queue()
            self.play_pause()
        else:
            audio_file = self.download_audio(url)
            self.playing = True
            self.play_button.setText("pause")
            self.play_music(audio_file)
            self.queue.insert(0, {"name": f"{self.song_name}", "ID": f"{self.filename}"})
            self.refresh_queue()

    def refresh_queue(self):
        r = self.queue_box.count()
        if r > 0:
            for i in reversed(range(r)):
                temp = self.queue_box.itemAt(i).widget()
                if temp != self.queue_label:
                    print(i)
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
        self.volume = 30
        self.player.setVolume(self.volume)
        self.volume_slider.setSliderPosition(self.volume)
        self.playing = True
        self.setWindowTitle(f"Now playing: {self.song_name}")
        self.timer.start()

    def play_stop(self):
        if self.playing:
            self.player.stop()
            self.playing = False
            self.play_button.setText("play")

    def play_pause(self):
        if self.playing:
            self.player.pause()
            self.play_button.setText("play")
            self.playing = False
            self.play_button.setStyleSheet(self.play_style)
        elif len(self.queue) > 0:
            if self.player.state() == 0:
                audio_file = self.download_audio(self.queue[0]["ID"])
                self.playing = True
                self.play_button.setText("pause")
                self.play_music(audio_file)
                print(f"queue dict: {self.queue}")
                self.refresh_queue()
            else:
                self.player.play()
                self.play_button.setText("pause")
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
                    temp = {'name': '', 'ID': ''}
                    temp['ID'] = info_dict['entries'][i].get("display_id", None)
                    temp['name'] = info_dict['entries'][i].get('fulltitle', None)
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
            del self.queue[0]
            audio_file = self.download_audio(self.queue[0]["ID"])
            self.playing = True
            self.play_button.setText("pause")
            self.play_music(audio_file)
            print(f"queue dict: {self.queue}")
        self.refresh_queue()

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
                temp = {'name': '', 'ID': ''}
                temp['ID'] = info_dict['entries'][i].get("display_id", None)
                temp['name'] = info_dict['entries'][i].get('fulltitle', None)
                yt_playlist.append(temp)
            self.playlist["songs"] = self.playlist["songs"] + yt_playlist
            with open('playlist.json', 'w') as f2:
                json.dump(self.playlist, f2)
            print(self.playlist)
            self.refresh_playlist()
            if self.playing:
                self.setWindowTitle(f"Now playing: self.queue[0]")
            else:
                self.setWindowTitle('YouTube Audio Player')
        else:
            if self.filename is not None:
                added_in_playlist = False
                for i in self.playlist["songs"]:
                    if i["ID"] == self.filename:
                        print("already added in playlist")
                        added_in_playlist = True
                        break
                if not added_in_playlist:
                    print(f"{self.song_name} is not in playlist, adding...")
                    self.playlist["songs"].append({"name": self.song_name, "ID": self.filename})
                    temp = QLabel(f"{self.playlist_box.count() + 1}: {self.song_name}")
                    self.playlist_box.addWidget(temp)
                    temp.setStyleSheet(self.text_style)
                    with open('playlist.json', 'w') as f2:
                        json.dump(self.playlist, f2)
                    print(self.playlist)
            else:
                print("nothing for me to add bruh")

    def refresh_playlist(self):

        r = self.playlist_box.count()
        if r > 0:
            for i in reversed(range(r)):
                temp = self.playlist_box.itemAt(i).widget()
                if temp != self.playlist_label:
                    self.playlist_box.removeWidget(temp)
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
        while (index > 0):
            my_widget = self.playlist_box.itemAt(index - 1).widget()
            my_widget.setVisible(not self.playlist_shown)
            index -= 1
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
