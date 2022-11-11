import os
import sys
import urllib.request as request

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class DownloadDialog(qtw.QDialog):
    finished = qtc.pyqtSignal()

    def __init__(
        self, url: str, output_directory: os.PathLike, file_name: str, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.output_directory = output_directory
        self.file_name = file_name

        self.init_UI()

    def init_UI(self):
        self.progress_bar = qtw.QProgressBar()
        self.progress_bar.setGeometry(25, 45, 210, 30)

        self.stop_button = qtw.QPushButton("STOP Download")
        self.stop_button.clicked.connect(self.download)

        self.layout = qtw.QVBoxLayout(self)

        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.stop_button)

    def stop_download(self):
        pass

    def download(self):
        try:
            out_path = os.path.join(self.output_directory, self.file_name)
            request.urlretrieve(self.url, out_path, self.handle_progress)
        except Exception as e:
            print(repr(e))
            print(e.args)

    def handle_progress(self, blocknum, blocksize, totalsize):
        read_data = blocknum * blocksize

        if totalsize > 0:
            download_percentage = read_data * 100 / totalsize
            print(download_percentage)
            self.progress_bar.setValue(download_percentage)
            qtw.QApplication.processEvents()


import requests

file_url = "http://codex.cs.yale.edu/avi/db-book/db4/slide-dir/ch1-2.pdf"

r = requests.get(file_url, stream=True)

with open("python.pdf", "wb") as pdf:
    for chunk in r.iter_content(chunk_size=1024):

        # writing one chunk at a time to pdf file
        if chunk:
            pdf.write(chunk)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)

    url_ = "https://speed.hetzner.de/100MB.bin"
    out_dir_ = r"C:\Users\Raphael\Desktop\download_test"
    out_filename_ = "test"

    dialog = DownloadDialog(url_, out_dir_, out_filename_)
    dialog.open()
    # dialog.download()

    sys.exit(app.exec())
