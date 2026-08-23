import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QSizePolicy


class StorageChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=4, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1E1E1E')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(250, 250)

    def _truncate_label(self, name: str, max_len: int = 15) -> str:
        """Truncates long folder/file names so the legend remains compact."""
        if len(name) > max_len:
            return f"{name[:max_len - 3]}..."
        return name

    def update_pie_chart(self, items, total_size):
        self.ax.clear()

        if not items or total_size <= 0:
            self.draw()
            return

        display_items = []
        other_size = 0

        for i, item in enumerate(items):
            if i < 5:
                display_items.append({
                    'name': item['name'],
                    'true_size': item['size'],
                    'true_pct': (item['size'] / total_size) * 100
                })
            else:
                other_size += item['size']

        if other_size > 0:
            display_items.append({
                'name': 'Others',
                'true_size': other_size,
                'true_pct': (other_size / total_size) * 100
            })

        MIN_PCT = 5.0
        visual_pcts = [max(item['true_pct'], MIN_PCT) for item in display_items]
        visual_sum = sum(visual_pcts)
        visual_sizes = [(v / visual_sum) * 100 for v in visual_pcts]

        colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']

        # Draw donut chart with internal percentage labels
        wedges, texts = self.ax.pie(
            visual_sizes,
            labels=[f"{item['true_pct']:.1f}%" for item in display_items],
            labeldistance=0.75,
            startangle=140,
            colors=colors[:len(visual_sizes)],
            wedgeprops=dict(width=0.45, edgecolor='#1E1E1E', linewidth=2),
            textprops=dict(color="#FFFFFF", fontsize=8, fontweight='bold', ha='center', va='center')
        )

        
    
        

        if {item['true_size'] > 1024 * 1024 * 1024 for item in display_items}:
            legend_labels = [
                f"{self._truncate_label(item['name'])} ({item['true_size'] / (1024 * 1024 * 1024):.1f} GB)"
                for item in display_items
            ]
        else:
            legend_labels = [
                f"{self._truncate_label(item['name'])} ({item['true_size'] / (1024 * 1024):.1f} MB)"
                for item in display_items
            ]
        # Add embedded legend contained strictly within canvas bounds
        legend = self.ax.legend(
            wedges,
            legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.15),
            ncol=2,
            frameon=False,
            fontsize=8,
            handletextpad=0.5,
            columnspacing=1.0
        )
        
        for text in legend.get_texts():
            text.set_color("#E0E0E0")

        self.fig.tight_layout()
        self.draw()