from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create buttons
        self.button1 = QPushButton('Check Receiver Health', self)
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
        self.setCentralWidget(QLabel('Screen 1'))

    def show_screen2(self):
        self.setCentralWidget(QLabel('Screen 2'))


if __name__ == "__main__":
    app = QApplication([])

    main_window = MainScreen()
    main_window.show()

    app.exec()
