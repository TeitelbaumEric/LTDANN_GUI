import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QWidget, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal
from tdoa_sim.TDoA import *
from random import randint
from joblib import load
import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window properties
        self.setWindowTitle("LTDANN")
        self.setGeometry(100, 100, 700, 500)  # Set the window size

        # Create buttons
        self.button1 = QPushButton('Check Network Health', self)
        self.button2 = QPushButton('Visualize Object Localization', self)
        self.button3 = QPushButton('Visualize Neural Network', self)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        # Connect buttons to their respective functions
        self.button1.clicked.connect(self.show_screen1)
        self.button2.clicked.connect(self.show_screen2)
        self.button3.clicked.connect(self.show_screen3)

    def show_screen1(self):
        self.setCentralWidget(Screen1(self))

    def show_screen2(self):
        self.setCentralWidget(Screen2(self))

    def show_screen3(self):
        self.setCentralWidget(Screen3(self))

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

class NetworkWorker(QThread):
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


class Screen3(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.show_spheres = True  # Flag to toggle sphere visibility

        self.unknown_node = [500,500,500] 

        # Load the trained model
        self.model = load('gradient_boosting_regressor.joblib')

        # UI setup
        label = QLabel('Visualize Distance Predictions')
        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

        # Buttons for toggling sphere visibility and randomizing node location
        self.toggle_spheres_button = QPushButton('Toggle Spheres Visibility', self)
        self.toggle_spheres_button.clicked.connect(self.toggle_spheres)
        self.randomize_node_button = QPushButton('Randomize Node & Recalculate', self)
        self.randomize_node_button.clicked.connect(self.randomize_and_redisplay)

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

        # For demonstration, call a method to visualize nodes and predictions
        self.display_predictions()

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

    def find_closest_measurements(self, calculated_distances):
        """
        For each calculated distance, find the closest GPSDistance in the dataset and select its RSSI and SNR values.
        
        Parameters:
        - calculated_distances: An array of distances calculated between an unknown node and known nodes.
        - data: The dataset containing GPSDistance, RSSI, and SNR values.
        
        Returns:
        - A DataFrame with the closest GPSDistance, RSSI, and SNR values for each calculated distance.
        """
        data = pd.read_csv('./output.csv')
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

        self.matplotlib_canvas.axes.set_xlabel('X-axis')
        self.matplotlib_canvas.axes.set_ylabel('Y-axis')
        self.matplotlib_canvas.axes.set_zlabel('Z-axis')
        self.matplotlib_canvas.axes.set_title('Distance Predictions')
        self.matplotlib_canvas.draw()

    def toggle_spheres(self):
        self.show_spheres = not self.show_spheres
        self.display_predictions()

    def randomize_and_redisplay(self):
        # Randomize unknown node position within [0, 1000] range in 3D space
        self.unknown_node = np.random.rand(3) * 600 - 300  # Scale and shift to get [-300, 300]
        print(self.unknown_node)
        self.display_predictions()

    def display_predictions(self):
        # Known nodes positions
        nodes = np.array([[0, 0, 0], [0, 1000, 0], [1000, 0, 0], [1000, 1000, 0]])

        # # Unknown node positionF
        # unknown_node = np.array([500, 500, 500])

        # Calculate distances from the unknown node to each known node
        distances = np.array([euclidean(node, self.unknown_node) for node in nodes])
        closest_measurements = self.find_closest_measurements(distances)

        self.matplotlib_canvas.axes.cla()

        predicted_distances = []

        for index, row in closest_measurements.iterrows():
                rssi = row['RSSI']
                snr = row['SNR']

                # If your model expects input as a single array per prediction,
                # and assuming no additional preprocessing is needed:
                model_input = np.array([[rssi, snr]])
                
                # Predict the distance
                predicted_distance = self.model.predict(model_input)[0]
                predicted_distances.append(predicted_distance)
                # Visualization: Draw a point or other marker at the predicted distance
                # Assuming you want to visualize the prediction in relation to the original node position
                # This part is conceptual. The actual implementation will depend on your visualization logic.
                node_position = nodes[index]
                # This is a simplification. You might want to adjust the visualization
                # to clearly represent the predicted distance.
                self.matplotlib_canvas.axes.scatter(*node_position, s=100, label=f'Node {index + 1} Pred')
        
        # Generating points within the expected intersection region
        num_points = 100000
        points = np.random.rand(num_points, 3) * 1000  # Generates points within [0, 1000] in 3D space
        points += np.random.rand(num_points, 3) * -1000

        for center, radius in zip(nodes, predicted_distances):
            points = self.sphere_intersection_points(center, radius, points)

        self.plot_spheres_and_intersection(nodes, predicted_distances, points)
    
        

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainScreen()
    main_window.show()

    app.exec()