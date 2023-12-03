import gui_common
import gui_utils
import arduboy.device
import constants

from arduboy.constants import *
from arduboy.common import *

from PyQt6 import QtGui
from PyQt6.QtWidgets import  QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt, QThread

from PIL import Image


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
            self.image_done.emit(arduboy.image.bin_to_pilimage(self.image, raw=True))
        except Exception as ex:
            self.on_error.emit(ex)

class TitleImageWidget(QLabel):
    onimage_bytes = pyqtSignal(bytearray)

    def __init__(self, parent=None, scale=1, modifiable=True):
        super().__init__(parent)
        self.modifiable = modifiable
        if modifiable:
            self.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))  # Set cursor to pointing hand
        self.setScaledContents(True)  # Scale the image to fit the label
        self.set_image_bytes(None)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(SCREEN_WIDTH * scale, SCREEN_HEIGHT * scale)
        self.setStyleSheet(f"background-color: {gui_common.SUBDUEDCOLOR}")
    
    def set_image_pil(self, image_pil):
        # Yes, this is a lot of conversion, I don't care. There's a function that magically converts
        # images into just the right format, might as well just use it.
        self.set_image_bytes(arduboy.image.pilimage_to_bin(image_pil))

    # NOTE: should be the simple 1024 bytes directly from the parsing! Anytime image bytes are needed, that's what is expected!
    def set_image_bytes(self, image_bytes):
        if image_bytes is not None and sum(image_bytes) > 0:
            self.image_bytes = image_bytes
            self.worker = ImageConvertWorker(image_bytes)
            self.worker.image_done.connect(self._finish_image)
            self.worker.on_error.connect(lambda ex: gui_utils.show_exception(ex))
            self.worker.start()
        else:
            self.image_bytes = None
            self.setPixmap(QtGui.QPixmap())
            if self.modifiable:
                self.setText("Choose image")
            else:
                self.setText("No image")
    
    def _finish_image(self, b):
        qt_image = QtGui.QImage(b, SCREEN_WIDTH, SCREEN_HEIGHT, QtGui.QImage.Format.Format_Grayscale8)
        pixmap = QtGui.QPixmap(qt_image) 
        self.setPixmap(pixmap)
        self.setText("")

    def mousePressEvent(self, event):
        if not self.modifiable:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # Open a file select dialog, resize+crop the image to exactly 128x64, then set it as self and pass it along!
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Title Image File", "", constants.IMAGE_FILEFILTER)
            if file_path:
                # We convert to bytes to send over the wire (emit) and to set our own image. Yes, we will be converting it back in set_image_bytes
                image_bytes = arduboy.image.pilimage_to_bin(Image.open(file_path)) 
                self.set_image_bytes(image_bytes)
                self.onimage_bytes.emit(image_bytes)

