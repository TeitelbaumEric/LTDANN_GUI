import time
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy
from PySide6.QtCore import QThread, Signal
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
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate

    def run(self):
        with serial.Serial(self.port_name, self.baud_rate) as ser:
            while True:
                try:
                    info = ser.readline().decode().strip().split(',')
                    node_dict["nodevals"][info[0]] = {'rssi': info[1], 'snr': info[2]}
                    if EMULATOR:
                        # Convert 'x' and 'y' values to floats
                        node_dict['x'] = float(info[3])
                        node_dict['y'] = float(info[4])
                        # print("For node" + info[0] + ", the prediction is " + info[5] + " meters")

                    self.new_data.emit(node_dict)
                except IndexError:
                    pass

class Twod_visualization_LS(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.show_circles = True  # Flag to toggle circle visibility
        self.unknown_node = [400, 400]
        self.error_list = []  # List to store the errors over the trip

        # UI setup
        label = QLabel('Visualize Distance Predictions')
        self.error_label = QLabel('Error: N/A')  # Label to display the error
        self.avg_error_label = QLabel('Average Error: N/A')  # Label to display the average error over the trip
        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Buttons for toggling circle visibility and randomizing node location
        self.toggle_circles_button = QPushButton('Toggle Circles Visibility', self)
        self.toggle_circles_button.clicked.connect(self.toggle_circles)
        # Create the Matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas(self)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.matplotlib_canvas)
        layout.addWidget(self.toggle_circles_button)  # Add toggle visibility button
        layout.addWidget(self.error_label)  # Add the error label to the layout
        layout.addWidget(self.avg_error_label)  # Add the average error label to the layout
        layout.addWidget(back_button)  # Add back button
        self.setLayout(layout)  # Set the layout for this widget
        # Create and start the serial worker thread
        self.serial_worker = SerialWorker('COM15', 115200)
        self.serial_worker.new_data.connect(self.update_transmitter_data)
        self.serial_worker.start()

        self.transmitter_data = {}

    def back_to_main(self):
        self.serial_worker.terminate()
        self.main_window.setCentralWidget(MainScreen())

    def update_transmitter_data(self, data):
        self.transmitter_data = data
        self.display_predictions()

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

    def toggle_circles(self):
        self.show_circles = not self.show_circles
        self.display_predictions()
        