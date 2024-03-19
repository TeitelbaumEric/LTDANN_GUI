from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QWidget, QTextEdit
from PySide6.QtCore import Qt, Signal, QThread
from tdoa_sim.TDoA import *
from random import randint
import serial

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window properties
        self.setWindowTitle("LTDANN")
        self.setGeometry(100, 100, 700, 500)  # Set the window size

        # Create buttons
        self.button1 = QPushButton('Check Network Health', self)
        self.button2 = QPushButton('Visualize Object Localization', self)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # Connect buttons to their respective functions
        self.button1.clicked.connect(self.show_screen1)
        self.button2.clicked.connect(self.show_screen2)

    def show_screen1(self):
        self.setCentralWidget(Screen1(self))

    def show_screen2(self):
        self.setCentralWidget(Screen2(self))

class Screen1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        label = QLabel('Check network health')

        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Create a list widget to display receivers and their connection status
        self.receiver_list = QListWidget(self)

        # Add items to the list widget
        self.receiver1_item = QListWidgetItem('Receiver 1: Connected, Strength: 90%')
        self.receiver2_item = QListWidgetItem('Receiver 2: Disconnected, Strength: N/A')
        self.receiver3_item = QListWidgetItem('Receiver 3: Connected, Strength: 85%')
        self.receiver4_item = QListWidgetItem('Receiver 4: Disconnected, Strength: N/A')

        # Set the connection status for each receiver
        self.receiver1_item.setForeground(Qt.green)  # Connected is displayed in green
        self.receiver2_item.setForeground(Qt.red)    # Disconnected is displayed in red
        self.receiver3_item.setForeground(Qt.green)
        self.receiver4_item.setForeground(Qt.red)

        # Add items to the list
        self.receiver_list.addItem(self.receiver1_item)
        self.receiver_list.addItem(self.receiver2_item)
        self.receiver_list.addItem(self.receiver3_item)
        self.receiver_list.addItem(self.receiver4_item)

        # Button to check signal strength
        retry_button = QPushButton('Check transmitter signal strength', self)
        retry_button.clicked.connect(self.check_signal_button)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(retry_button)
        layout.addWidget(self.receiver_list)
        layout.addWidget(back_button)
        self.setLayout(layout)

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

    def check_signal_button(self):
        # Change all receivers to connected and strong connection
        self.receiver1_item.setText(f'Receiver 1: Connected, Strength: {randint(0,100)}%')
        self.receiver2_item.setText(f'Receiver 2: Connected, Strength: {randint(0,100)}%')
        self.receiver3_item.setText(f'Receiver 3: Connected, Strength: {randint(0,100)}%')
        self.receiver4_item.setText(f'Receiver 4: Connected, Strength: {randint(0,100)}%')

        for item in [self.receiver1_item, self.receiver2_item, self.receiver3_item, self.receiver4_item]:
            item.setForeground(Qt.green)  # Set text color to green for connected receivers

class SerialWorker(QThread):
    new_data = Signal(str)

    def __init__(self, port_name, baud_rate):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate

    def run(self):
        with serial.Serial(self.port_name, self.baud_rate) as ser:
            while True:
                line = ser.readline().decode().strip()
                self.new_data.emit(line)

class Screen2(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        label = QLabel('Visualize object localization')

        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Text edit to display serial data
        self.serial_text_edit = QTextEdit()
        self.serial_text_edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.serial_text_edit)
        layout.addWidget(back_button)
        self.setLayout(layout)

        # Start serial communication
        self.serial_worker = SerialWorker('ACM0', 115200)
        self.serial_worker.new_data.connect(self.update_serial_text)
        self.serial_worker.start()

    def update_serial_text(self, data):
        self.serial_text_edit.append(data)

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainScreen()
    main_window.show()

    app.exec()