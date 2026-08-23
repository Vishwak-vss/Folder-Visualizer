from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionProgressBar, QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class ProgressBarDelegate(QStyledItemDelegate):
    """Renders a native fixed-width percentage bar inside QTreeWidget cells."""

    def paint(self, painter, option, index):
        # Column 2 holds numeric float percentage stored via UserRole
        data = index.data(Qt.ItemDataRole.UserRole)
        
        if data is not None and index.column() == 2:
            opts = QStyleOptionProgressBar()
            opts.rect = option.rect
            opts.minimum = 0
            opts.maximum = 100
            opts.progress = int(data)
            opts.text = f"{data:.1f}%"
            opts.textVisible = True
            opts.textAlignment = Qt.AlignmentFlag.AlignCenter

            # Apply clean dark-theme styling to cell progress bar
            widget = option.widget
            style = widget.style() if widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ProgressBar, opts, painter)
        else:
            super().paint(painter, option, index)