from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from serial import SerialException
import time
from network_health import NetworkHealth
from serial_manager import SerialWorker
from twod_leastSquared import Twod_visualization_LS

class MainScreen(QMainWindow):
    def __init__(self, mainwindow, num_nodes, network_size):
        super().__init__()
        self.mainwindow = mainwindow
        self.num_nodes = num_nodes
        self.network_size = network_size

        self.setWindowTitle("LTDANN")
        self.setGeometry(0, 0, 800, 480)  # Set the window size to 800x480 pixels

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)  # Increase spacing between buttons

        title_label = QLabel("LTDANN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))

        self.button1 = QPushButton('Check Network Health')
        self.button1.clicked.connect(self.show_screen1)
        self.button1.setFixedHeight(120)  # Increase button height

        self.button3 = QPushButton('Visualize Neural Network 2D')
        self.button3.clicked.connect(self.show_screentwoDimensional)
        self.button3.setFixedHeight(120)  # Increase button height

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.button1)
        main_layout.addWidget(self.button3)

        self.network_health_screen = NetworkHealth(self, self.num_nodes, self.network_size)
        self.twod_screen = Twod_visualization_LS(self, self.num_nodes, self.network_size)

    def show_screen1(self):
        self.network_health_screen.showMaximized()
        self.hide()

    def show_screentwoDimensional(self):
        self.twod_screen.showMaximized()
        self.hide()