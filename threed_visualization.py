import time
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
node_dict = {"nodevals": {}, 'x': -9999, "y" : -9999}


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111, projection='3d')
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
                    
                    self.new_data.emit(node_dict)
                except IndexError:
                    pass

    # def parse_transmitter_data(self, line):
    #     transmitter_data = {}
    #     entries = line.split(',')
    #     print(entries)
    #     for entry in entries:
    #         parts = entry.split(',')
    #         print(parts)
    #         if len(parts) == 3:
    #             transmitter_id = int(parts[0])
    #             rssi = int(parts[1])
    #             snr = float(parts[2])
    #             try:
    #                 x = float(parts[3])
    #                 y = float(parts[4])
    #                 unknown_node["x"] = x
    #                 unknown_node['y'] = y
    #             except:
    #                 pass
    #             transmitter_data[transmitter_id] = {'rssi': rssi, 'snr': snr}
    #     return transmitter_data

class Threed_visualization(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.show_spheres = True  # Flag to toggle sphere visibility

        self.unknown_node = [400, 400, 0]

        # Load the trained model
        self.model = load('random_forest_ModelV2.joblib')

        # UI setup
        label = QLabel('Visualize Distance Predictions')
        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Buttons for toggling sphere visibility and randomizing node location
        self.toggle_spheres_button = QPushButton('Toggle Spheres Visibility', self)
        self.toggle_spheres_button.clicked.connect(self.toggle_spheres)
        self.randomize_node_button = QPushButton('Randomize Node & Recalculate', self)
        # self.randomize_node_button.clicked.connect(self.randomize_and_redisplay)

        # Create the Matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas(self)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.matplotlib_canvas)
        layout.addWidget(self.toggle_spheres_button)  # Add toggle visibility button
        layout.addWidget(self.randomize_node_button)  # Add randomize node button
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

    def sphere_intersection_points(self, center, radius, points):
        """
        Filters points to those that lie within a given sphere.

        Parameters:
        - center: The (x, y, z) coordinates of the sphere's center
        - radius: The radius of the sphere
        - points: An array of points to filter

        Returns:
        - An array of points lying within the sphere
        """
        return points[np.linalg.norm(points - np.array(center), axis=1) <= radius]

    def draw_sphere(self, ax, center, radius, color='b', alpha=0.1):
        """
        Draws a wireframe sphere on the given Axes3D object.

        Parameters:
        - ax: The Axes3D object where the sphere will be drawn.
        - center: A tuple (x, y, z) representing the sphere's center.
        - radius: The radius of the sphere.
        - color: (Optional) The color of the sphere.
        - alpha: (Optional) The transparency of the sphere.
        """
        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
        x = center[0] + radius * np.cos(u) * np.sin(v)
        y = center[1] + radius * np.sin(u) * np.sin(v)
        z = center[2] + radius * np.cos(v)
        ax.plot_wireframe(x, y, z, color=color, alpha=alpha)

    def plot_spheres_and_intersection(self, centers, radii, points):
        """
        Plots the spheres and the intersection points.

        Parameters:
        - centers: A list of tuples representing the centers of the spheres.
        - radii: A list of radii for the spheres.
        - points: An array of points representing the intersection.
        """
        if self.show_spheres:
            # Draw each sphere
            for center, radius in zip(centers, radii):
                self.draw_sphere(self.matplotlib_canvas.axes, center, radius)

        # Plot intersection points if available
        if points.size > 0:
            self.matplotlib_canvas.axes.scatter(points[:,0], points[:,1], points[:,2], color='r', s=10)
        
        if node_dict['x'] != -9999 and node_dict['y'] != -9999:
            x = node_dict['x']
            y = node_dict['y']
            print(node_dict['x'],  node_dict['y'])
            self.matplotlib_canvas.axes.scatter(x, y, 1000, s=100, color='blue', label='Unknown Object')

        self.matplotlib_canvas.axes.set_xlabel('X-axis')
        self.matplotlib_canvas.axes.set_ylabel('Y-axis')
        self.matplotlib_canvas.axes.set_zlabel('Z-axis')
        self.matplotlib_canvas.axes.set_title('Distance Predictions')
        self.matplotlib_canvas.draw()

    def toggle_spheres(self):
        self.show_spheres = not self.show_spheres
        self.display_predictions()

    # def randomize_and_redisplay(self):
    #     # Randomize unknown node position within [0, 1000] range in 3D space
    #     self.unknown_node = [np.random.rand() * 400 + 200, np.random.rand() * 400 + 200, 0]
    #     print(self.unknown_node)
    #     self.display_predictions()

    def display_predictions(self):
        # Known nodes positions
        nodes = np.array([[0, 0, 0], [0, 200, 0], [200, 0, 0], [200, 200, 0]])

        self.matplotlib_canvas.axes.cla()
        predicted_distances = []

        if len(node_dict["nodevals"]) > 3:
            for key, value in node_dict["nodevals"].items():
                rssi = value['rssi']
                snr = value['snr']
                # Create a DataFrame with the appropriate feature names
                model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

                # Predict the distance using the DataFrame
                predicted_distance = self.model.predict(model_input)[0]
                predicted_distances.append(predicted_distance)

                node_position = nodes[int(key)-1]

                self.matplotlib_canvas.axes.scatter(*node_position, s=100, label=f'Node {int(key) -1 } Pred')

            # Generating points within the expected intersection region
            num_points = 100000
            points = np.random.rand(num_points, 3) * 200  # Generates points within [0, 1000] in 3D space
            points += np.random.rand(num_points, 3) * -200
            for center, radius in zip(nodes, predicted_distances):
                points = self.sphere_intersection_points(center, radius, points)

            # start test
            buffer = 0 
            
            while not points.size > 0:
                predicted_distances = []
                buffer += 10
                for key, value in node_dict["nodevals"].items():
                    rssi = value['rssi']
                    snr = value['snr']
                    # Create a DataFrame with the appropriate feature names
                    model_input = pd.DataFrame({'RSSI': [rssi], 'SNR': [snr]})

                    # Predict the distance using the DataFrame
                    predicted_distance = self.model.predict(model_input)[0]
                    predicted_distances.append(predicted_distance + buffer)
                    node_position = nodes[int(key)-1]
                    self.matplotlib_canvas.axes.scatter(*node_position, s=100, label=f'Node {int(key) -1 } Pred')

                # Generating points within the expected intersection region
                num_points = 100000
                points = np.random.rand(num_points, 3) * 200  # Generates points within [0, 1000] in 3D space
                points += np.random.rand(num_points, 3) * -200

                for center, radius in zip(nodes, predicted_distances):
                    points = self.sphere_intersection_points(center, radius, points)
            # end test 
                    

            self.plot_spheres_and_intersection(nodes, predicted_distances, points)
        

            # # Set tick markers for x, y, and z axes
            # self.matplotlib_canvas.axes.set_xticks([0, 250, 500, 750, 1000])
            # self.matplotlib_canvas.axes.set_yticks([0, 250, 500, 750, 1000])
            # self.matplotlib_canvas.axes.set_zticks([0, 250, 500, 750, 1000])

            # # Add grid lines
            # self.matplotlib_canvas.axes.grid(True)

            # # Customize tick labels (optional)
            # self.matplotlib_canvas.axes.set_xticklabels(['0', '250', '500', '750', '1000'])
            # self.matplotlib_canvas.axes.set_yticklabels(['0', '250', '500', '750', '1000'])
            # self.matplotlib_canvas.axes.set_zticklabels(['0', '250', '500', '750', '1000'])
            # self.matplotlib_canvas.draw()


