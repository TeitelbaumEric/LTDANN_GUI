from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer
from serial_manager import serial_manager
from health_screen import NetworkHealth
from localization_screen import Twod_visualization_LS

class MainScreen(QMainWindow):
    def __init__(self, mainwindow, num_nodes, network_size):
        super().__init__()
        self.mainwindow = mainwindow
        self.num_nodes = num_nodes
        self.network_size = network_size

        self.setWindowTitle("Localized Temporarily Deployable Autonomous Navigation Network")
        # self.setGeometry(0, 0, 800, 480)  # Set the window size to 800x480 pixels

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)  # Increase spacing between buttons

        title_label = QLabel("Localized Temporarily Deployable Autonomous Navigation Network (LTDANN)")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))

        self.button1 = QPushButton('Check Network Health')
        self.button1.clicked.connect(self.show_screen1)
        self.button1.setFixedHeight(120)  # Increase button height

        self.button3 = QPushButton('Visualize Neural Network 2D')
        self.button3.clicked.connect(self.show_screentwoDimensional)
        self.button3.setFixedHeight(120)  # Increase button height

        # Stylized component to display the number of communicating nodes
        self.node_status_layout = QHBoxLayout()
        self.node_status_label = QLabel("Communicating Nodes:")
        self.node_status_label.setFont(QFont("Arial", 16))
        self.node_status_value = QLabel("0")
        self.node_status_value.setFont(QFont("Arial", 16, QFont.Bold))
        self.node_status_value.setStyleSheet("color: green")
        self.node_status_layout.addWidget(self.node_status_label)
        self.node_status_layout.addWidget(self.node_status_value)
        self.node_status_layout.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title_label)
        main_layout.addLayout(self.node_status_layout)
        main_layout.addWidget(self.button1)
        main_layout.addWidget(self.button3)

        self.network_health_screen = NetworkHealth(self, self.num_nodes, self.network_size)
        self.twod_screen = Twod_visualization_LS(self, self.num_nodes, self.network_size)

        # Update the number of communicating nodes every 1 second
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_communicating_nodes)
        self.update_timer.start(1000)  # Update every 1000 milliseconds (1 second)


    def show_screen1(self):
        self.network_health_screen.showFullScreen()
        self.hide()

    def show_screentwoDimensional(self):
        self.twod_screen.showFullScreen()
        self.hide()

    def update_communicating_nodes(self):
        receivers_data = serial_manager.get_latest_data()
        if receivers_data is not None:
            num_communicating_nodes = len(receivers_data)
            self.node_status_value.setText(str(num_communicating_nodes))
        else:
            self.node_status_value.setText("0")