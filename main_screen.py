from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer
from serial import SerialException
import time
from health_screen import NetworkHealth
from serial_manager import serial_manager
from localization_screen import Twod_visualization_LS

class MainScreen(QMainWindow):
    def __init__(self, mainwindow, num_nodes, network_size):
        super().__init__()
        self.mainwindow = mainwindow
        self.num_nodes = num_nodes
        self.network_size = network_size

        self.setWindowTitle("LTDANN")
        self.setGeometry(0, 0, 800, 480)  # Set the window size to match the touchscreen resolution

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        title_label = QLabel("LTDANN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))

        self.button1 = QPushButton('Check Network Health')
        self.button1.clicked.connect(self.show_screen1)
        self.button1.setFixedHeight(80)

        self.button3 = QPushButton('Visualize Neural Network 2D')
        self.button3.clicked.connect(self.show_screentwoDimensional)
        self.button3.setFixedHeight(80)

        self.exit_button = QPushButton('Exit')  # Add an exit button
        self.exit_button.clicked.connect(self.exit_program)  # Connect the button to the exit_program method
        self.exit_button.setFixedHeight(80)

        self.node_status_layout = QHBoxLayout()
        self.node_status_label = QLabel("Communicating Nodes:")
        self.node_status_label.setFont(QFont("Arial", 14))
        self.node_status_value = QLabel("0")
        self.node_status_value.setFont(QFont("Arial", 14, QFont.Bold))
        self.node_status_value.setStyleSheet("color: green")
        self.node_status_layout.addWidget(self.node_status_label)
        self.node_status_layout.addWidget(self.node_status_value)
        self.node_status_layout.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title_label)
        main_layout.addLayout(self.node_status_layout)
        main_layout.addWidget(self.button1)
        main_layout.addWidget(self.button3)
        main_layout.addWidget(self.exit_button)  # Add the exit button to the layout
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduce the layout margins
        main_layout.setSpacing(20)  # Reduce the spacing between buttons
        
                
        self.network_health_screen = NetworkHealth(self, self.num_nodes, self.network_size)
        self.twod_screen = Twod_visualization_LS(self, self.num_nodes, self.network_size)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_communicating_nodes)
        self.update_timer.start(1000)  # Update every 1000 milliseconds (1 second)

    def show_screen1(self):
        self.network_health_screen.showMaximized()
        self.hide()

    def show_screentwoDimensional(self):
        self.twod_screen.showMaximized()
        self.hide()

    def update_communicating_nodes(self):
        receivers_data = serial_manager.get_latest_data()
        if receivers_data is not None:
            num_communicating_nodes = len(receivers_data)
            self.node_status_value.setText(str(num_communicating_nodes))
        else:
            self.node_status_value.setText("0")

    def exit_program(self):
        QApplication.quit()  # Quit the application