import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QLabel, QSplitter, QHeaderView, QFrame
)
from PyQt6.QtGui import QColor

from scanner import ScanWorker
from chart import StorageChartCanvas

# Modern Dark QSS Stylesheet
DARK_THEME_QSS = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    color: #E0E0E0;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

/* Card Container Styling */
QFrame#Card {
    background-color: #1E1E1E;
    border: 1px solid #2D2D2D;
    border-radius: 8px;
    padding: 12px;
}

/* Header & Status Labels */
QLabel#Title {
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
}

QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #FFFFFF;
    padding-bottom: 4px;
}

QLabel#Status {
    color: #9E9E9E;
    font-size: 13px;
}

/* Primary Button */
QPushButton#BrowseBtn {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#BrowseBtn:hover {
    background-color: #3B82F6;
}

QPushButton#BrowseBtn:pressed {
    background-color: #1D4ED8;
}

QPushButton#BrowseBtn:disabled {
    background-color: #334155;
    color: #64748B;
}

/* Progress Bar */
QProgressBar {
    border: none;
    background-color: #2A2A2A;
    height: 4px;
    border-radius: 2px;
}

QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 2px;
}

/* Tree Widget Styling */
QTreeWidget {
    background-color: #1E1E1E;
    border: 1px solid #2D2D2D;
    border-radius: 8px;
    outline: none;
    font-size: 13px;
}

QTreeWidget::item {
    padding: 6px 4px;
    border-bottom: 1px solid #252525;
}

QTreeWidget::item:hover {
    background-color: #2A2A2A;
}

QTreeWidget::item:selected {
    background-color: #3B82F6;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #181818;
    color: #A1A1AA;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2D2D2D;
    font-size: 12px;
    font-weight: 600;
}

/* Splitter handle */
QSplitter::handle {
    background-color: #121212;
    width: 6px;
}
"""


class StorageVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Percentage Viewer")
        self.resize(1150, 700)
        self.raw_data = None  # Cache root data
        self.init_ui()

    def init_ui(self):
        # Main Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Top Header Card
        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(12, 8, 12, 8)

        info_layout = QVBoxLayout()
        lbl_title = QLabel("Storage Inspector")
        lbl_title.setObjectName("Title")
        
        self.lbl_status = QLabel("Select a folder or drive to visualize disk usage")
        self.lbl_status.setObjectName("Status")
        
        info_layout.addWidget(lbl_title)
        info_layout.addWidget(self.lbl_status)

        self.btn_select = QPushButton("Browse Folder")
        self.btn_select.setObjectName("BrowseBtn")
        self.btn_select.clicked.connect(self.choose_folder)

        top_layout.addLayout(info_layout, stretch=1)
        top_layout.addWidget(self.btn_select, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(top_card)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 2. Main Content Splitter (Tree + Chart)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tree View
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Usage Visual", "Share"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Connect single-click item selection to chart update
        self.tree.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree)

        # Donut Chart Container Frame
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

        splitter.setSizes([650, 450])
        main_layout.addWidget(splitter, stretch=1)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan", "C:\\")
        if folder:
            self.start_scan(folder)

    def start_scan(self, path):
        self.btn_select.setEnabled(False)
        self.progress_bar.show()
        self.tree.clear()
        self.lbl_status.setText(f"Scanning directory: {path}")

        self.worker = ScanWorker(path)
        self.worker.progress.connect(lambda p: self.lbl_status.setText(p))
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, data):
        self.progress_bar.hide()
        self.btn_select.setEnabled(True)
        self.lbl_status.setText(f"Active Path: {data['path']}")
        self.raw_data = data  # Store full scan data

        total_size = data['size'] if data['size'] > 0 else 1
        sorted_children = sorted(data['children'], key=lambda x: x['size'], reverse=True)

        for child in sorted_children:
            pct = (child['size'] / total_size) * 100
            size_mb = child['size'] / (1024 * 1024)

            bar_len = int(pct / 2.5)
            bar_str = "█" * bar_len + "░" * (40 - bar_len)

            item = QTreeWidgetItem([
                f"{'📁' if child['is_dir'] else '📄'}  {child['name']}",
                f"{size_mb:.2f} MB",
                bar_str,
                f"{pct:.2f}%"
            ])

            # Attach raw item dictionary to tree node for access on click
            item.setData(0, Qt.ItemDataRole.UserRole, child)

            if pct > 20:
                item.setForeground(3, QColor("#EF4444"))
                item.setForeground(2, QColor("#EF4444"))
            elif pct > 5:
                item.setForeground(3, QColor("#F59E0B"))
                item.setForeground(2, QColor("#F59E0B"))
            else:
                item.setForeground(3, QColor("#10B981"))

            self.tree.addTopLevelItem(item)

        self.lbl_chart_title.setText("Capacity Share (Root Level)")
        self.chart_canvas.update_pie_chart(sorted_children, total_size)

    def on_item_clicked(self, item, column):
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data:
            return

        # If it's a directory with scanned child items, show its breakdown
        if node_data.get('is_dir') and node_data.get('children'):
            children = node_data['children']
            dir_size = node_data['size'] if node_data['size'] > 0 else 1
            sorted_children = sorted(children, key=lambda x: x['size'], reverse=True)
            
            self.lbl_chart_title.setText(f"Capacity Share: {node_data['name']}")
            self.chart_canvas.update_pie_chart(sorted_children, dir_size)
        
        # If it's a single file or empty folder, highlight its contribution against total size
        else:
            total_size = self.raw_data['size'] if self.raw_data and self.raw_data['size'] > 0 else 1
            item_size = node_data['size']
            
            single_item_data = [
                {'name': node_data['name'], 'size': item_size},
                {'name': 'Rest of Directory', 'size': max(0, total_size - item_size)}
            ]
            self.lbl_chart_title.setText(f"File Share: {node_data['name']}")
            self.chart_canvas.update_pie_chart(single_item_data, total_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    
    win = StorageVisualizer()
    win.show()
    sys.exit(app.exec())