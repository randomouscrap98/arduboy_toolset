import logging
import os
import sys
import constants
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget
from PyQt5 import QtGui


def main():

    # Some initial setup
    try:
        # This apparently only matters for windows and for GUI apps
        from ctypes import windll  # Only exists on Windows.
        myappid = 'Haloopdy.ArduboyToolset' # 'mycompany.myproduct.subproduct.version'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_file("icon.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


def resource_file(name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, 'appresource', name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle(f"Arduboy Toolset v{constants.VERSION}")
        self.setGeometry(100, 100, 400, 300)  # Set a reasonable window size

        # Create a vertical layout
        layout = QVBoxLayout()

        # Create widgets to add to the layout
        coninfo = ConnectionInfo()
        tabs = ActionTable()

        # Add widgets to the layout
        layout.addWidget(coninfo)
        layout.addWidget(tabs)

        layout.setStretchFactor(coninfo, 0)
        layout.setStretchFactor(tabs, 1)

        # Set the layout as the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class ConnectionInfo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()

        label = QLabel("Label")
        layout.addWidget(label)

        self.setLayout(layout)


# The table of actions which can be performed. Has functions to enable/disable parts of itself
# based on common external interactions
class ActionTable(QTabWidget):
    def __init__(self):
        super().__init__()

        # Create and add tabs
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        
        self.addTab(tab1, "Sketch")
        self.addTab(tab2, "Flashcart")
        self.addTab(tab3, "Utilities")

        # Create layouts for each tab
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()

        # Add widgets to tab1
        label1 = QLabel("This is Tab 1")
        layout1.addWidget(label1)

        # Add widgets to tab2
        label2 = QLabel("This is Tab 2")
        button2 = QPushButton("Button in Tab 2")
        layout2.addWidget(label2)
        layout2.addWidget(button2)

        # Add widgets to tab3
        label3 = QLabel("This is Tab 3")
        button3 = QPushButton("Button in Tab 3")
        layout3.addWidget(label3)
        layout3.addWidget(button3)

        # Set layouts for each tab
        tab1.setLayout(layout1)
        tab2.setLayout(layout2)
        tab3.setLayout(layout3)


if __name__ == "__main__":
    main()
