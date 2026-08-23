import sys
import os
import string
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QProgressBar, QLabel, QSplitter, QFrame, QTreeWidgetItem
)

from styles import DARK_THEME_QSS
from header_card import HeaderCard
from tree_widget import StorageTreeWidget
from chart import StorageChartCanvas
from scanner import ScanWorker


class StorageVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Percentage Viewer")
        self.resize(1150, 700)
        self.raw_data = None
        self.active_workers = []  # Prevents thread GC crashes
        self.init_ui()
        self.load_available_drives()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Card
        self.header_card = HeaderCard()
        self.header_card.drive_changed.connect(self.start_scan)
        self.header_card.reset_scope_clicked.connect(self.reset_to_global)
        main_layout.addWidget(self.header_card)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Main Content Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Tree View
        self.tree = StorageTreeWidget()
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.node_selected.connect(self.on_node_selected)
        self.tree.folder_clicked.connect(self.scan_subfolder)
        splitter.addWidget(self.tree)

        # Chart Card
        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        self.lbl_chart_title = QLabel("Capacity Share")
        self.lbl_chart_title.setObjectName("SectionTitle")
        chart_layout.addWidget(self.lbl_chart_title)

        self.chart_canvas = StorageChartCanvas(self)
        chart_layout.addWidget(self.chart_canvas, stretch=1)
        splitter.addWidget(chart_card)

        # Lock layout proportions and expansion factors
        splitter.setSizes([650, 450])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter, stretch=1)

    def scan_subfolder(self, node_data: dict, tree_item: QTreeWidgetItem):
        """Triggers a background scan for the subfolder and updates tree & chart."""
        # If folder is already scanned, directly populate tree & chart
        if node_data.get('scanned') and node_data.get('children'):
            self.tree.populate_tree(node_data, parent_item=tree_item)
            self._update_chart_for_folder(node_data)
            return

        self.progress_bar.show()
        self.lbl_chart_title.setText(f"Breakdown: {node_data['name']}")

        # Start multi-threaded scan and hold worker reference safely
        worker = ScanWorker(node_data['path'])
        self.active_workers.append(worker)

        worker.finished.connect(
            lambda result, w=worker: self.on_subfolder_scan_finished(result, node_data, tree_item, w)
        )
        worker.start()

    def on_subfolder_scan_finished(self, scan_result: dict, original_node: dict, tree_item: QTreeWidgetItem, worker: ScanWorker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

        if not self.active_workers:
            self.progress_bar.hide()

        # Mark node as scanned and assign newly fetched subfolder children
        original_node['children'] = scan_result['children']
        original_node['scanned'] = True

        # Render subfolder items under the target tree item
        self.tree.populate_tree(scan_result, parent_item=tree_item)

        # Update chart
        self._update_chart_for_folder(original_node)

    def _update_chart_for_folder(self, node_data: dict):
        """Helper to refresh pie chart on subfolder selection."""
        if node_data.get('children'):
            children = node_data['children']
            dir_size = node_data['size'] if node_data['size'] > 0 else 1
            sorted_children = sorted(children, key=lambda x: x['size'], reverse=True)

            self.lbl_chart_title.setText(f"Folder Weightage: {node_data['name']}")
            self.chart_canvas.update_pie_chart(sorted_children, dir_size)

    def load_available_drives(self):
        drives = []
        if sys.platform == 'win32':
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ["/"]

        self.header_card.set_drives(drives)
        if drives:
            self.start_scan(drives[0])

    def start_scan(self, path: str):
        if not path:
            return

        self.header_card.set_busy(True)
        self.progress_bar.show()
        self.tree.clear()
        self.header_card.set_status(f"Scanning drive: {path}")

        worker = ScanWorker(path)
        self.active_workers.append(worker)
        worker.progress.connect(self.header_card.set_status)
        worker.finished.connect(
            lambda data, w=worker: self.on_scan_finished(data, w)
        )
        worker.start()

    def on_scan_finished(self, data: dict, worker: ScanWorker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

        if not self.active_workers:
            self.progress_bar.hide()

        self.header_card.set_busy(False)
        self.header_card.set_status(f"Active Drive: {data['path']}")
        self.raw_data = data

        self.tree.populate_tree(data)
        self.reset_to_global()

    def reset_to_global(self):
        """Resets pie chart to show global drive root level share."""
        if not self.raw_data:
            return

        total_size = self.raw_data['size'] if self.raw_data['size'] > 0 else 1
        sorted_children = sorted(self.raw_data['children'], key=lambda x: x['size'], reverse=True)

        self.lbl_chart_title.setText(f"Global Scope Share ({self.raw_data['path']})")
        self.chart_canvas.update_pie_chart(sorted_children, total_size)

    def on_node_selected(self, node_data: dict):
        """Updates pie chart weightage based on clicked directory or file."""
        if node_data.get('is_dir') and node_data.get('children'):
            self._update_chart_for_folder(node_data)
        else:
            total_size = self.raw_data['size'] if self.raw_data and self.raw_data['size'] > 0 else 1
            item_size = node_data['size']

            single_item_data = [
                {'name': node_data['name'], 'size': item_size},
                {'name': 'Rest of Drive', 'size': max(0, total_size - item_size)}
            ]
            self.lbl_chart_title.setText(f"File Share: {node_data['name']}")
            self.chart_canvas.update_pie_chart(single_item_data, total_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    win = StorageVisualizer()
    win.show()
    sys.exit(app.exec())