# ⚡ High-Performance File & Disk Space Analyzer

A fast, multithreaded desktop application for visualizing disk usage, file percentage breakdowns, and directory trees. Built with **PyQt6** for a responsive user interface and powered by a high-performance **Rust native extension (`pyo3` + `rayon`)** for near-instantaneous directory scanning.

---

# You can use the release version and click on main.exe inside dist/main

## 🚀 Features

- **Blazing Fast Scanning:** Multi-threaded parallel directory traversal powered by Rust (`rayon` + `walkdir`).
- **GIL-Free Multi-Threading:** Rust bypasses Python's Global Interpreter Lock (GIL) to utilize all available CPU cores.
- **Decomposed UI Component Architecture:** Modular components for tree visualization, breakdown charts, summary cards, and custom progress delegates.
- **Non-Blocking Background Threads:** Scanning runs on separate `QThread` workers (`scanner.py`) to keep the interface smooth and responsive.
- **Cross-Version Binary:** Compiled with Python Stable ABI (`abi3`) for compatibility across Python versions.

---

## 🏗 Project Architecture

```text
file-percentage-viewer/
├── chart.py                 # File percentage visualization chart widget
├── header_card.py           # Summary statistics and header card UI
├── main.py                  # Main application window & entry point
├── progress_delegate.py     # Custom QStyledItemDelegate for inline progress bars
├── scanner.py               # PyQt QThread worker wrapper (ScanWorker)
├── folder_scanner.cpp
├── styles.py                # Application styling & QSS themes
├── tree_widget.py           # Custom QTreeWidget for file/folder hierarchies
└── requirements.txt         # Python dependency manifest

# Run these commands
g++ -O3 -shared -o folder_scanner.dll folder_scanner.cpp     -static -static-libgcc -static-libstdc++
pip install PyQt6 matplotlib adjustText
py main.py

# This project is under MIT Licence