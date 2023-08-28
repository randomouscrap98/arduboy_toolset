import arduboy.device

import utils
import logging
import os
import traceback
import sys

from PyQt6 import QtGui
from PyQt6.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QFileDialog, QLabel, QTextBrowser, QDialog, QVBoxLayout, QProgressBar, QMessageBox, QGroupBox
from PyQt6.QtWidgets import  QCheckBox, QApplication, QComboBox, QGraphicsView
from PyQt6.QtGui import QIntValidator, QPainter

# I don't know what registering a font multiple times will do, might as well just make it a global
EMOJIFONT = None

SUBDUEDCOLOR = "rgba(128,128,128,0.75)"
WARNINGINPUT = "border: 1px solid rgba(255,0,0,1)"
SUCCESSCOLOR = "#30c249"
ERRORCOLOR = "#c23030"
BACKUPCOLOR = "#308dc2"

SHOWTRACE = True

def exception_hook(exctype, value, exctrace):
    show_exception(value)

def show_exception(exception, parent = None):
    global SHOWTRACE
    error_message = f"An unhandled exception occurred:\n{exception}"
    if SHOWTRACE:
        error_message += f"\n\nTraceback:" + "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    else:
        error_message += "\n\nSee log for details"
    QMessageBox.critical(parent, "Unhandled Exception", error_message, QMessageBox.StandardButton.Ok)
    logging.exception(exception)


def setup_font(name):
    font_id = QtGui.QFontDatabase.addApplicationFont(utils.resource_file(name))
    if font_id != -1:
        loaded_font_families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        if loaded_font_families:
            return loaded_font_families[0]
        else:
            raise Exception(f"Failed to find font after adding to database: {name}")
    else:
        raise Exception(f"Failed adding font to database: {name}")

def try_create_emoji_font():
    # Register the emoji font
    global EMOJIFONT
    try:
        EMOJIFONT = setup_font("NotoEmoji-Medium.ttf")
    except Exception as ex:
        logging.error(f"Could not load emoji font, falling back to system default! Error: {ex}")

def set_emoji_font(widget, size = None):
    global EMOJIFONT
    font = widget.font()
    if size is None:
        size = font.pointSize()
    if EMOJIFONT:
        widget.setFont(QtGui.QFont(EMOJIFONT, size))
    else:
        font.setPointSize(size)
        widget.setFont(font) 

def set_font_size(widget, size):
    font = widget.font()  # Get the current font of the label
    font.setPointSize(int(size))
    widget.setFont(font) 

def mod_font_size(widget, mod_size):
    font = widget.font()
    newsize = int(font.pointSize() * mod_size)
    font.setPointSize(newsize)
    widget.setFont(font) 
    return newsize

def make_button_bigger(button):
    newsize = mod_font_size(button, 1.25) # This is part of having a file action: the button is bigger
    padding = newsize * 0.75
    button.setStyleSheet(f"padding: {padding}px {padding * 3}px")


def make_file_action(title: str, picker, button, symbol = None, symbol_color = None):
    group = QGroupBox(title)
    group_layout = QVBoxLayout()
    file_action_parent,_ = make_file_group_generic(picker, button, symbol, symbol_color)
    group_layout.addWidget(file_action_parent)
    group.setLayout(group_layout)
    group.setStyleSheet("QCheckBox { margin-left: 8px; margin-bottom: 5px; }")
    return (group, group_layout)

def make_file_group_generic(picker, endcap, symbol = None, symbol_color = None):
    file_action_parent = QWidget()
    innerlayout = QHBoxLayout()
    if symbol:
        symbolwidg = QLabel(symbol)
        set_emoji_font(symbolwidg)
        mod_font_size(symbolwidg, 2)
        if symbol_color:
            symbolwidg.setStyleSheet(f"QLabel {{ color: {symbol_color} }} QLabel:disabled {{ color: {SUBDUEDCOLOR} }}")
        innerlayout.addWidget(symbolwidg)
        innerlayout.setStretchFactor(symbolwidg, 0)
    if isinstance(endcap, QPushButton):
        make_button_bigger(endcap)
    if picker is None:
        picker = QWidget()
    innerlayout.addWidget(picker)
    innerlayout.addWidget(endcap)
    innerlayout.setStretchFactor(picker, 1)
    innerlayout.setStretchFactor(endcap, 0)
    innerlayout.setContentsMargins(0,0,0,0)
    file_action_parent.setLayout(innerlayout)
    return file_action_parent, symbolwidg

def make_toggleable_element(text: str, element: QWidget, toggled = False, nostretch = False):
    toggle_parent = QWidget()
    toggle_layout = QHBoxLayout()
    checker = QCheckBox(text)
    check_event = lambda: element.setEnabled(checker.isChecked())
    checker.stateChanged.connect(check_event)
    checker.setChecked(toggled)
    check_event()
    if nostretch:
        add_children_nostretch(toggle_layout, [checker, element])
    else:
        toggle_layout.addWidget(checker)
        toggle_layout.addWidget(element)
    toggle_layout.setContentsMargins(0,0,0,0)
    toggle_parent.setLayout(toggle_layout)
    return toggle_parent, checker

def add_children_nostretch(layout, children, spacer = None):
    for c in children:
        layout.addWidget(c)
        layout.setStretchFactor(c, 0)
    if not spacer:
        spacer = QWidget()
    layout.addWidget(spacer)
    layout.setStretchFactor(spacer, 1)

def new_selflabeled_edit(text, contents = None):
    if contents:
        field = QLineEdit(contents)
    else:
        field = QLineEdit()
    field.setPlaceholderText(text)
    field.setToolTip(text)
    return field

def emoji_button(text, tooltip):
    button = QPushButton(text)
    button.setToolTip(tooltip)
    button.setFixedSize(30,30)
    set_emoji_font(button)
    return button

class FilePicker(QWidget):
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


class ContrastPicker(QComboBox):
    def __init__(self):
        super().__init__()
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
    def __init__(self, title, resource):
        super().__init__()
        with open(utils.resource_file(resource), "r") as f:
            basehtml = f.read()
            buffer = '<p style="color:rgba(0,0,0,0)"><center>---</center></p>'
            self.setHtml('<style>p, h1, h2, h3 { margin: 15px; }</style>' + buffer + basehtml + buffer)
        self.setWindowTitle(title)
        self.resize(500,500)
        self.setOpenExternalLinks(True)


# Most gui "apps" all have the same setup
def basic_gui_setup():
    utils.set_basic_logging()

    app = QApplication(sys.argv) # Frustrating... you HAVE to run this first before you do ANY QT stuff!
    sys.excepthook = exception_hook
    utils.set_app_id()
    app.setWindowIcon(QtGui.QIcon(utils.resource_file("icon.ico")))

    try_create_emoji_font()

    return app

def yes_no(title, question, parent):
    return QMessageBox.question(parent, title, question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    ) == QMessageBox.StandardButton.Yes

def screen_patch(flash_data: bytearray, ssd1309_cb : QCheckBox = None, contrast_cb : QCheckBox = None, contrast_picker : ContrastPicker = None):
    ssd1309_checked = ssd1309_cb is not None and ssd1309_cb.isChecked()
    contrast_checked = contrast_cb is not None and contrast_picker is not None and contrast_cb.isChecked()
    if ssd1309_checked or contrast_checked:
        patch_message = []
        if ssd1309_checked: patch_message.append("SSD1309")
        if contrast_checked: patch_message.append(f"CONTRAST:{contrast_picker.get_contrast_str()}")
        patch_message = "[" + ",".join(patch_message) + "]"
        contrast_value = contrast_picker.get_contrast() if contrast_checked else None
        if arduboy.patch.patch_all_screen(flash_data, ssd1309=ssd1309_checked, contrast=contrast_value):
            logging.info(f"Patched upload for {patch_message}")
        else:
            logging.warning(f"Flagged for {patch_message} patching but no LCD boot program found! Not patched!")


class NumberOnlyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = QIntValidator() # QValidator(self)
        # self.validator.setRegExp(r'^[0-9]*$')  # Regular expression to match only digits
        self.setValidator(self.validator)


class CustomGraphicsView(QGraphicsView):
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