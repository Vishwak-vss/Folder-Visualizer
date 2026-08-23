from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView


class StorageTreeWidget(QTreeWidget):
    """Lazy-loading tree view with fixed column layouts and deep click handlers."""
    
    node_selected = pyqtSignal(dict)
    folder_clicked = pyqtSignal(dict, QTreeWidgetItem)  # Emits node data AND item handle

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Name", "Size", "Share"])
        
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        self.setColumnWidth(1, 90)   # Size
        self.setColumnWidth(2, 70)   # Share percentage

        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(self._on_item_expanded)

    def populate_tree(self, root_data: dict, parent_item=None):
        """Populates root data or attaches child nodes dynamically."""
        total_size = root_data['size'] if root_data['size'] > 0 else 1
        sorted_children = sorted(root_data.get('children', []), key=lambda x: x['size'], reverse=True)

        if parent_item is None:
            self.clear()
            for child in sorted_children:
                self._add_single_node(self, child, total_size)
        else:
            # Clear dummy "Loading..." placeholder item
            parent_item.takeChildren()
            for child in sorted_children:
                self._add_single_node(parent_item, child, total_size)

    def _add_single_node(self, parent_item, node_data: dict, parent_total_size: int):
        pct = (node_data['size'] / parent_total_size) * 100 if parent_total_size > 0 else 0
        size_mb = node_data['size'] / (1024 * 1024)

        if size_mb > 1024:
            size_formatted = f"{size_mb / 1024:.2f} GB"
        else:
            size_formatted = f"{size_mb:.2f} MB"

        item = QTreeWidgetItem([
            f"{'📁' if node_data['is_dir'] else '📄'}  {node_data['name']}",
            size_formatted,
            f"{pct:.1f}%"
        ])

        item.setData(0, Qt.ItemDataRole.UserRole, node_data)

        if pct > 20:
            item.setForeground(2, QColor("#EF4444"))
        elif pct > 5:
            item.setForeground(2, QColor("#F59E0B"))
        else:
            item.setForeground(2, QColor("#10B981"))

        if isinstance(parent_item, QTreeWidget):
            parent_item.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        # Add dummy placeholder for folders that haven't been scanned yet
        if node_data.get('is_dir') and not node_data.get('scanned', False):
            dummy = QTreeWidgetItem(["Loading..."])
            item.addChild(dummy)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if node_data:
            self.node_selected.emit(node_data)
            if node_data.get('is_dir'):
                item.setExpanded(True)  # Auto-expand item visual branch
                self.folder_clicked.emit(node_data, item)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if node_data and node_data.get('is_dir'):
            self.folder_clicked.emit(node_data, item)