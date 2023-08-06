from PyQt5 import QtGui
from PyQt5.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QFileDialog, QLabel, QTextBrowser
import utils
import logging

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
    newsize = mod_font_size(button, 1.5) # This is part of having a file action: the button is bigger
    padding = newsize * 0.75
    button.setStyleSheet(f"padding: {padding}px {padding * 2}px")

def add_file_action(picker, button, container, symbol = None, symbol_color = None):
    innerlayout = QHBoxLayout()
    if symbol:
        symbol = QLabel(symbol)
        set_emoji_font(symbol)
        mod_font_size(symbol, 2)
        if symbol_color:
            symbol.setStyleSheet(f"color: {symbol_color}")
        innerlayout.addWidget(symbol)
        innerlayout.setStretchFactor(symbol, 0)
    make_button_bigger(button)
    if picker is None:
        picker = QWidget()
    innerlayout.addWidget(picker)
    innerlayout.addWidget(button)
    innerlayout.setStretchFactor(picker, 1)
    innerlayout.setStretchFactor(button, 0)
    container.setLayout(innerlayout)

def add_children_nostretch(layout, children):
    for c in children:
        layout.addWidget(c)
        layout.setStretchFactor(c, 0)
    spacer = QWidget()
    layout.addWidget(spacer)
    layout.setStretchFactor(spacer, 1)

class FilePicker(QWidget):
    def __init__(self, file_filter = "All Files (*)", save_new_file = False, default_name_generator = None):
        super().__init__()
        self.file_filter = file_filter
        self.save_new_file = save_new_file
        self.default_name_generator = default_name_generator

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
    
    # Retrieve the chosen file. Not an event or anything, just call this to get whatever text is
    # in the textbox, regardless of how it was entered
    def get_chosen_file(self):
        return self.filetext.text()
    
    def show_file_dialog(self):
        options = QFileDialog.Options()
        if self.default_name_generator:
            default_name = self.default_name_generator()
        else:
            default_name = ""
        if self.save_new_file:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", default_name, self.file_filter, options=options)
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Choose File", default_name, self.file_filter, options=options)
        self.filetext.setText(file_path)


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
        # self.setStyleSheet("padding: 10px")

# class BigButton(QWidget):
#     def __init__(self, text, left_symbol = None, right_symbol = None, size_mod = 1.5, symbol_color = None):
#         super().__init__()
#         layout = QHBoxLayout()
# 
#         if left_symbol:
#             BigButton.create_symbol(left_symbol, layout, symbol_color, size_mod * 1.5)
# 
#         self.button = QPushButton(text)
#         mod_font_size(self.button, size_mod)
#         self.button.setStyleSheet("padding: 10px") # A constant? IDK about that...
#         layout.addWidget(self.button)
#         # layout.setStretchFactor(self.button, 1)
# 
#         if right_symbol:
#             BigButton.create_symbol(right_symbol, layout, symbol_color, size_mod * 1.5)
# 
#         self.setLayout(layout)
#     
#     def create_symbol(text, layout, color = None, size_mod = 1):
#         symbol = QLabel(text)
#         set_emoji_font(symbol)
#         mod_font_size(symbol, size_mod)
#         if color:
#             symbol.setStyleSheet(f"color: {color}")
#         layout.addWidget(symbol)
#         # layout.setStretchFactor(symbol, 0)
#         return symbol
# 