from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from serial import SerialException
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from main_screen import MainScreen
from serial_manager import SerialWorker

import numpy as np

class InitializationScreen(QWidget):
    def __init__(self, mainwindow):
        super().__init__()
        self.mainwindow = mainwindow
        try:
            self.serial_worker = SerialWorker('COM15', 115200)
            self.serial_worker.start()
        except SerialException:
            print("SerialException Error")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Initialization")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        form_layout = QVBoxLayout()

        node_layout = QHBoxLayout()
        node_label = QLabel("Number of Nodes:")
        self.node_combo = QComboBox()
        self.node_combo.addItems(["4", "8"])
        self.node_combo.currentIndexChanged.connect(self.update_node_map)
        node_layout.addWidget(node_label)
        node_layout.addWidget(self.node_combo)
        form_layout.addLayout(node_layout)

        size_layout = QHBoxLayout()
        size_label = QLabel("Network Size (Meters):")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["10", "20", "30", "40", "50", "60", "70", "80", "90", "100",
                                  "200", "300", "400", "500", "600", "700", "800", "900", "1000"])
        self.size_combo.currentTextChanged.connect(self.update_node_map)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        form_layout.addLayout(size_layout)

        layout.addLayout(form_layout)

        self.node_map_canvas = FigureCanvas(Figure(figsize=(5, 5)))
        self.node_map_axes = self.node_map_canvas.figure.add_subplot(111)
        layout.addWidget(self.node_map_canvas)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_form)
        layout.addWidget(submit_button)

        self.setLayout(layout)

        self.update_node_map()

    def update_node_map(self):
        num_nodes = int(self.node_combo.currentText())
        network_size = int(self.size_combo.currentText())

        self.node_map_axes.clear()

        if num_nodes == 4:
            nodes = np.array([
                [0, 0],
                [network_size, 0],
                [network_size, network_size],
                [0, network_size],
            ])
        elif num_nodes == 8:
            nodes = np.array([
                [0, 0],
                [network_size / 2, 0],
                [network_size, 0],
                [network_size, network_size / 2],
                [network_size, network_size],
                [network_size / 2, network_size],
                [0, network_size],
                [0, network_size / 2]
            ])

        for i, node in enumerate(nodes):
            self.node_map_axes.scatter(node[0], node[1], color='blue')
            self.node_map_axes.annotate(f'Node {i+1}', (node[0], node[1]), textcoords="offset points", xytext=(0, 10), ha='center')

        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                if self.are_nodes_adjacent(nodes[i], nodes[j], network_size):
                    node1 = nodes[i]
                    node2 = nodes[j]
                    distance = np.sqrt((node1[0] - node2[0])**2 + (node1[1] - node2[1])**2)
                    midpoint = ((node1[0] + node2[0]) / 2, (node1[1] + node2[1]) / 2)
                    self.node_map_axes.plot([node1[0], node2[0]], [node1[1], node2[1]], 'k--')
                    self.node_map_axes.annotate(f'{distance:.2f}', midpoint, textcoords="offset points", xytext=(0, 5), ha='center')

        self.node_map_axes.set_xlim(-network_size*0.1, network_size*1.1)
        self.node_map_axes.set_ylim(-network_size*0.1, network_size*1.1)
        self.node_map_axes.set_aspect('equal')
        self.node_map_axes.set_title('Node Map')
        self.node_map_axes.set_xlabel('West')
        self.node_map_axes.set_ylabel('South')

        self.node_map_canvas.draw()

    def are_nodes_adjacent(self, node1, node2, network_size):
        # Check if two nodes are adjacent based on their positions
        if node1[0] == node2[0] and abs(node1[1] - node2[1]) == network_size / 2:
            return True
        if node1[1] == node2[1] and abs(node1[0] - node2[0]) == network_size / 2:
            return True
        return False
    
    def submit_form(self):
        num_nodes = int(self.node_combo.currentText())
        network_size = int(self.size_combo.currentText())
        main_screen = MainScreen(self.mainwindow, num_nodes, network_size)
        main_screen.showMaximized()
        self.close()
    