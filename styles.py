"""
Application stylesheet module.
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    color: #E0E0E0;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

QFrame#Card {
    background-color: #1E1E1E;
    border: 1px solid #2D2D2D;
    border-radius: 8px;
    padding: 12px;
}

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

QSplitter::handle {
    background-color: #121212;
    width: 6px;
}
"""