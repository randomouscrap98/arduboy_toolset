import logging
import os
import sys
import constants
import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.utils
import utils
import gui_utils
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QGroupBox
from PyQt5.QtWidgets import QMessageBox, QAction, QCheckBox
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, Qt


class CrateWindow(QMainWindow):
    def __init__(self, filepath):
        super().__init__()

        self.filepath = filepath
        self.resize(800, 600)
        self.set_modified(True) # Change to false!
    
    def set_modified(self, modded = True):
        self.modified = modded
        title = f"Cart Editor - {self.filepath}"
        if modded:
            title = f"[!] {title}"
        self.setWindowTitle(title)
    
    def save(self):
        pass

    def closeEvent(self, event) -> None:
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"There are unsaved changes to {self.filepath}. Do you want to save your work before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save()
            elif reply == QMessageBox.Cancel:
                event.ignore()  # Ignore the close event
                return

        event.accept()  # Allow the close event to proceed