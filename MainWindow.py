from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem, QWidget, QGraphicsSimpleTextItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

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

        back_button = QPushButton('Back', self)
        back_button.clicked.connect(self.back_to_main)

        back_button.setMaximumWidth(100)
        back_button.setMaximumHeight(30)

        # Create a graphics view to display the node network
        scene = QGraphicsScene(self)
        view = QGraphicsView(scene, self)

        # Add nodes (transmitters and receiver) to the scene
        transmitter1 = QGraphicsEllipseItem(0, 0, 50, 50)
        transmitter2 = QGraphicsEllipseItem(0, 100, 50, 50)
        transmitter3 = QGraphicsEllipseItem(0, 200, 50, 50)
        transmitter4 = QGraphicsEllipseItem(0, 300, 50, 50)
        receiver = QGraphicsEllipseItem(100, 100, 50, 50)

        # Set labels for nodes
        transmitter1_label = QGraphicsSimpleTextItem("T1", transmitter1)
        transmitter2_label = QGraphicsSimpleTextItem("T2", transmitter2)
        transmitter3_label = QGraphicsSimpleTextItem("T3", transmitter3)
        transmitter4_label = QGraphicsSimpleTextItem("T4", transmitter4)
        receiver_label = QGraphicsSimpleTextItem("R", receiver)

        scene.addItem(transmitter1)
        scene.addItem(transmitter2)
        scene.addItem(transmitter3)
        scene.addItem(transmitter4)
        scene.addItem(receiver)

        # Set labels' positions
        transmitter1_label.setPos(5, 5)
        transmitter2_label.setPos(5, 105)
        transmitter3_label.setPos(5, 205)
        transmitter4_label.setPos(5, 305)
        receiver_label.setPos(105, 105)

        # Add connections between nodes with green lines
        connection1 = QGraphicsLineItem(50, 25, 100, 125)
        connection2 = QGraphicsLineItem(50, 125, 100, 125)
        connection3 = QGraphicsLineItem(50, 225, 100, 125)
        connection4 = QGraphicsLineItem(50, 325, 100, 125)

        for connection in [connection1, connection2, connection3, connection4]:
            connection.setPen(QColor("green"))
            scene.addItem(connection)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(back_button)
        layout.addWidget(view)
        self.setLayout(layout)

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

class Screen2(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        label = QLabel('Show object localization')

        back_button = QPushButton('Back', self)
        back_button.clicked.connect(self.back_to_main)

        back_button.setMaximumWidth(100)
        back_button.setMaximumHeight(30)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(back_button)
        self.setLayout(layout)

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

if __name__ == "__main__":
    app = QApplication([])

    main_window = MainScreen()
    main_window.show()

    app.exec()