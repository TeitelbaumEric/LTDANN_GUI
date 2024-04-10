# twod_leastSquared.py

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
from serial_manager import serial_manager

EMULATOR = True
network_size = 400

# Load the trained model once
model = load('./network_config/random_forest_model.joblib')

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class Twod_visualization_LS(QWidget):
    def __init__(self, main_screen, num_nodes, network_size):
        super().__init__()
        self.main_screen = main_screen
        self.num_nodes = num_nodes
        self.network_size = network_size
        self.node_history = {}
        self.log_data = []
        self.max_log_entries = 1000  # Maximum number of log entries to keep

        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setFixedHeight(40)  # Reduce the button height

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.show()

        self.show_circles = True  # Flag to toggle circle visibility
    
        self.error_list = []  # List to store the errors over the trip

        self.show_nodes = True
        self.show_lines = True

        self.toggle_lines_button = QPushButton("Toggle Lines")
        self.toggle_lines_button.clicked.connect(self.toggle_lines)
        self.toggle_lines_button.setFixedHeight(40)  # Reduce the button height
        back_button.setFixedHeight(40)  # Reduce the button height

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
        layout.setStretchFactor(self.matplotlib_canvas, 2)

        # Create the Matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas(self, width=4, height=3, dpi=100)  # Reduce the plot size)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.matplotlib_canvas)
        layout.addWidget(self.error_label)  # Add the error label to the layout
        layout.addWidget(self.avg_error_label)  # Add the average error label to the layout
        layout.addWidget(back_button)  # Add back button
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.toggle_lines_button)
        layout.addWidget(self.export_button)
        self.setLayout(layout)  # Set the layout for this widget
    
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
        for key, value in data.items():
            if key not in self.node_history:
                self.node_history[key] = []
            self.node_history[key].append({
                'timestamp': time.time(),
                'rssi': float(value['rssi']),
                'snr': float(value['snr'])
            })
        self.main_window.node_history = self.node_history

    def toggle_nodes(self):
        self.show_nodes = not self.show_nodes
        self.display_predictions()

    def toggle_lines(self):
        self.show_lines = not self.show_lines
        self.display_predictions()

    def back_to_main(self):
        self.main_screen.showFullScreen()
        self.hide()

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
        #new        
        if self.num_nodes == 4:
            nodes = np.array([
                [0, 0],
                [self.network_size, 0],
                [self.network_size, self.network_size],
                [0, self.network_size],
            ])
        elif self.num_nodes == 8:
            nodes = np.array([
                [0, 0],
                [self.network_size / 2, 0],
                [self.network_size, 0],
                [self.network_size, self.network_size / 2],
                [self.network_size, self.network_size],
                [self.network_size / 2, self.network_size],
                [0, self.network_size],
                [0, self.network_size / 2]
            ])
        else:
            raise ValueError("Invalid number of nodes. Supported values are 4 or 8.")

        self.matplotlib_canvas.axes.cla()
        predicted_distances = []

        receivers_data = serial_manager.get_latest_data()
        if receivers_data is not None and len(receivers_data) > 7:
            self.progress_bar.hide()
            rssi_values = []
            snr_values = []
            predicted_distances = []
            for key, value in receivers_data.items():
                if int(key) <= self.num_nodes:
                    rssi = value['rssi']
                    snr = value['snr']

                    rssi_values.append(rssi)
                    snr_values.append(snr)

                    # Create a DataFrame with the appropriate feature names
                    model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

                    # Predict the distance using the DataFrame
                    predicted_distance = model.predict(model_input)[0]
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

            # Check if 'x' and 'y' keys exist in receivers_data for any node
            if any('x' in value and 'y' in value for value in receivers_data.values()):
                # Find the first node that has 'x' and 'y' keys
                known_node = next((value for value in receivers_data.values() if 'x' in value and 'y' in value), None)
                if known_node is not None:
                    x = float(known_node['x'])
                    y = float(known_node['y'])
                    self.matplotlib_canvas.axes.scatter(x, y, s=100, color='blue', label='Known Object')

                    # Calculate the error
                    if estimated_x is not None and estimated_y is not None:
                        # Procure Log Statement
                        log_entry = {
                            'timestamp': time.time(),
                            'nodes': [],
                            'estimated_x': estimated_x[0],
                            'estimated_y': estimated_y[0]
                        }
                        for key, value in receivers_data.items():
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

            self.matplotlib_canvas.axes.set_title('Localization using Least Squares Estimation', fontsize=12)  # Reduce the font size of the plot title
            self.matplotlib_canvas.axes.set_xlabel('X-axis', fontsize=10)  # Reduce the font size of the x-axis label
            self.matplotlib_canvas.axes.set_ylabel('Y-axis', fontsize=10)  # Reduce the font size of the y-axis label
            self.matplotlib_canvas.axes.tick_params(labelsize=8)  # Reduce the font size of the tick labels
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