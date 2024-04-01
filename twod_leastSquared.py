import csv
import time
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QProgressBar, QFileDialog
from PySide6.QtCore import QThread, Signal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from joblib import load
from sklearn.linear_model import RANSACRegressor
import serial

EMULATOR = True
node_dict = {"nodevals": {}, 'x': -9999, "y": -9999}
network_size = 400

# Load the trained model once
model = load('random_forest_Model.joblib')

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class SerialWorker(QThread):
    new_data = Signal(dict)
    def __init__(self, port_name, baud_rate):
        self.on = True
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate

    def run(self):
        time.sleep(1) 
        with serial.Serial(self.port_name, self.baud_rate) as ser:
            while self.on:
                try:
                    info = ser.readline().decode().strip().split(',')
                    node_dict["nodevals"][info[0]] = {'rssi': info[1], 'snr': info[2]}
                    if EMULATOR:
                        # Convert 'x' and 'y' values to floats
                        node_dict['x'] = float(info[3])
                        node_dict['y'] = float(info[4])
                        # print("For node" + info[0] + ", the prediction is " + info[5] + " meters")

                    self.new_data.emit(node_dict)
                    time.sleep(0.1) # delay to prevent overwhelming the main thread
                except IndexError:
                    pass

class Twod_visualization_LS(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.log_data = []
        self.max_log_entries = 1000  # Maximum number of log entries to keep

        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.show()

        
        self.main_window = main_window
        self.show_circles = True  # Flag to toggle circle visibility
        self.unknown_node = [400, 400]
        self.error_list = []  # List to store the errors over the trip

        self.show_nodes = True
        self.show_lines = True

        self.toggle_lines_button = QPushButton("Toggle Lines")
        self.toggle_lines_button.clicked.connect(self.toggle_lines)

        # Reduce GUI update frequency
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.display_predictions)
        self.update_timer.start(1000)  # Update the GUI every 1000 milliseconds HARD WAIT

        # UI setup
        label = QLabel('Visualize Distance Predictions')
        self.error_label = QLabel('Error: N/A')  # Label to display the error
        self.avg_error_label = QLabel('Average Error: N/A')  # Label to display the average error over the trip
        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Create the Matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas(self)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.matplotlib_canvas)
        # layout.addWidget(self.toggle_circles_button)  # Add toggle visibility button
        layout.addWidget(self.error_label)  # Add the error label to the layout
        layout.addWidget(self.avg_error_label)  # Add the average error label to the layout
        layout.addWidget(back_button)  # Add back button
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.toggle_lines_button)
        layout.addWidget(self.export_button)
        self.setLayout(layout)  # Set the layout for this widget
        # Create and start the serial worker thread
        self.serial_worker = SerialWorker('COM15', 115200)
        self.serial_worker.new_data.connect(self.update_transmitter_data)
        self.serial_worker.start()

        self.transmitter_data = {}
    
    def export_data(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        file_dialog.setDefaultSuffix("csv")

        if file_dialog.exec() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.write_data_to_csv(file_path)

    def update_transmitter_data(self, data):
        self.transmitter_data = data
        self.log_data.append(data)
        if len(self.log_data) > self.max_log_entries:
            self.log_data.pop(0)  # Remove the oldest entry if the log exceeds the maximum size

    def toggle_nodes(self):
        self.show_nodes = not self.show_nodes
        self.display_predictions()

    def toggle_lines(self):
        self.show_lines = not self.show_lines
        self.display_predictions()

    def back_to_main(self):
        self.serial_worker.on = False
        time.sleep(0.2) 
        self.serial_worker.terminate()
        self.serial_worker.wait()  # Wait for the worker thread to finish
        if hasattr(self.serial_worker, 'ser'):
            self.serial_worker.ser.close()  # Close the serial connection
        from main_screen import MainScreen
        self.main_window.setCentralWidget(MainScreen())

    def update_transmitter_data(self, data):
        self.transmitter_data = data
        # self.display_predictions() // Test letting timer handle redisplay

    def least_squares_estimation(self, distances, node_positions, weights=None):
        x_coords, y_coords = zip(*node_positions)

        A = np.array([
            [2 * (x_coords[0] - x_coords[i]), 2 * (y_coords[0] - y_coords[i])] for i in range(1, len(x_coords))
        ])

        B = np.array([
            [distances[i]**2 - distances[0]**2 - x_coords[i]**2 + x_coords[0]**2 - y_coords[i]**2 + y_coords[0]**2] for i in range(1, len(distances))
        ])

        # Apply RANSAC for outlier detection
        ransac = RANSACRegressor()
        ransac.fit(A, B.ravel())
        inlier_mask = ransac.inlier_mask_

        # Check and adjust weights array if necessary
        if weights is None or len(weights) != len(A):
            weights = np.ones(len(A))

        # Filter out outliers from A and B using inlier_mask, ensuring weights matches dimensions
        A_inliers = A[inlier_mask]
        B_inliers = B[inlier_mask].reshape(-1, 1)
        weights_inliers = weights[inlier_mask]

        # If after filtering there are not enough inliers to perform a reliable estimation, return a default or error
        if len(A_inliers) < 2:
            print("Error: Not enough inliers for a reliable estimation.")
            return None, None

        # Solve the least squares problem with weighted inliers
        W = np.diag(weights_inliers)
        X = np.linalg.lstsq(A_inliers.T.dot(W).dot(A_inliers), A_inliers.T.dot(W).dot(B_inliers), rcond=None)[0]

        return X[0], X[1]

    def calculate_weights(self, rssi_values, snr_values):
        # Convert RSSI and SNR values to floats
        rssi_values = np.array(rssi_values, dtype=float)
        snr_values = np.array(snr_values, dtype=float)

        # Normalize RSSI and SNR values
        rssi_normalized = (rssi_values - rssi_values.min()) / (rssi_values.max() - rssi_values.min())
        snr_normalized = (snr_values - snr_values.min()) / (snr_values.max() - snr_values.min())

        # Combine RSSI and SNR weights
        weights = (rssi_normalized + snr_normalized) / 2

        return weights

    def calculate_error(self, estimated_x, estimated_y, true_x, true_y):
        estimated_position = np.array([estimated_x, estimated_y])
        true_position = np.array([true_x, true_y])
        error = np.linalg.norm(estimated_position - true_position)
        return error

    def display_predictions(self):
        # Known nodes positions
        nodes = np.array([
            [0, 0],
            [network_size / 2, 0],
            [network_size, 0],
            [network_size, network_size / 2],
            [network_size, network_size],
            [network_size / 2, network_size],
            [0, network_size],
            [0, network_size / 2]
        ])

        self.matplotlib_canvas.axes.cla()
        predicted_distances = []

        if len(node_dict["nodevals"]) > 7:
            self.progress_bar.hide()
            rssi_values = []
            snr_values = []
            predicted_distances = []
            for key, value in node_dict["nodevals"].items():
                rssi = value['rssi']
                snr = value['snr']

                rssi_values.append(rssi)
                snr_values.append(snr)

                # Create a DataFrame with the appropriate feature names
                model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

                # Predict the distance using the DataFrame
                predicted_distance = model.predict(model_input)[0]
                # print("For node" + key + ", the prediction is " + str(predicted_distance) + " meters")
                predicted_distances.append(predicted_distance)

                node_position = nodes[int(key)-1]

                self.matplotlib_canvas.axes.plot(node_position[0], node_position[1], 'bo', label=f'Node {int(key)}')

        
            # Calculate weights based on RSSI and SNR values
            weights = self.calculate_weights(rssi_values, snr_values)

            # Localization using Weighted Least Squares with RANSAC
            estimated_x, estimated_y = self.least_squares_estimation(distances=predicted_distances, node_positions=nodes, weights=weights)

            # Plot the estimated position
            if estimated_x is not None and estimated_y is not None:
                self.matplotlib_canvas.axes.plot(estimated_x, estimated_y, 'ro', label='Estimated Position')

                # Draw lines connecting the nodes to the estimated position
                if self.show_lines:
                    for i, (x, y) in enumerate(nodes):
                        estimated_x_scalar = estimated_x[0]
                        estimated_y_scalar = estimated_y[0]

                        self.matplotlib_canvas.axes.plot([x, estimated_x_scalar], [y, estimated_y_scalar], 'k--')

            if node_dict['x'] != -9999 and node_dict['y'] != -9999:
                x = node_dict['x']
                y = node_dict['y']
                self.matplotlib_canvas.axes.scatter(x, y, s=100, color='blue', label='Unknown Object')

                # Calculate the error
                if estimated_x is not None and estimated_y is not None:
                    # Procure Log Statement
                    log_entry = {
                        'timestamp': time.time(),
                        'nodes': [],
                        'estimated_x': estimated_x[0],
                        'estimated_y': estimated_y[0]
                    }
                    for key, value in node_dict["nodevals"].items():
                        log_entry['nodes'].append({
                            'node_id': key,
                            'rssi': value['rssi'],
                            'snr': value['snr']
                        })
                    self.log_data.append(log_entry)
                    if len(self.log_data) > self.max_log_entries:
                        self.log_data.pop(0)  # Remove the oldest entry if the log exceeds the maximum size

                    # Calculate error if emulating.
                    error = self.calculate_error(estimated_x[0], estimated_y[0], x, y)
                    self.error_label.setText(f'Error: {error:.2f} meters')
                    self.error_list.append(error)  # Add the error to the error list
                    avg_error = np.mean(self.error_list)
                    self.avg_error_label.setText(f'Average Error: {avg_error:.2f} meters')
                else:
                    self.error_label.setText('Error: N/A')
                    self.avg_error_label.setText('Average Error: N/A')

            self.matplotlib_canvas.axes.set_xlabel('X-axis')
            self.matplotlib_canvas.axes.set_ylabel('Y-axis')
            self.matplotlib_canvas.axes.set_title('Localization using Least Squares Estimation')
            self.matplotlib_canvas.axes.legend()
            self.matplotlib_canvas.axes.grid(True)
            self.matplotlib_canvas.axes.axis('equal')
            self.matplotlib_canvas.draw()
        else:
            self.progress_bar.show()
    

    def write_data_to_csv(self, file_path):
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Node ID', 'RSSI', 'SNR', 'Estimated X', 'Estimated Y'])
            for entry in self.log_data:
                timestamp = entry['timestamp']
                estimated_x = entry['estimated_x']
                estimated_y = entry['estimated_y']
                for node in entry['nodes']:
                    node_id = node['node_id']
                    rssi = node['rssi']
                    snr = node['snr']
                    writer.writerow([timestamp, node_id, rssi, snr, estimated_x, estimated_y])