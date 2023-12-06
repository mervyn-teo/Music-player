import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
import datetime
import shutil
# coding=utf-8

def download_audio(youtube_url, output_format='mp3'):
    for fn in os.listdir("./temp"):
        os.remove(os.path.join("./temp", fn))
        print("temp file exists, deleting...")
    filename_command = f'yt-dlp -x --get-id --audio-format {output_format} {youtube_url} '
    filename = subprocess.getoutput(filename_command)
    command = f'yt-dlp -x --audio-format {output_format} {youtube_url} -o {filename}'
    subprocess.call(command, shell=True)
    shutil.move(filename + f".{output_format}", os.path.join("./temp/", filename + f".{output_format}"))
    return os.path.join("./temp/", filename + f".{output_format}")

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.player = QMediaPlayer()
        self.initUI()

    def initUI(self):
        global playing
        playing = False
        self.setWindowTitle("YouTube Audio Player")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()
        horizontal_button = QHBoxLayout()
        horizontal_slider = QHBoxLayout()

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

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 1000)
        self.slider.sliderMoved.connect(self.set_position)
        horizontal_slider.addWidget(self.slider)

        self.time_text = QLabel("00:00")
        horizontal_slider.addWidget(self.time_text)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider)

        layout.addLayout(horizontal_button)
        layout.addLayout(horizontal_slider)

    def download_and_play(self):
        global playing
        if playing:
            self.play_stop()
        url = self.url_entry.text()
        if not url:
            return
        audio_file = download_audio(url)
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
        dt = datetime.timedelta(milliseconds=duration/2)
        disp_duration = "{:0=2}".format(dt.seconds // 60) + ":" + "{:0=2}".format(dt.seconds % 60)
        if duration > 0:
            position = self.player.position()
            self.slider.setValue(int((position / duration) * 1000))
            st = datetime.timedelta(milliseconds=position/2)
            disp_runtime = "{:0=2}".format(st.seconds // 60) + ":" + "{:0=2}".format(st.seconds % 60)
            self.time_text.setText(disp_runtime + " / " + disp_duration)

    def set_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            value = position / 1000 * duration
            self.player.setPosition(int(value))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MusicPlayer()
    ex.show()
    sys.exit(app.exec_())
