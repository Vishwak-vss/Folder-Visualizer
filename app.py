import sys
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QLabel, QSplitter, QHeaderView
)
from PyQt6.QtGui import QColor, QFont

# Matplotlib Qt Integration
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# Fast Background File Scanner
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


# Matplotlib Canvas Widget for Dark Mode
class StorageChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Configure dark-themed matplotlib canvas
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def update_pie_chart(self, items, total_size):
        self.ax.clear()
        
        if not items or total_size <= 0:
            self.draw()
            return

        # Prepare chart data (Top 6 items + "Others" bucket)
        labels = []
        sizes = []
        other_size = 0

        for i, item in enumerate(items):
            if i < 6:
                labels.append(item['name'])
                sizes.append(item['size'])
            else:
                other_size += item['size']

        if other_size > 0:
            labels.append('Others')
            sizes.append(other_size)

        # Plot Donut/Pie Chart
        colors = ['#ff6b6b', '#4ecdc4', '#ffe66d', '#1a535c', '#f7fff7', '#ff9f1c', '#95a5a6']
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors[:len(sizes)],
            textprops=dict(color="white", fontsize=9),
            wedgeprops=dict(width=0.4, edgecolor='#1e1e1e') # Donut cutout
        )

        for autotext in autotexts:
            autotext.set_color('#ffffff')
            autotext.set_weight('bold')

        self.ax.set_title("Storage Share", color="white", fontsize=12, pad=15)
        self.draw()


# Main Storage Visualizer UI
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

        # Top Bar Controls
        top_bar = QHBoxLayout()
        self.btn_select = QPushButton("Browse Folder / Drive")
        self.btn_select.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        self.btn_select.clicked.connect(self.choose_folder)

        self.lbl_status = QLabel("Select a folder to scan...")
        self.lbl_status.setFont(QFont("Segoe UI", 10))

        top_bar.addWidget(self.btn_select)
        top_bar.addWidget(self.lbl_status, stretch=1)
        layout.addLayout(top_bar)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Splitter Layout (Tree View on Left, Chart Canvas on Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Tree View Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Percentage Bar", "Percentage"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        splitter.addWidget(self.tree)

        # 2. Matplotlib Pie Chart Canvas Widget
        self.chart_canvas = StorageChartCanvas(self)
        splitter.addWidget(self.chart_canvas)

        # Set 60/40 default width split
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

        # Populate Tree View
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

        # Update Matplotlib Pie Chart
        self.chart_canvas.update_pie_chart(sorted_children, total_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    win = StorageVisualizer()
    win.show()
    sys.exit(app.exec())