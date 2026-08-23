from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox


class HeaderCard(QFrame):
    """Header component featuring system drive selection and global scope reset."""
    
    drive_changed = pyqtSignal(str)
    reset_scope_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        info_layout = QVBoxLayout()
        lbl_title = QLabel("Storage Visualizer")
        lbl_title.setObjectName("Title")
        
        self.lbl_status = QLabel("Select a drive to scan")
        self.lbl_status.setObjectName("Status")

        info_layout.addWidget(lbl_title)
        info_layout.addWidget(self.lbl_status)

        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.combo_drives = QComboBox()
        self.combo_drives.setFixedWidth(120)
        self.combo_drives.currentTextChanged.connect(self.drive_changed.emit)

        self.btn_reset = QPushButton("Reset to Global Scope")
        self.btn_reset.setObjectName("BrowseBtn")
        self.btn_reset.clicked.connect(self.reset_scope_clicked.emit)

        controls_layout.addWidget(self.combo_drives)
        controls_layout.addWidget(self.btn_reset)

        layout.addLayout(info_layout, stretch=1)
        layout.addLayout(controls_layout)

    def set_drives(self, drives: list):
        self.combo_drives.blockSignals(True)
        self.combo_drives.clear()
        self.combo_drives.addItems(drives)
        self.combo_drives.blockSignals(False)

    def set_status(self, text: str):
        self.lbl_status.setText(text)

    def set_busy(self, is_busy: bool):
        self.combo_drives.setEnabled(not is_busy)
        self.btn_reset.setEnabled(not is_busy)