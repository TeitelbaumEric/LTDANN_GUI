import sys
from PySide6.QtWidgets import QApplication
from main_screen import MainScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("styles.qss", "r") as file:
        app.setStyleSheet(file.read())

    main_window = MainScreen()
    main_window.show()

    sys.exit(app.exec())

