import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
import serial

class SerialWorker(QThread):
    new_data = Signal(dict)

    def __init__(self, port_name, baud_rate):
        super().__init__()
        self.on = True
        self.port_name = port_name
        self.baud_rate = baud_rate

    def run(self):
        time.sleep(1) 
        with serial.Serial(self.port_name, self.baud_rate) as ser:
            while self.on:
                try:
                    data = ser.readline().decode().strip().split(',')
                    receiver_data = {
                        'receiver': data[0],
                        'rssi': data[1],
                        'snr': data[2]
                    }
                    self.new_data.emit(receiver_data)
                    time.sleep(0.1)  # Delay to prevent overwhelming the main thread
                except (IndexError, ValueError):
                    pass

class Screen1(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.show()

        label = QLabel('Network Health')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        back_button = QPushButton('Back to Main Screen')
        back_button.clicked.connect(self.back_to_main)

        self.receiver_table = QTableWidget()
        self.receiver_table.setColumnCount(3)
        self.receiver_table.setHorizontalHeaderLabels(['Receiver', 'RSSI', 'SNR'])
        self.receiver_table.setRowCount(4)
        self.receiver_table.verticalHeader().setVisible(False)
        self.receiver_table.setStyleSheet("QTableWidget {background-color: #F0F0F0;}"
                                          "QHeaderView::section {background-color: #CCCCCC;}")
        self.receiver_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.receiver_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.receiver_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for i in range(4):
            self.receiver_table.setItem(i, 0, QTableWidgetItem(f'Receiver {i+1}'))
            self.receiver_table.setItem(i, 1, QTableWidgetItem('N/A'))
            self.receiver_table.setItem(i, 2, QTableWidgetItem('N/A'))

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.receiver_table)
        layout.addWidget(back_button)
        layout.addWidget(self.progress_bar)
        layout.setStretchFactor(self.receiver_table, 1)
        self.setLayout(layout)

        self.serial_worker = SerialWorker('COM15', 115200)
        self.serial_worker.new_data.connect(self.update_receiver_data)
        self.serial_worker.start()

    def back_to_main(self):
        self.serial_worker.on = False
        time.sleep(0.2) 
        self.serial_worker.terminate()
        self.serial_worker.wait()  # Wait for the worker thread to finish
        if hasattr(self.serial_worker, 'ser'):
            self.serial_worker.ser.close()  # Close the serial connection
        from main_screen import MainScreen
        self.main_window.setCentralWidget(MainScreen())

    
    def update_receiver_data(self, data):
        try:
            if len(data) > 0:
                self.progress_bar.hide()
            else: 
                self.progress_bar.show()

            receiver_id = data['receiver']
            rssi = data['rssi']
            snr = data['snr']

            row = int(receiver_id) - 1
            self.receiver_table.setItem(row, 1, QTableWidgetItem(rssi))
            self.receiver_table.setItem(row, 2, QTableWidgetItem(snr))

            rssi_color = self.get_color(int(rssi), -100, -50)
            snr_color = self.get_color(float(snr), 0, 30)

            self.receiver_table.item(row, 1).setBackground(rssi_color)
            self.receiver_table.item(row, 2).setBackground(snr_color)
        except (KeyError, ValueError) as e:
            print("Received data in unexpected format:", data)
            print("Error:", str(e))

    @staticmethod
    def get_color(value, min_value, max_value):
        if value <= min_value:
            return QColor(255, 0, 0)  # Red
        elif value >= max_value:
            return QColor(0, 255, 0)  # Green
        else:
            ratio = (value - min_value) / (max_value - min_value)
            red = int(255 * (1 - ratio))
            green = int(255 * ratio)
            return QColor(red, green, 0)