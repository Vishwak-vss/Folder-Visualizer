import os
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    """Multi-threaded background scanner for rapid directory size calculations."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path

    def run(self):
        result = self.scan_single_level(self.root_path)
        self.finished.emit(result)

    def scan_single_level(self, path: str) -> dict:
        self.progress.emit(f"Scanning: {path}")

        node = {
            'name': os.path.basename(path) or path,
            'path': path,
            'size': 0,
            'is_dir': True,
            'children': [],
            'scanned': True
        }

        try:
            entries = list(os.scandir(path))
        except (PermissionError, OSError):
            return node

        dirs_to_scan = []

        # Process immediate files first
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue

                if entry.is_dir(follow_symlinks=False):
                    dirs_to_scan.append(entry)
                elif entry.is_file(follow_symlinks=False):
                    file_size = entry.stat(follow_symlinks=False).st_size
                    node['children'].append({
                        'name': entry.name,
                        'path': entry.path,
                        'size': file_size,
                        'is_dir': False,
                        'children': [],
                        'scanned': True
                    })
                    node['size'] += file_size
            except (PermissionError, OSError):
                continue

        # Process subdirectories concurrently across thread pool
        if dirs_to_scan:
            with ThreadPoolExecutor(max_workers=16) as executor:
                # Submit subfolders to worker thread queue
                future_to_entry = {
                    executor.submit(self._get_folder_size, entry.path): entry
                    for entry in dirs_to_scan
                }

                for future in future_to_entry:
                    entry = future_to_entry[future]
                    try:
                        dir_size = future.result()
                    except (PermissionError, OSError):
                        dir_size = 0

                    node['children'].append({
                        'name': entry.name,
                        'path': entry.path,
                        'size': dir_size,
                        'is_dir': True,
                        'children': [],
                        'scanned': False
                    })
                    node['size'] += dir_size

        return node

    def _get_folder_size(self, path: str) -> int:
        """Recursive folder calculation with fast exception suppression."""
        total = 0
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += self._get_folder_size(entry.path)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

        return total