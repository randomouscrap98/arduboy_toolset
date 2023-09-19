
import gui_utils

import os

from PyQt6 import QtGui
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QDialog, QComboBox, QLabel
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QGraphicsView, QTextBrowser, QFileDialog, QMessageBox
from PyQt6.QtGui import QIntValidator, QPainter
from PyQt6.QtCore import pyqtSignal, Qt
from typing import List


class ComboDialog(QDialog):
    """A simple dialog box that gives some text and a combobox for choosing an item"""
    def __init__(self, title: str, text: str, options: List[str]):
        super().__init__()

        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(text)
        layout.addWidget(label)

        # Create and add a combo box to the dialog
        self.combo_box = QComboBox()
        for opt in options:
            self.combo_box.addItem(opt)
        layout.addWidget(self.combo_box)

        # Create and add a button to close the dialog
        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)



class ConnectionInfo(QWidget):
    """A large, stylized connection indicator. You are required to set the connection status"""
    def __init__(self):
        super().__init__()

        self.update_count = 0

        layout = QHBoxLayout()

        self.status_picture = QLabel("$")
        gui_utils.set_emoji_font(self.status_picture, 24)
        layout.addWidget(self.status_picture)

        text_container = QWidget()
        text_layout = QVBoxLayout()

        self.status_label = QLabel("Label")
        gui_utils.set_font_size(self.status_label, 14)
        text_layout.addWidget(self.status_label)

        self.info_label = QLabel("Info")
        gui_utils.set_font_size(self.info_label, 8)
        self.info_label.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
        text_layout.addWidget(self.info_label)

        text_container.setLayout(text_layout)

        layout.addWidget(text_container)

        layout.setStretchFactor(self.status_picture, 0)
        layout.setStretchFactor(text_container, 1)
        layout.setContentsMargins(15,5,15,7)

        self.setLayout(layout)
        self.set_connected_device(None)
    
    def set_connected_device(self, device = None):
        self.update_count += 1
        if device:
            self.status_label.setText("Connected!")
            self.info_label.setText(device.display_name())
            self.status_picture.setText("✅")
            self.status_picture.setStyleSheet(f"color: {gui_utils.SUCCESSCOLOR}")
        else:
            self.status_label.setText("Searching for Arduboy" + "." * ((self.update_count % 3) + 1))
            self.info_label.setText("Make sure Arduboy is connected + turned on")
            self.status_picture.setText("⏳")
            self.status_picture.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")



class ClickableLabel(QLabel):
    """A label that implements a rudimentary "clicked" event, just like a button"""
    clicked = pyqtSignal()
    def __init__(self, text, parent = None):
        super().__init__(text, parent = parent)

    def mousePressEvent(self, event):
        self.clicked.emit()
        # Handle the mouse click event here
        # if event.button() == 1:  # Left mouse button



class NumberOnlyLineEdit(QLineEdit):
    """A line edit that only accepts numbers"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = QIntValidator() # QValidator(self)
        self.setValidator(self.validator)



class CustomGraphicsView(QGraphicsView):
    """A basic QGraphicsView that also supports basic zooming"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.zoom_factor = 1.0

    def wheelEvent(self, event):
        num_degrees = event.angleDelta().y() / 8
        num_steps = num_degrees / 15
        self.zoom_by_factor(num_steps)
        event.accept()

    def zoom_by_factor(self, factor):
        self.set_zoom(self.zoom_factor * (1.2 ** factor))
        self.setTransform(QtGui.QTransform().scale(self.zoom_factor, self.zoom_factor))
    
    def set_zoom(self, zoom):
        self.zoom_factor = zoom
        self.setTransform(QtGui.QTransform().scale(self.zoom_factor, self.zoom_factor))



class WidthHeightWidget(QWidget):
    """A set of inputs for entering width and height."""
    onchange = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()

        self.width = NumberOnlyLineEdit()
        self.width.setToolTip("Width")
        layout.addWidget(self.width)
        the_x = QLabel("X")
        layout.addWidget(the_x)
        self.height = NumberOnlyLineEdit()
        self.height.setToolTip("Height")
        layout.addWidget(self.height)

        self.set_values(0, 0)

        self.width.textChanged.connect(lambda: self.onchange.emit())
        self.height.textChanged.connect(lambda: self.onchange.emit())

        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
    
    def set_values(self, width, height):
        self.width.setText(str(width))
        self.height.setText(str(height))

    def get_values(self):
        return int(self.width.text()), int(self.height.text())



class ContrastPicker(QComboBox):
    """Basic contrast picker for arduboy screen patching"""
    def __init__(self):
        super().__init__()
        import arduboy.patch # The only place we really need this...
        self.addItem("Max Contrast", arduboy.patch.CONTRAST_HIGHEST)
        self.addItem("Normal", arduboy.patch.CONTRAST_NORMAL)
        self.addItem("Dim", arduboy.patch.CONTRAST_DIM)
        self.addItem("Dimmer", arduboy.patch.CONTRAST_DIMMER)
        self.addItem("Dimmest", arduboy.patch.CONTRAST_DIMMEST)
        self.setCurrentIndex(1)
    
    def get_contrast(self):
        return self.itemData(self.currentIndex())
    
    def get_contrast_str(self):
        return hex(self.get_contrast())



class HtmlWindow(QTextBrowser):
    """Basic html browser for in-built resources (usually help documentation)."""
    def __init__(self, title, resource):
        super().__init__()
        import utils
        with open(utils.resource_file(resource), "r") as f:
            basehtml = f.read()
            buffer = '<p style="color:rgba(0,0,0,0)"><center>---</center></p>'
            self.setHtml('<style>p, h1, h2, h3 { margin: 15px; }</style>' + buffer + basehtml + buffer)
        self.setWindowTitle(title)
        self.resize(500,500)
        self.setOpenExternalLinks(True)



class FilePicker(QWidget):
    """A basic file picker meant to emulate the html file input (with a settable field and clickable choose button, plus drag+drop)."""
    def __init__(self, file_filter = "All Files (*)", save_new_file = False, default_name_generator = None):
        super().__init__()
        self.file_filter = file_filter
        self.save_new_file = save_new_file
        self.default_name_generator = default_name_generator

        self.setAcceptDrops(True)

        layout = QHBoxLayout()

        # File picker is like a web file picker, a textbox you can mess with + a choose button.
        self.filetext = QLineEdit()
        layout.addWidget(self.filetext)

        self.filechoose = QPushButton("Save File" if save_new_file else "Open File")
        self.filechoose.clicked.connect(self.show_file_dialog)
        layout.addWidget(self.filechoose)

        layout.setStretchFactor(self.filetext, 1)
        layout.setStretchFactor(self.filechoose, 0)

        self.setLayout(layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            self.filetext.setText(url.toLocalFile())  # Display file path in QLineEdit
    
    # Retrieve the chosen file. Not an event or anything, just call this to get whatever text is
    # in the textbox, regardless of how it was entered
    def get_chosen_file(self):
        return self.filetext.text()
    
    def show_file_dialog(self):
        if self.default_name_generator:
            default_name = self.default_name_generator()
        else:
            default_name = ""
        if self.save_new_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_name, self.file_filter)
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Choose File", default_name, self.file_filter)
        self.filetext.setText(file_path)


    # Verify filepath. May throw exceptions, and may open dialogs. This should be called on a UI thread!!!
    def check_filepath(self, parent):
        if self.save_new_file:
            return self._check_save_filepath(parent)
        else:
            return self._check_open_filepath()

    # Internal check filepath, only really valid for not save_new_file
    def _check_open_filepath(self):
        filepath = self.get_chosen_file()
        if not filepath:
            raise Exception("No file chosen!")
        if not os.path.isfile(filepath):
            raise Exception("File not found!")
        return filepath

    # Internal check filepath, only really valid for save_new_file
    def _check_save_filepath(self, parent):
        filepath = self.get_chosen_file()
        if not filepath:
            raise Exception("No file chosen!")
        if os.path.isfile(filepath):
            confirmation = QMessageBox.question(
                parent, "Overwrite file",
                f"File already exists. Are you sure you want to overwrite this file: {filepath}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if confirmation == QMessageBox.StandardButton.Yes:
                os.remove(filepath)
            else:
                return None

        return filepath

