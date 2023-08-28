import arduboy.image

import constants
import gui_utils
import utils
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGroupBox
from PyQt6.QtWidgets import QGraphicsPixmapItem, QFileDialog, QHBoxLayout, QPlainTextEdit, QCheckBox
from PyQt6.QtGui import QPixmap, QPen, QColor
from PyQt6.QtCore import QRectF, Qt
from PIL import Image

# A fully self contained widget which can upload and backup EEPROM from arduboy
class ImageConvertWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.rects = []
        self.pilimage = None
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
        self.image_view = gui_utils.CustomGraphicsView()
        self.image_view.setScene(self.image_scene)
        self.image_view.set_zoom(4.0)
        # self.image_view.setObjectName("imageviewer")
        # self.image_view.setStyleSheet("#imageviewer { background-color: red }")
        self.image_view.setStyleSheet(f"background-color: {gui_utils.SUBDUEDCOLOR}")

        image_layout.addWidget(self.image_view)

        # Config display another vbox
        # ---------------------------------------
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        config_widget.setLayout(config_layout)

        self.select_image_button = QPushButton("Select Image")
        self.select_image_button.clicked.connect(self.do_load_image)
        config_layout.addWidget(self.select_image_button)

        self.tilesize = gui_utils.WidthHeightWidget()
        tilesize_container, self.tilesize_cb = gui_utils.make_toggleable_element("Tiled image", self.tilesize, nostretch=True)
        config_layout.addWidget(tilesize_container)
        self.tilesize.onchange.connect(self.recalculate_rects)
        self.tilesize_cb.stateChanged.connect(self.recalculate_rects)

        self.spacing_number = gui_utils.NumberOnlyLineEdit()
        self.spacing_number.setText("0")
        spacing_container, self.spacing_cb = gui_utils.make_toggleable_element("Tile spacing", self.spacing_number, nostretch=True)
        config_layout.addWidget(spacing_container)
        self.spacing_number.textChanged.connect(self.recalculate_rects)
        self.spacing_cb.stateChanged.connect(self.recalculate_rects)

        self.mask_cb = QCheckBox("Use transparency to make mask")
        self.mask_cb.setChecked(True)
        config_layout.addWidget(self.mask_cb)
        self.mask_cb.stateChanged.connect(self.recalculate_rects)

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
        top_layout.setStretchFactor(image_widget, 2)
        top_layout.setStretchFactor(config_widget, 3)

        full_layout.addWidget(top_widget)
        full_layout.addWidget(self.output_box)
        full_layout.setStretchFactor(top_widget, 3)
        full_layout.setStretchFactor(self.output_box, 2)

        self.setLayout(full_layout)
    
    def get_tileconfig(self):
        result = arduboy.image.TileConfig()
        if self.spacing_cb.isChecked():
            try:
                result.spacing = int(self.spacing_number.text())
            except:
                logging.warning(f"Bad spacing value: {self.spacing_number.text()}, not setting spacing!")
        if self.tilesize_cb.isChecked():
            try:
                result.width, result.height = self.tilesize.get_values()
            except:
                logging.warning(f"Bad width/height values, not setting tiling!")
        result.use_mask = self.mask_cb.isChecked()
        return result

    def recalculate_rects(self):
        if not self.pilimage:
            logging.error("No image set in image converter widget, can't recalculate rectangles!")
            return
        # gather all the relevant values
        tileconfig = self.get_tileconfig()
        # Clear out the old rects
        for r in self.rects:
            self.image_scene.removeItem(r)
        self.rects = []
        pen = QPen(Qt.GlobalColor.red, 0.2, Qt.PenStyle.SolidLine)

        # Now let's figure out where all the rects should go!
        spriteWidth, spriteHeight, hframes, vframes = arduboy.image.expand_tileconfig(tileconfig, self.pilimage)
        spacing = tileconfig.spacing

        fy = spacing
        for _ in range(vframes):
            fx = spacing
            for _ in range(hframes):
                rect = QRectF(fx, fy, spriteWidth, spriteHeight)
                self.rects.append(self.image_scene.addRect(rect, pen=pen))
                fx += spriteWidth + spacing
            fy += spriteHeight + spacing

    def do_load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", constants.IMAGE_FILEFILTER)
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_item.setPixmap(pixmap)
            if self.pilimage:
                self.pilimage.close()
            self.pilimage = Image.open(file_path)
            rect = pixmap.rect()
            self.image_view.setSceneRect(0, 0, rect.width(), rect.height())
            debug_actions.global_debug.add_action_str(f"Loaded image into converter: {file_path}")
            self.recalculate_rects()
    
    def do_convert(self):
        pass

    def do_convert_file(self):
        pass

    def do_convert_fx(self):
        pass