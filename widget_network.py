import arduboy.image

import constants
import gui_common
import gui_utils
import widgets_common
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGroupBox, QMessageBox, QLabel
from PyQt6.QtWidgets import QGraphicsPixmapItem, QFileDialog, QHBoxLayout, QPlainTextEdit, QCheckBox, QLineEdit, QComboBox
from PyQt6.QtGui import QPixmap, QPen, QRegularExpressionValidator
from PyQt6.QtCore import QRectF, Qt, QRegularExpression
from PIL import Image

class NetworkBrowseWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)

        download_icon = QLabel("⬇️")
        gui_common.set_emoji_font(download_icon, 15)
        download_icon.setStyleSheet(f"color: {gui_common.SUCCESSCOLOR}")
        controls_layout.addWidget(download_icon)
        
        self.load_button = QPushButton("   Load From Website   ")
        self.load_button.setStyleSheet("font-weight: bold")
        controls_layout.addWidget(self.load_button)

        self.device_select = QComboBox()
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOY)
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYFX)
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.device_select.setStyleSheet("font-weight: bold")
        self.device_select.setToolTip("Show games compatible with the given device")
        controls_layout.addWidget(self.device_select)

        website_link = widgets_common.ClickableLink("Cart builder website", constants.OFFICIAL_INDEX)
        website_link.setFixedHeight(self.load_button.sizeHint().height())
        # website_link.setFixedWidth(125)
        controls_layout.addWidget(website_link)
        # controls_layout.setStretchFactor(website_link, 50)
        # self.license_help.setFixedWidth(125)

        self.gameslist = QGroupBox("Whatever")

        about_text = QLabel("Data provided (with permission) by the semi-official cart builder website")
        about_text.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}")

        full_layout.addWidget(controls_widget)
        full_layout.addWidget(self.gameslist)
        full_layout.addWidget(about_text)
        full_layout.setStretchFactor(controls_widget, 0)
        full_layout.setStretchFactor(self.gameslist, 1)
        full_layout.setStretchFactor(about_text, 0)

        self.setLayout(full_layout)
