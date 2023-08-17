import utils
import gui_utils

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem, QListWidget, QFileDialog, QAbstractItemView, QLineEdit
from PyQt6 import QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QThread

class PackageWindow(QMainWindow):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    app = gui_utils.basic_gui_setup()
    window = PackageWindow()
    window.show()
    sys.exit(app.exec())
