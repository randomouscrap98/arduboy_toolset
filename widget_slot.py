import arduboy.fxcart

import gui_utils
import constants
import debug_actions

from arduboy.constants import *
from arduboy.common import *

from typing import List
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem, QListWidget, QFileDialog, QAbstractItemView, QLineEdit
from PyQt6 import QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QThread
from PIL import Image

# Info input field's length limit. Just the field, not the data (though apparently the data is truncated
# when placed in the field)
INFO_MAX_LENGTH = 175
CATEGORY_BLOCK_STYLE = "background: rgba(255,255,0,1); color: #000; font-weight: bold"

class SlotWidget(QWidget):
    onchange = pyqtSignal()
    
    # A slot must always have SOME parsed data associated with it!
    def __init__(self, parsed: arduboy.fxcart.FxParsedSlot, force_all_fields = False):
        super().__init__()

        # !! BIG NOTE: widgets should NOT be able to change "modes", so we set up lots 
        # of mode-specific stuff in the constructor! IE a category cannot become a program etc
        self.mode = "game"

        if parsed.is_category() and not force_all_fields:
            self.mode = "category"

        self.parsed = parsed
        toplayout = QHBoxLayout()

        # ---------------------------
        #  Left section (image, data)
        # ---------------------------
        leftlayout = QVBoxLayout()
        self.leftwidget = QWidget()
        self.leftwidget.setObjectName("leftwidget")

        self.image = TitleImageWidget()
        if parsed.has_image():
            self.image.set_image_bytes(parsed.image_raw)
        self.image.onimage_bytes.connect(self.set_image_bytes)
        leftlayout.addWidget(self.image)

        # Create it now, use it later
        self.meta_label = QLabel()

        if self.mode != "category":
            datalayout = QHBoxLayout()
            datawidget = QWidget()

            self.program = gui_utils.emoji_button("💻", "Set program .hex")
            self.program.clicked.connect(self.select_program)
            datalayout.addWidget(self.program)
            self.data = gui_utils.emoji_button("🧰", "Set data .bin")
            self.data.clicked.connect(self.select_data)
            datalayout.addWidget(self.data)
            self.save = gui_utils.emoji_button("💾", "Set save .bin")
            self.save.clicked.connect(self.select_save)
            datalayout.addWidget(self.save)

            datalayout.setContentsMargins(0,0,0,0)
            datawidget.setLayout(datalayout)
            leftlayout.addWidget(datawidget)

        # This is a category then
        else:
            self.leftwidget.setStyleSheet(CATEGORY_BLOCK_STYLE)
            self.meta_label.setStyleSheet("font-weight: bold; margin-bottom: 5px")

        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gui_utils.mod_font_size(self.meta_label, 0.85)
        leftlayout.addWidget(self.meta_label)
        self.update_metalabel()

        leftlayout.setContentsMargins(0,0,0,0)
        self.leftwidget.setLayout(leftlayout)
        toplayout.addWidget(self.leftwidget)

        # And now all the editable fields!
        # ---------------------------
        #  Right section (image, data)
        # ---------------------------
        fieldlayout = QVBoxLayout()
        fieldsparent = QWidget()

        fields = []
        self.title = gui_utils.new_selflabeled_edit("Title", parsed.meta.title)
        self.title.textChanged.connect(self.title_set_event)
        fields.append(self.title)
        if self.mode != "category":
            self.version = gui_utils.new_selflabeled_edit("Version", parsed.meta.version)
            self.version.textChanged.connect(lambda t: self.do_meta_change(t, "version"))
            fields.append(self.version)
            self.author = gui_utils.new_selflabeled_edit("Author", parsed.meta.developer)
            self.author.textChanged.connect(lambda t: self.do_meta_change(t, "developer"))
            fields.append(self.author)
        self.info = gui_utils.new_selflabeled_edit("Info", parsed.meta.info)
        self.info.textChanged.connect(lambda t: self.do_meta_change(t, "info"))
        self.info.setMaxLength(INFO_MAX_LENGTH) # Max total length of meta in header is 199, this limit is just a warning
        fields.append(self.info)
        
        self.category_bigtitle = None

        if self.mode == "category":
            self.category_bigtitle = QLabel(parsed.meta.title)
            self.category_bigtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gui_utils.set_font_size(self.category_bigtitle, 16)
            self.category_bigtitle.setMinimumHeight((int)(self.title.sizeHint().height() * 2.75))
            self.category_bigtitle.setStyleSheet(CATEGORY_BLOCK_STYLE)
            gui_utils.add_children_nostretch(fieldlayout, fields, self.category_bigtitle)
        else:
            for f in fields:
                fieldlayout.addWidget(f)

        fieldlayout.setContentsMargins(0,0,0,0)
        fieldsparent.setLayout(fieldlayout)

        toplayout.addWidget(fieldsparent)

        self.setLayout(toplayout)
    
    def title_set_event(self, title):
        self.do_meta_change(title, "title")
        if self.category_bigtitle:
            self.category_bigtitle.setText(title)

    # Update the metadata label for this unit with whatever new information is stored locally
    def update_metalabel(self):
        if self.mode == "category": #self.parsed.is_category():
            self.meta_label.setText("Category ↓")
        else:
            self.meta_label.setText(f"{len(self.parsed.program_raw)}  |  {len(self.parsed.data_raw)}  |  {len(self.parsed.save_raw)}")
            if len(self.parsed.data_raw) or len(self.parsed.save_raw):
                self.leftwidget.setToolTip("FX-Enabled title")
                self.leftwidget.setStyleSheet("#leftwidget { background: rgba(255,0,0,0.15) }")
            else:
                self.leftwidget.setToolTip(None)
                self.leftwidget.setStyleSheet("")
    
    # Perform a simple meta field change. This is unfortunately DIFFERENT than the metalabel!
    def do_meta_change(self, new_text, field):
        setattr(self.parsed.meta, field, new_text) # .title = new_text
        self.onchange.emit()

    def get_slot_data(self):
        return self.parsed
    
    def select_program(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER)
        if file_path:
            # NOTE: eventually, this should set the various fields based on the parsed arduboy file!!
            parsed = arduboy.arduhex.read(file_path)
            self.parsed.program_raw = arduboy.arduhex.parse(parsed).flash_data_min()
            self.update_metalabel()
            self.onchange.emit()
            debug_actions.global_debug.add_action_str(f"Edited program for: {self.parsed.meta.title}")

    def select_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", constants.BIN_FILEFILTER)
        if file_path:
            with open(file_path, "rb") as f:
                data = f.read()
            unused_pages = count_unused_pages(data)
            if (unused_pages % (arduboy.fxcart.SAVE_ALIGNMENT // FX_PAGESIZE)) == 0:
                # Ask if the user wants to create a save out of this
                if gui_utils.yes_no("Split save section out",
                                    "The data provided appears to have a save section at the end. This is normal when using the development binary. Do you want to strip the save and add it properly to the slot (recommended)?", 
                                    self):
                    if not len(self.parsed.save_raw) or gui_utils.yes_no("Warn: Overwrite existing save",
                                                                         "Data set to truncate. However, there's already a save section, do you want to overwrite the existing save (not recommended)?", self):
                        self.parsed.save_raw = data[-unused_pages * FX_PAGESIZE:]
                    data = data[:-unused_pages * FX_PAGESIZE]
            self.parsed.data_raw = data
            self.update_metalabel()
            self.onchange.emit()
            debug_actions.global_debug.add_action_str(f"Edited FX data for: {self.parsed.meta.title}")

    def select_save(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Save File", "", constants.BIN_FILEFILTER)
        if file_path:
            with open(file_path, "rb") as f:
                self.parsed.save_raw = f.read()
            self.update_metalabel()
            self.onchange.emit()
            debug_actions.global_debug.add_action_str(f"Edited FX save for: {self.parsed.meta.title}")
    
    def set_image_bytes(self, image_bytes):
        self.parsed.image_raw = image_bytes
        self.onchange.emit()
        debug_actions.global_debug.add_action_str(f"Edited tile image for: {self.parsed.meta.title}")
    

# Perform image conversion in a worker, since it actually does take a non-trivial amount of 
# time. This speeds up the apparent rendering of the list
class ImageConvertWorker(QThread):
    image_done = pyqtSignal(bytearray)
    on_error = pyqtSignal(Exception)
    def __init__(self, image):
        super().__init__()
        self.image = image
    def run(self):
        try:
            self.image_done.emit(bin_to_pilimage(self.image, raw=True))
        except Exception as ex:
            self.on_error.emit(ex)

class TitleImageWidget(QLabel):
    onimage_bytes = pyqtSignal(bytearray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))  # Set cursor to pointing hand
        self.setScaledContents(True)  # Scale the image to fit the label
        self.set_image_bytes(None)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setStyleSheet(f"background-color: {gui_utils.SUBDUEDCOLOR}")
    
    # NOTE: should be the simple 1024 bytes directly from the parsing! Anytime image bytes are needed, that's what is expected!
    def set_image_bytes(self, image_bytes):
        if image_bytes is not None and sum(image_bytes) > 0:
            self.worker = ImageConvertWorker(image_bytes)
            self.worker.image_done.connect(self._finish_image)
            self.worker.on_error.connect(lambda ex: gui_utils.show_exception(ex))
            self.worker.start()
        else:
            self.setPixmap(QtGui.QPixmap())
            self.setText("Choose image")
    
    def _finish_image(self, b):
        qt_image = QtGui.QImage(b, SCREEN_WIDTH, SCREEN_HEIGHT, QtGui.QImage.Format.Format_Grayscale8)
        pixmap = QtGui.QPixmap(qt_image) 
        self.setPixmap(pixmap)
        self.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Open a file select dialog, resize+crop the image to exactly 128x64, then set it as self and pass it along!
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Title Image File", "", constants.IMAGE_FILEFILTER)
            if file_path:
                # We convert to bytes to send over the wire (emit) and to set our own image. Yes, we will be converting it back in set_image_bytes
                image_bytes = pilimage_to_bin(Image.open(file_path)) 
                self.set_image_bytes(image_bytes)
                self.onimage_bytes.emit(image_bytes) #arduboy.utils.pilimage_to_bin(image))

