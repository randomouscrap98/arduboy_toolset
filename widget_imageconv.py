import constants
import gui_utils
import utils

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton

# A fully self contained widget which can upload and backup EEPROM from arduboy
class ImageConvertWidget(QWidget):

    def __init__(self):
        super().__init__()
