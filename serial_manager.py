# serial_manager.py

import serial
from PySide6.QtCore import QThread, Signal

class SerialManager:
    def __init__(self):
        self.latest_data = None

    def update_data(self, data):
        self.latest_data = data

    def get_latest_data(self):
        return self.latest_data

serial_manager = SerialManager()

class SerialWorker(QThread):
    new_data = Signal(dict)

    def __init__(self, port_name, baud_rate):
        super().__init__()
        self.on = True
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.receivers_data = {}

    def run(self):
        with serial.Serial(self.port_name, self.baud_rate) as ser:
            while self.on:
                try:
                    data = ser.readline().decode().strip().split(',')

                    try: 
                        self.receivers_data[data[0]] = {'rssi': data[1], 'snr': data[2], 'x': data[3], 'y': data[4]}
                    except IndexError: 
                        self.receivers_data[data[0]] = {'rssi': data[1], 'snr': data[2]}

                    serial_manager.update_data(self.receivers_data)
                    self.new_data.emit(self.receivers_data)
                except (IndexError, ValueError):
                    pass