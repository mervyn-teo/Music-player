import sys
import os
import subprocess
import datetime
import shutil
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

os.environ['PYTHONIOENCODING'] = 'utf-8'

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.player = QMediaPlayer()
        self.initUI()

    def initUI(self):
        self.playlist_shown = False
        self.playing = False
        self.filename = None

        # load playlist
        with open('playlist.json', 'r') as f:
            self.playlist = json.load(f)

        # Set window title
        self.setWindowTitle("YouTube Audio Player")
        self.setGeometry(300, 300, 300, 150)

        # layouts
        layout = QVBoxLayout()
        horizontal_button = QHBoxLayout()
        horizontal_slider = QHBoxLayout()
        self.playlist_box = QVBoxLayout()

        # overall layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        # URL
        self.url_entry = QLineEdit(self)
        self.url_entry.setPlaceholderText("Enter YouTube URL")
        layout.addWidget(self.url_entry)

        # Download and play button
        self.download_play_button = QPushButton("Download and Play", self)
        self.download_play_button.clicked.connect(self.download_and_play)
        horizontal_button.addWidget(self.download_play_button)

        # play/pause button
        self.play_button = QPushButton("pause", self)
        self.play_button.clicked.connect(self.play_pause)
        horizontal_button.addWidget(self.play_button)

        # add playlist button
        self.add_playlist = QPushButton("add to playlist", self)
        self.add_playlist.clicked.connect(self.add_to_playlist)
        horizontal_button.addWidget(self.add_playlist)

        # show/hide play button
        self.show_playlist_button = QPushButton("show playlist", self)
        self.show_playlist_button.clicked.connect(self.show_playlist)
        horizontal_button.addWidget(self.show_playlist_button)

        # slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.set_position)
        horizontal_slider.addWidget(self.slider)
        self.time_text = QLabel("00:00")
        horizontal_slider.addWidget(self.time_text)

        # initialise playlists
        for i in range(len(self.playlist["songs"])):
            temp = QLabel(f"{i+1}: {self.playlist['songs'][i]['name']}")
            temp.setVisible(False)
            self.playlist_box.addWidget(temp)
        layout.addLayout(self.playlist_box)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider)

        layout.addLayout(horizontal_button)
        layout.addLayout(horizontal_slider)

    def download_audio(self, youtube_url, output_format='mp3'): # TODO: separate permanent download and on-the-spot play
        # remove subfixes
        if youtube_url.find('&') >= 0:
            youtube_url = youtube_url[:youtube_url.index('&')]
        print(youtube_url)

        for fn in os.listdir("./temp"):
            os.remove(os.path.join("./temp", fn))
            print("temp file exists, deleting...")

        self.filename = subprocess.Popen(['yt-dlp', '-x', '--get-id', 'audio-format', output_format, youtube_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        filename_out, filename_err = self.filename.communicate()
        self.filename = filename_out.decode('utf-8').strip()
        print(f"file name: {self.filename}")

        self.song_name = subprocess.Popen(['yt-dlp', '-x', '--print', 'filename', 'audio-format', output_format, youtube_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        songname_out, songname_err = self.song_name.communicate()
        self.song_name = songname_out.decode('utf-8').strip()
        print(f"song name: {self.song_name}")

        command = f"yt-dlp -x --audio-format {output_format} {youtube_url} -o {self.filename}"
        subprocess.call(command, shell=True)
        print("here")
        shutil.move(self.filename + f".{output_format}", os.path.join("./temp/", self.filename + f".{output_format}"))
        return os.path.join("./temp/", self.filename + f".{output_format}")

    def download_and_play(self):
        if self.playing:
            self.play_stop()
        url = self.url_entry.text()
        if not url:
            return
        audio_file = self.download_audio(url)
        self.playing = True
        self.play_button.setText("pause")
        self.play_music(audio_file)

    def play_music(self, file_path):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.player.play()
        self.player.setVolume(30)
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
            self.playing = not self.playing
        else:
            self.player.play()
            self.play_button.setText("pause")
            self.playing = not self.playing

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

    def set_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            value = position / 1000 * duration
            self.player.setPosition(int(value))

    def add_to_playlist(self):
        global added_in_playlist

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
                temp = QLabel(f"{self.playlist_box.count()+1}: {self.song_name}")
                self.playlist_box.addWidget(temp)
                with open('playlist.json', 'w') as f2:
                    json.dump(self.playlist, f2)
                print(self.playlist)
        else:
            print("nothing for me to add bruh")


    def show_playlist(self):
        index = self.playlist_box.count()
        while (index > 0):
            my_widget = self.playlist_box.itemAt(index-1).widget()
            my_widget.setVisible(not self.playlist_shown)
            index -= 1
        self.playlist_shown = not self.playlist_shown
        if self.playlist_shown:
            self.show_playlist_button.setText('Hide playlist')
        else:
            self.show_playlist_button.setText('Show playlist')





if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
