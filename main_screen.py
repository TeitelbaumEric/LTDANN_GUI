from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from network_health import Screen1
from twod_leastSquared import Twod_visualization_LS

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LTDANN")
        self.setGeometry(0, 0, 800, 480)  # Set the window size to 800x480 pixels

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("LTDANN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))

        
        self.button1 = QPushButton('Check Network Health')
        self.button1.clicked.connect(self.show_screen1)

        self.button3 = QPushButton('Visualize Neural Network 2D')
        self.button3.clicked.connect(self.show_screentwoDimensional)

        self.button1.setFixedHeight(100)
        self.button3.setFixedHeight(100)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button1)
        button_layout.addWidget(self.button3)

        main_layout.addWidget(title_label)
        main_layout.addLayout(button_layout)
        main_layout.setSpacing(20)

    def show_screen1(self):
        self.setCentralWidget(Screen1(self))

    def show_screentwoDimensional(self):
        self.setCentralWidget(Twod_visualization_LS(self))
