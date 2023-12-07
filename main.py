# coding=utf-8
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
import datetime
import shutil
import json


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.player = QMediaPlayer()
        self.initUI()

    def initUI(self): # TODO: add another window to display playlist
        global playing
        global filename
        playing = False
        filename = None

        with open('playlist.json', 'r') as f: # load playlist
            global playlist
            playlist = json.load(f)


        self.setWindowTitle("YouTube Audio Player")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()
        horizontal_button = QHBoxLayout()
        horizontal_slider = QHBoxLayout()
        playlist_box = QVBoxLayout()

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(layout)

        self.url_entry = QLineEdit(self)
        self.url_entry.setPlaceholderText("Enter YouTube URL")
        layout.addWidget(self.url_entry)

        self.download_play_button = QPushButton("Download and Play", self)
        self.download_play_button.clicked.connect(self.download_and_play)
        horizontal_button.addWidget(self.download_play_button)

        self.play_button = QPushButton("pause", self)
        self.play_button.clicked.connect(self.play_pause)
        horizontal_button.addWidget(self.play_button)

        self.add_playlist = QPushButton("add to playlist", self)
        self.add_playlist.clicked.connect(self.add_to_playlist)
        horizontal_button.addWidget(self.add_playlist)

        # self.show_playlist_button = QPushButton("show playlist", self)
        # self.show_playlist_button.clicked.connect(self.show_playlist)
        # horizontal_button.addWidget(self.show_playlist_button)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.set_position)
        horizontal_slider.addWidget(self.slider)

        self.time_text = QLabel("00:00")
        horizontal_slider.addWidget(self.time_text)

        for i in range(len(playlist["songs"])):
            temp = QLabel(f"{i+1}: {playlist['songs'][i]['name']}")
            playlist_box.addWidget(temp)
        layout.addLayout(playlist_box)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider)

        layout.addLayout(horizontal_button)
        layout.addLayout(horizontal_slider)

    def download_audio(self, youtube_url, output_format='mp3'): # TODO: separate permanent download and on-the-spot play
        global filename
        global song_name
        for fn in os.listdir("./temp"):
            os.remove(os.path.join("./temp", fn))
            print("temp file exists, deleting...")
        filename_command = f'yt-dlp -x --get-id --audio-format {output_format} {youtube_url} '
        song_name_command = f'yt-dlp -x --print filename --audio-format {output_format} {youtube_url} '
        filename = subprocess.getoutput(filename_command)
        print(f"filname: {filename}")
        song_name = subprocess.getoutput(song_name_command)
        print(f"songname: {song_name}") # TODO: make this compatible with non english characters
        command = f'yt-dlp -x --audio-format {output_format} {youtube_url} -o {filename}'
        subprocess.call(command, shell=True)
        shutil.move(filename + f".{output_format}", os.path.join("./temp/", filename + f".{output_format}"))
        return os.path.join("./temp/", filename + f".{output_format}")

    def download_and_play(self):
        global playing
        if playing:
            self.play_stop()
        url = self.url_entry.text()
        if not url:
            return
        audio_file = self.download_audio(url)
        playing = True
        self.play_button.setText("pause")
        self.play_music(audio_file)

    def play_music(self, file_path):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.player.play()
        self.player.setVolume(30)
        self.timer.start()

    def play_stop(self):
        global playing
        if playing:
            self.player.stop()
            playing = False
            self.play_button.setText("play")

    def play_pause(self):
        global playing
        if playing:
            self.player.pause()
            self.play_button.setText("play")
            playing = not playing
        else:
            self.player.play()
            self.play_button.setText("pause")
            playing = not playing

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
        global filename
        global song_name
        global added_in_playlist
        global playlist

        if filename is not None:
            added_in_playlist = False
            for i in playlist["songs"]:
                if i["ID"] == filename:
                    print("already added in playlist")
                    added_in_playlist = True
                    break
            if not added_in_playlist:
                print(f"{song_name} is not in playlist, adding...")
                playlist["songs"].append({"name": song_name, "ID": filename})
                with open('playlist.json', 'w') as f2:
                    json.dump(playlist, f2)
                print(playlist)
        else:
            print("nothing for me to add bruh")

    # def show_playlist(self):





if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
