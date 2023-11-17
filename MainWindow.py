from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget

class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window properties
        self.setWindowTitle("LTDANN")
        self.setGeometry(100, 100, 600, 400)  # Set the window size

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

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(back_button)
        self.setLayout(layout)

    def back_to_main(self):
        self.main_window.setCentralWidget(MainScreen())

class Screen2(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        label = QLabel('Show object localization')

        back_button = QPushButton('Back to Main Screen', self)
        back_button.clicked.connect(self.back_to_main)

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