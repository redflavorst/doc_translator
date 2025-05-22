from threading import Lock


class ProgressManager:
    def __init__(self):
        self._progress = {}
        self._lock = Lock()

    def start(self, path: str):
        with self._lock:
            self._progress[path] = 'running'

    def finish(self, path: str):
        with self._lock:
            self._progress[path] = 'done'

    def get(self, path: str):
        with self._lock:
            return self._progress.get(path)

    def all(self):
        with self._lock:
            return dict(self._progress)

progress_manager = ProgressManager()
