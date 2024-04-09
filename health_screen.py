# network_health.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from serial_manager import serial_manager

class NetworkHealth(QWidget):
    def __init__(self, main_screen, num_nodes, network_size):
        super().__init__()
        self.main_screen = main_screen
        self.num_nodes = num_nodes
        self.network_size = network_size
        label = QLabel('Network Health')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        back_button = QPushButton('Back to Main Screen')
        back_button.clicked.connect(self.back_to_main)

        self.receiver_table = QTableWidget()
        self.receiver_table.setColumnCount(3)
        self.receiver_table.setHorizontalHeaderLabels(['Receiver', 'RSSI', 'SNR'])
        self.receiver_table.verticalHeader().setVisible(False)
        self.receiver_table.setStyleSheet("QTableWidget {background-color: #F0F0F0;}"
                                          "QHeaderView::section {background-color: #CCCCCC;}")
        self.receiver_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.receiver_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.receiver_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.receiver_table)
        layout.addWidget(back_button)
        layout.setStretchFactor(self.receiver_table, 1)
        self.setLayout(layout)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_receiver_data)
        self.update_timer.start(1000)  # Update every 1000 milliseconds (1 second)

    def back_to_main(self):
        self.main_screen.showFullScreen()
        self.hide()

    def update_receiver_data(self):
        receivers_data = serial_manager.get_latest_data()
        if receivers_data is not None:
            self.receiver_table.setRowCount(self.num_nodes)
            for row, (receiver_id, data) in enumerate(receivers_data.items()):
                if row < self.num_nodes:
                    self.receiver_table.setItem(row, 0, QTableWidgetItem(receiver_id))
                    self.receiver_table.setItem(row, 1, QTableWidgetItem(data['rssi']))
                    self.receiver_table.setItem(row, 2, QTableWidgetItem(data['snr']))

                    rssi_color = self.get_color(int(data['rssi']), -100, -50)
                    snr_color = self.get_color(float(data['snr']), 0, 30)

                    self.receiver_table.item(row, 1).setBackground(rssi_color)
                    self.receiver_table.item(row, 2).setBackground(snr_color)

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