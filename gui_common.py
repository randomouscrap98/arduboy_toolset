import utils
import logging

from PyQt6 import QtGui
# from PyQt6.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QVBoxLayout, QMessageBox, QGroupBox
# from PyQt6.QtWidgets import  QCheckBox, QApplication 
from PyQt6.QtCore import Qt

SUBDUEDCOLOR = "rgba(128,128,128,0.75)"
WARNINGINPUT = "border: 1px solid rgba(255,0,0,1)"
SUCCESSCOLOR = "#30c249"
ERRORCOLOR = "#c23030"
BACKUPCOLOR = "#308dc2"

# I don't know what registering a font multiple times will do, might as well just make it a global
EMOJIFONT = None

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
