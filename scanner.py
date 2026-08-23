import os
import time
import ctypes
from ctypes import wintypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal


# --- Load the native DLL once, at import time ---------------------------
_dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "folder_scanner.dll")
_native = ctypes.WinDLL(_dll_path)

_native.get_folder_size.argtypes = [wintypes.LPCWSTR]
_native.get_folder_size.restype = ctypes.c_ulonglong


def native_folder_size(path: str) -> int:
    """Calls into the compiled C++ walker. Releases the GIL for the
    duration of the call (ctypes does this automatically), so this
    is safe and effective to run concurrently across threads."""
    return _native.get_folder_size(path)


class ScanWorker(QThread):
    """Multi-threaded background scanner for rapid directory size calculations.

    Top-level listing stays in Python (cheap - it's a single os.scandir
    call). Recursive size calculation for each subdirectory is delegated
    to a native C++ DLL, which avoids per-file/per-call Python interpreter
    overhead during the deep recursive walk - this is where nearly all
    the time was going.
    """

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, root_path: str, max_workers: int = 16):
        super().__init__()
        self.root_path = root_path
        self.max_workers = max_workers

    def run(self):
        start = time.perf_counter()
        result = self.scan_single_level(self.root_path)
        elapsed = time.perf_counter() - start
        result['scan_duration'] = elapsed
        self.progress.emit(f"Scan completed in {elapsed:.2f}s")
        # print(f"Scan of '{self.root_path}' completed in {elapsed:.2f}s")
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
            with os.scandir(path) as it:
                entries = list(it)
        except (PermissionError, OSError):
            return node

        dirs_to_scan = []

        # Immediate files - handled in Python since this is a single
        # shallow listing, not the deep recursive part.
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

        # Subdirectories: native recursion, parallelized across threads.
        if dirs_to_scan and not self.isInterruptionRequested():
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_entry = {
                    executor.submit(native_folder_size, entry.path): entry
                    for entry in dirs_to_scan
                }

                completed = 0
                total = len(future_to_entry)

                for future in as_completed(future_to_entry):
                    entry = future_to_entry[future]
                    try:
                        dir_size = future.result()
                    except Exception:
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
                    completed += 1

                    if completed % 25 == 0 or completed == total:
                        self.progress.emit(f"Scanned {completed}/{total} folders in {path}")

                    if self.isInterruptionRequested():
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

        return node