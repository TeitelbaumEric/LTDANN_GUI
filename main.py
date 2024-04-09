import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from initialization_screen import InitializationScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("./style_sheet/styles.qss", "r") as file:
        app.setStyleSheet(file.read())

    main_window = QMainWindow()
    initialization_screen = InitializationScreen(main_window)
    main_window.setCentralWidget(initialization_screen)
    main_window.showMaximized()

    app.exec()
