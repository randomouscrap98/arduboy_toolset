import constants
import gui_utils
import utils
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGroupBox
from PyQt6.QtWidgets import QGraphicsPixmapItem, QFileDialog, QHBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QPixmap

# A fully self contained widget which can upload and backup EEPROM from arduboy
class ImageConvertWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()

        # Image display + config portion is hbox layout
        top_widget = QGroupBox("Image converter")
        top_layout = QHBoxLayout()
        top_widget.setLayout(top_layout)

        # Image display by itself is another vbox
        # ---------------------------------------
        image_widget = QWidget()
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_widget.setLayout(image_layout)

        # You put stuff in the scene. We go ahead and add our base image item
        self.image_scene = QGraphicsScene()
        self.image_item = QGraphicsPixmapItem()
        self.image_scene.addItem(self.image_item)

        # The view is a window into a scene, this is what you put into the layout?
        self.image_view = QGraphicsView(self.image_scene)

        image_layout.addWidget(self.image_view)

        # Config display another vbox
        # ---------------------------------------
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        config_widget.setLayout(config_layout)

        self.select_image_button = QPushButton("Select Image")
        self.select_image_button.clicked.connect(self.do_load_image)
        config_layout.addWidget(self.select_image_button)

        # Lower controls for config
        # ---------------------------------------
        controls_widget = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_widget.setLayout(controls_layout)

        self.convert_button = QPushButton("Convert ↓")
        self.convert_button.setToolTip("Convert directly to code and place in the textbox below")
        self.convert_button.clicked.connect(self.do_convert)
        controls_layout.addWidget(self.convert_button)

        self.convert_file_button = QPushButton("Convert to .h")
        self.convert_file_button.setToolTip("Convert to code and save to a .h file with appropriate boilerplate")
        self.convert_file_button.clicked.connect(self.do_convert_file)
        controls_layout.addWidget(self.convert_file_button)

        self.convert_fx_button = QPushButton("Convert to fxdata")
        self.convert_fx_button.setToolTip("Convert to a binary blob usable with the FX libraries and save to a .bin file")
        self.convert_fx_button.clicked.connect(self.do_convert_fx)
        controls_layout.addWidget(self.convert_fx_button)
    
        config_layout.addWidget(controls_widget)

        # Setup the output box
        # ---------------------------------------
        self.output_box = QPlainTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("Converted image code goes here")
        self.output_box.setToolTip("Converted image code goes here")

        # Put all the junk together
        # ---------------------------------------
        top_layout.addWidget(image_widget)
        top_layout.addWidget(config_widget)
        top_layout.setStretchFactor(image_widget, 1)
        top_layout.setStretchFactor(config_widget, 3)

        full_layout.addWidget(top_widget)
        full_layout.addWidget(self.output_box)

        self.setLayout(full_layout)
    

    def do_load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", constants.IMAGE_FILEFILTER)
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_item.setPixmap(pixmap)
            rect = pixmap.rect()
            self.image_view.setSceneRect(0, 0, rect.width(), rect.height())
            debug_actions.global_debug.add_action_str(f"Loaded image into converter: {file_path}")
    
    def do_convert(self):
        pass

    def do_convert_file(self):
        pass

    def do_convert_fx(self):
        pass