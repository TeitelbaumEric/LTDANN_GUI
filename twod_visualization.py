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
import serial

EMULATOR = True
node_dict = {"nodevals": {}, 'x': -9999, "y": -9999}
network_size = 100

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
                        print("For node" + info[0] + ", the prediction is " + info[5] + " meters")

                    self.new_data.emit(node_dict)
                except IndexError:
                    pass

class Twod_visualization(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.show_circles = True  # Flag to toggle circle visibility
        self.unknown_node = [400, 400]

        # Load the trained model
        self.model = load('random_forest_Model.joblib')

        # UI setup
        label = QLabel('Visualize Distance Predictions')
        self.error_label = QLabel('Error: N/A')  # Label to display the error
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

    def find_closest_measurements(self, calculated_distances):
        """
        For each calculated distance, find the closest GPSDistance in the dataset and select its RSSI and SNR values.

        Parameters:
        - calculated_distances: An array of distances calculated between an unknown node and known nodes.
        - data: The dataset containing GPSDistance, RSSI, and SNR values.

        Returns:
        - A DataFrame with the closest GPSDistance, RSSI, and SNR values for each calculated distance.
        """
        data = pd.read_csv('./output_large.csv')
        closest_values = {'Node': [], 'CalculatedDistance': [], 'ClosestGPSDistance': [], 'RSSI': [], 'SNR': []}

        for i, distance in enumerate(calculated_distances):
            closest_row = data.iloc[(data['GPSDistance'] - distance).abs().argsort()[:1]]
            rssi = closest_row['RSSI'].values[0]
            snr = closest_row['SNR'].values[0]
            closest_gps_distance = closest_row['GPSDistance'].values[0]

            closest_values['Node'].append(f'Node {i+1}')
            closest_values['CalculatedDistance'].append(distance)
            closest_values['ClosestGPSDistance'].append(closest_gps_distance)
            closest_values['RSSI'].append(rssi)
            closest_values['SNR'].append(snr)

        return pd.DataFrame(closest_values)

    def circle_intersection_points(self, center, radius, points):
        """
        Filters points to those that lie within a given circle.

        Parameters:
        - center: The (x, y) coordinates of the circle's center
        - radius: The radius of the circle
        - points: An array of points to filter

        Returns:
        - An array of points lying within the circle
        """
        return points[np.linalg.norm(points - np.array(center), axis=1) <= radius]

    def draw_circle(self, ax, center, radius, color='b', alpha=0.1):
        """
        Draws a circle on the given Axes object.

        Parameters:
        - ax: The Axes object where the circle will be drawn.
        - center: A tuple (x, y) representing the circle's center.
        - radius: The radius of the circle.
        - color: (Optional) The color of the circle.
        - alpha: (Optional) The transparency of the circle.
        """
        circle = plt.Circle(center, radius, color=color, alpha=alpha)
        ax.add_patch(circle)

    def plot_circles_and_intersection(self, centers, radii, points):
        """
        Plots the circles and the intersection points.

        Parameters:
        - centers: A list of tuples representing the centers of the circles.
        - radii: A list of radii for the circles.
        - points: An array of points representing the intersection.
        """
        if self.show_circles:
            # Draw each circle
            for center, radius in zip(centers, radii):
                self.draw_circle(self.matplotlib_canvas.axes, center, radius)

        # Plot intersection points if available
        if points.size > 0:
            x = node_dict['x']
            y = node_dict['y']
            self.matplotlib_canvas.axes.scatter(points[:,0], points[:,1], color='r', s=10)
            distances = np.linalg.norm(points - np.array([x, y]), axis=1)
            mean_error = np.mean(distances)
            self.error_label.setText(f'Error: {mean_error:.2f}')
        else:
            self.error_label.setText('Error: N/A')


        if node_dict['x'] != -9999 and node_dict['y'] != -9999:
            x = node_dict['x']
            y = node_dict['y']
            self.matplotlib_canvas.axes.scatter(x, y, s=100, color='blue', label='Unknown Object')
    
        self.matplotlib_canvas.axes.set_xlabel('X-axis')
        self.matplotlib_canvas.axes.set_ylabel('Y-axis')
        self.matplotlib_canvas.axes.set_title('Distance Predictions')
        self.matplotlib_canvas.draw()

    def toggle_circles(self):
        self.show_circles = not self.show_circles
        self.display_predictions()

    def display_predictions(self):
        # Known nodes positions
        nodes = np.array([[0, 0], [0, network_size], [ network_size, 0], [ network_size, network_size]])

        self.matplotlib_canvas.axes.cla()
        predicted_distances = []

        if len(node_dict["nodevals"]) > 3:
            for key, value in node_dict["nodevals"].items():
                rssi = value['rssi']
                snr = value['snr']
                # Create a DataFrame with the appropriate feature names
                model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

                # Predict the distance using the DataFrame'
                predicted_distance = self.model.predict(model_input)[0]
                print("For node" + key + ", the prediction is " + str(predicted_distance) + " meters")
                predicted_distances.append(predicted_distance)

                node_position = nodes[int(key)-1]

                self.matplotlib_canvas.axes.scatter(*node_position, s=100, label=f'Node {int(key)-1} Pred')

            # Generating points within the expected intersection region
            num_points = 100000
            points = np.random.rand(num_points, 2) * network_size  # Generates points within [0, 1000] in 2D space
            for center, radius in zip(nodes, predicted_distances):
                points = self.circle_intersection_points(center, radius, points)

            # start test
            buffer = 0

            # while not points.size > 0:
            #     predicted_distances = []
            #     buffer += 10
            #     for key, value in node_dict["nodevals"].items():
            #         rssi = value['rssi']
            #         snr = value['snr']
            #         # Create a DataFrame with the appropriate feature names
            #         model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

            #         # Predict the distance using the DataFrame
            #         predicted_distance = self.model.predict(model_input)[0]
            #         predicted_distances.append(predicted_distance + buffer)
            #         node_position = nodes[int(key)-1]
            #         self.matplotlib_canvas.axes.scatter(*node_position, s=100, label=f'Node {int(key)-1} Pred')

            #     # Generating points within the expected intersection region
            #     num_points = 100000
            #     points = np.random.rand(num_points, 2) * 1000  # Generates points within [0, 1000] in 2D space

            #     for center, radius in zip(nodes, predicted_distances):
            #         points = self.circle_intersection_points(center, radius, points)
            # end test

            self.plot_circles_and_intersection(nodes, predicted_distances, points)
