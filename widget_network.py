import arduboy.image

import constants
import gui_common
import gui_utils
import widgets_common
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGroupBox, QMessageBox
from PyQt6.QtWidgets import QGraphicsPixmapItem, QFileDialog, QHBoxLayout, QPlainTextEdit, QCheckBox, QLineEdit
from PyQt6.QtGui import QPixmap, QPen, QRegularExpressionValidator
from PyQt6.QtCore import QRectF, Qt, QRegularExpression
from PIL import Image

# A fully self contained widget which can upload and backup EEPROM from arduboy
class NetworkBrowseWidget(QWidget):

    def __init__(self):
        super().__init__()