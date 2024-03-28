from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QWidget
from network_health import Screen1

from threed_visualization import Threed_visualization
from twod_leastSquared import Twod_visualization_LS
from twod_visualization import Twod_visualization


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window properties
        self.setWindowTitle("LTDANN")
        self.setGeometry(100, 100, 700, 500)  # Set the window size

        # Create buttons
        self.button1 = QPushButton('Check Network Health', self)
        self.button2 = QPushButton('Visualize Neural Network 3d', self)
        self.button3 = QPushButton('Visualize Neural Network 2d', self)
        
        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # Connect buttons to their respective functions
        self.button1.clicked.connect(self.show_screen1)
        self.button2.clicked.connect(self.show_screenthreeDimensional)
        self.button3.clicked.connect(self.show_screentwoDimensional)

        Threed_visualization

    def show_screen1(self):
        self.setCentralWidget(Screen1(self))

    def show_screentwoDimensional(self):
        self.setCentralWidget(Twod_visualization_LS(self))

    def show_screenthreeDimensional(self):
        self.setCentralWidget(Threed_visualization(self))