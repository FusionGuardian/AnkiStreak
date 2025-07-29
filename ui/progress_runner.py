from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import QThread, pyqtSignal, Qt

class ProgressThread(QThread):
    finished = pyqtSignal()

    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.target(*self.args, **self.kwargs)
        self.finished.emit()

class ProgressRunner:
    _instance = None

    def __new__(cls, mw=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.mw = mw or mw  # mw global do Anki
        return cls._instance

    def run_with_progress(self, title, target, on_finish=None, *args, **kwargs):
        progress = QProgressDialog(title, None, 0, 0, self.mw)
        progress.setWindowTitle("AnkiStreak")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.setAutoClose(True)
        progress.show()
        QApplication.processEvents()

        worker = ProgressThread(target, *args, **kwargs)
        worker.finished.connect(progress.close)
        if on_finish:
            worker.finished.connect(on_finish)
        worker.start()
        self._thread = worker