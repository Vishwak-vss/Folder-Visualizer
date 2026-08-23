import os
from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, target_dir):
        super().__init__()
        self.target_dir = target_dir

    def run(self):
        result = self.scan_directory(self.target_dir)
        self.finished.emit(result)

    def scan_directory(self, path):
        total_size = 0
        children = []

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    self.progress.emit(f"Scanning: {entry.path}")
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat(follow_symlinks=False).st_size
                            children.append({
                                'name': entry.name,
                                'path': entry.path,
                                'size': size,
                                'is_dir': False
                            })
                            total_size += size
                        elif entry.is_dir(follow_symlinks=False):
                            dir_size = self.get_quick_dir_size(entry.path)
                            children.append({
                                'name': entry.name,
                                'path': entry.path,
                                'size': dir_size,
                                'is_dir': True
                            })
                            total_size += dir_size
                    except PermissionError:
                        continue
        except PermissionError:
            pass

        return {
            'name': os.path.basename(path) or path,
            'path': path,
            'size': total_size,
            'children': children
        }

    def get_quick_dir_size(self, path):
        size = 0
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size += entry.stat(follow_symlinks=False).st_size
                    except PermissionError:
                        continue
        except PermissionError:
            pass
        return size