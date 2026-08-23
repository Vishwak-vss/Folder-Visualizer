import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QLabel, QSplitter, QHeaderView
)
from PyQt6.QtGui import QColor, QFont

from scanner import ScanWorker
from chart import StorageChartCanvas


class StorageVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Percentage Viewer (Python Prototype)")
        self.resize(1100, 650)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Top Bar
        top_bar = QHBoxLayout()
        self.btn_select = QPushButton("Browse Folder / Drive")
        self.btn_select.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        self.btn_select.clicked.connect(self.choose_folder)

        self.lbl_status = QLabel("Select a folder to scan...")
        self.lbl_status.setFont(QFont("Segoe UI", 10))

        top_bar.addWidget(self.btn_select)
        top_bar.addWidget(self.lbl_status, stretch=1)
        layout.addLayout(top_bar)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Splitter View (Tree + Chart)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Percentage Bar", "Percentage"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        splitter.addWidget(self.tree)

        self.chart_canvas = StorageChartCanvas(self)
        splitter.addWidget(self.chart_canvas)

        splitter.setSizes([650, 450])
        layout.addWidget(splitter)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan", "C:\\")
        if folder:
            self.start_scan(folder)

    def start_scan(self, path):
        self.btn_select.setEnabled(False)
        self.progress_bar.show()
        self.tree.clear()
        self.lbl_status.setText(f"Scanning {path}...")

        self.worker = ScanWorker(path)
        self.worker.progress.connect(lambda p: self.lbl_status.setText(p))
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, data):
        self.progress_bar.hide()
        self.btn_select.setEnabled(True)
        self.lbl_status.setText(f"Scan complete: {data['path']}")

        total_size = data['size'] if data['size'] > 0 else 1
        sorted_children = sorted(data['children'], key=lambda x: x['size'], reverse=True)

        for child in sorted_children:
            pct = (child['size'] / total_size) * 100
            size_mb = child['size'] / (1024 * 1024)

            bar_len = int(pct / 2)
            bar_str = "█" * bar_len + "░" * (50 - bar_len)

            item = QTreeWidgetItem([
                f"{'📁' if child['is_dir'] else '📄'} {child['name']}",
                f"{size_mb:.2f} MB",
                bar_str,
                f"{pct:.1f}%"
            ])

            if pct > 20:
                item.setForeground(3, QColor("#e74c3c"))
            elif pct > 5:
                item.setForeground(3, QColor("#f39c12"))

            self.tree.addTopLevelItem(item)

        self.chart_canvas.update_pie_chart(sorted_children, total_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    win = StorageVisualizer()
    win.show()
    sys.exit(app.exec())