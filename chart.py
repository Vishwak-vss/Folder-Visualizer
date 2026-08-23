import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class StorageChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1e1e1e')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def update_pie_chart(self, items, total_size):
        self.ax.clear()
        
        if not items or total_size <= 0:
            self.draw()
            return

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

        colors = ['#ff6b6b', '#4ecdc4', '#ffe66d', '#1a535c', '#f7fff7', '#ff9f1c', '#95a5a6']
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            colors=colors[:len(sizes)],
            textprops=dict(color="white", fontsize=9),
            wedgeprops=dict(width=0.4, edgecolor='#1e1e1e')
        )

        for autotext in autotexts:
            autotext.set_color('#ffffff')
            autotext.set_weight('bold')

        self.ax.set_title("Storage Share", color="white", fontsize=12, pad=15)
        self.draw()