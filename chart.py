import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class StorageChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1E1E1E')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def update_pie_chart(self, items, total_size):
        self.ax.clear()
        
        if not items or total_size <= 0:
            self.draw()
            return

        # 1. Top items + "Others"
        display_items = []
        other_size = 0

        for i, item in enumerate(items):
            if i < 6:
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

        # 2. Visual Minimum Floor of 5%
        MIN_PCT = 5.0
        visual_pcts = [max(item['true_pct'], MIN_PCT) for item in display_items]
        visual_sum = sum(visual_pcts)
        visual_sizes = [(v / visual_sum) * 100 for v in visual_pcts]

        colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#64748B']

        # 3. Render Donut Slices
        wedges, _ = self.ax.pie(
            visual_sizes,
            startangle=140,
            colors=colors[:len(visual_sizes)],
            wedgeprops=dict(width=0.45, edgecolor='#1E1E1E', linewidth=2)
        )

        # 4. Calculate initial positions for annotations
        annotations = []
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
            rad = np.deg2rad(ang)
            
            # Point on slice edge
            x_slice = np.cos(rad)
            y_slice = np.sin(rad)
            
            # Default text position
            x_text = 1.35 * x_slice
            y_text = 1.35 * y_slice
            
            label = f"{display_items[i]['name']} ({display_items[i]['true_pct']:.3f}%)"
            annotations.append({
                'label': label,
                'slice_pos': (x_slice, y_slice),
                'text_pos': [x_text, y_text],
                'x_dir': 1 if x_text >= 0 else -1
            })

        # 5. Anti-Collision: Push overlapping labels upward/downward on Y-axis
        MIN_Y_DIST = 0.18
        
        # Resolve collisions on right side (x >= 0) and left side (x < 0) separately
        for side in [1, -1]:
            side_nodes = [a for a in annotations if a['x_dir'] == side]
            # Sort vertically bottom to top
            side_nodes.sort(key=lambda a: a['text_pos'][1])
            
            for k in range(1, len(side_nodes)):
                prev_y = side_nodes[k - 1]['text_pos'][1]
                curr_y = side_nodes[k]['text_pos'][1]
                
                if (curr_y - prev_y) < MIN_Y_DIST:
                    side_nodes[k]['text_pos'][1] = prev_y + MIN_Y_DIST

        # 6. Render Native Matplotlib Annotations with Leader Lines
        for a in annotations:
            ha = "left" if a['x_dir'] == 1 else "right"
            
            self.ax.annotate(
                a['label'],
                xy=a['slice_pos'],
                xytext=a['text_pos'],
                horizontalalignment=ha,
                verticalalignment="center",
                color="#E0E0E0",
                fontsize=9,
                fontweight='bold',
                arrowprops=dict(
                    arrowstyle="-",
                    color="#64748B",
                    connectionstyle="angle,angleA=0,angleB=90,rad=5",
                    linewidth=1
                )
            )

        self.ax.set_title("", color="#FFFFFF", fontsize=12, pad=15, fontweight='bold')
        self.fig.tight_layout()
        self.draw()