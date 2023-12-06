import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QWidget, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal
from tdoa_sim.TDoA import *
from random import randint

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

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111, projection='3d')
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class TdoaWorker(QThread):
    finished = Signal(tuple)

    def run(self):
        while True:
            calculated_pos = self.calculate_tdoa()
            time.sleep(1)
            self.finished.emit(calculated_pos)

    def calculate_tdoa(self):
        # run tdoa sim using current node locations
        transmitter = Node(500, 400, 2)  # Transmitter
        num_nanos = 31.25
        receivers = [
            Node(0, 0, 5),  # Receiver 1
            Node(0, 1000, 2),  # Receiver 2
            Node(1000, 0, 3),  # Receiver 3
            Node(1000, 1000, 1)  # Receiver 4
        ]
        calculated_pos = calculate_tdoa(transmitter, receivers, num_nanos, transmitter.z)
        return receivers, calculated_pos


class Screen2(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        label = QLabel('Visualize object localization')

        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Button to run/rerun TDOA calculation
        # tdoa_button = QPushButton('Run TDoA simulation', self)
        # tdoa_button.clicked.connect(self.run_tdoa_sim)

        # Create the Matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas(self)

        layout = QVBoxLayout()
        layout.addWidget(label)
        # layout.addWidget(tdoa_button)
        layout.addWidget(self.matplotlib_canvas)
        layout.addWidget(back_button)
        self.setLayout(layout)

        # Create and start the worker thread
        self.worker_thread = TdoaWorker()
        self.worker_thread.finished.connect(self.display_3d_graph)
        self.worker_thread.start()

    def back_to_main(self):
        self.worker_thread.terminate()
        self.main_window.setCentralWidget(MainScreen())

    # def run_tdoa_sim(self):
        # restart sim if button pressed
        # self.worker_thread.terminate()
        # self.worker_thread.start()

    def display_3d_graph(self, data):
        receivers, calculated_pos = data
        # Clear the previous plot
        self.matplotlib_canvas.axes.cla()

        # Plot receivers
        for receiver in receivers:
            self.matplotlib_canvas.axes.scatter(receiver.x, receiver.y, receiver.z, marker='o', label=f'Receiver')

        # Plot calculated position
        self.matplotlib_canvas.axes.scatter(calculated_pos[0], calculated_pos[1], calculated_pos[2], marker='x', label='Calculated Position', s=100)

        # Set labels
        self.matplotlib_canvas.axes.set_xlabel('X-axis')
        self.matplotlib_canvas.axes.set_ylabel('Y-axis')
        self.matplotlib_canvas.axes.set_zlabel('Z-axis')
        self.matplotlib_canvas.axes.set_title('TDoA 3D Positioning')

        # Add legend
        self.matplotlib_canvas.axes.legend(loc='upper left')

        # Draw the plot
        self.matplotlib_canvas.draw()

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainScreen()
    main_window.show()

    app.exec()