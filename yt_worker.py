import os
import json
from yt_dlp import YoutubeDL
from PyQt5.QtCore import QObject, pyqtSignal

class MetadataWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            opts = {}
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url_or_id, outdir="./temp"):
        super().__init__()
        self.url_or_id = url_or_id
        self.outdir = outdir

    def run(self):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.outdir, '%(id)s.%(ext)s'),
                'format': 'bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp3'
                }]
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url_or_id])
            self.finished.emit(self.url_or_id)
        except Exception as e:
            self.error.emit(str(e))
