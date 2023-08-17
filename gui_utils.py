import arduboy.device

import utils
import logging
import os
import traceback
import sys

from PyQt6 import QtGui
from PyQt6.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QFileDialog, QLabel, QTextBrowser, QDialog, QVBoxLayout, QProgressBar, QMessageBox, QGroupBox
from PyQt6.QtWidgets import  QCheckBox, QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# I don't know what registering a font multiple times will do, might as well just make it a global
EMOJIFONT = None

SUBDUEDCOLOR = "rgba(128,128,128,0.75)"
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

def make_toggleable_element(text, element: QWidget, toggled = False):
    toggle_parent = QWidget()
    toggle_layout = QHBoxLayout()
    checker = QCheckBox(text)
    check_event = lambda: element.setEnabled(checker.isChecked())
    checker.stateChanged.connect(check_event)
    checker.setChecked(toggled)
    check_event()
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


class ProgressWindow(QDialog):
    def __init__(self, title, device = None, simple = False):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.error_state = False
        self.simple = simple

        if simple:
            self.resize(300, 100)
        else:
            self.resize(400, 200)

            self.status_label = QLabel("Waiting...")
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mod_font_size(self.status_label, 2)
            layout.addWidget(self.status_label)

            self.device_label = QLabel(device if device else "~")
            self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.device_label.setStyleSheet(f"color: {SUBDUEDCOLOR}")
            layout.addWidget(self.device_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        if not simple:
            self.ok_button = QPushButton("OK")
            self.ok_button.clicked.connect(self.accept)  # Connect to the accept() method
            self.ok_button.hide()  # Hide the OK button initially
            layout.addWidget(self.ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
    
    def set_device(self, device):
        if self.simple:
            logging.warning("Tried to set device when progress is set to simple! Ignoring!")
        else:
            self.device_label.setText(device)

    def set_status(self, status):
        if self.simple:
            self.setWindowTitle(status)
        else:
            self.status_label.setText(status)

    def set_complete(self):
        if self.simple:
            self.accept()
        else:
            result = "Failed" if self.error_state else "Complete"
            self.status_label.setText(f"{self.windowTitle()}: {result}!")
            self.progress_bar.setValue(0 if self.error_state else 100)
            self.ok_button.show()
    
    def report_progress(self, current, max):
        self.progress_bar.setValue(int(current / max * 100))
    
    def report_error(self, ex: Exception):
        self.error_state = True
        QMessageBox.critical(self, f"Error during '{self.windowTitle()}'", str(ex), QMessageBox.StandardButton.Ok)
        logging.exception(ex)
        self.accept()


class ProgressWorkerThread(QThread):
    update_progress = pyqtSignal(int, int)
    update_status = pyqtSignal(str)
    update_device = pyqtSignal(str)
    report_error = pyqtSignal(Exception)

    def __init__(self, work, simple = False):
        super().__init__()
        self.work = work
        self.simple = simple

    def run(self):
        try:
            if self.simple:
                # Yes, when simple, the work actually doesn't take the extra data. Be careful! This is dumb design!
                self.work(lambda cur, tot: self.update_progress.emit(cur, tot), lambda stat: self.update_status.emit(stat))
            else:
                self.update_status.emit("Waiting for bootloader...")
                device = arduboy.device.find_single()
                self.update_device.emit(device.display_name())
                self.work(device, lambda cur, tot: self.update_progress.emit(cur, tot), lambda stat: self.update_status.emit(stat))
        except Exception as ex:
            self.report_error.emit(ex)
    
    # Connect this worker thread to the given progress window by connecting up all the little signals
    def connect(self, pwindow):
        self.update_progress.connect(pwindow.report_progress)
        self.update_status.connect(pwindow.set_status)
        self.update_device.connect(pwindow.set_device)
        self.report_error.connect(pwindow.report_error)
        self.finished.connect(pwindow.set_complete)


# Perform the given work, which can report both progress and status updates through two lambdas,
# within a dialog made for reporting progress. The dialog cannot be exited, since I think exiting
# in the middle of flashing tasks is like... really bad?
def do_progress_work(work, title, simple = False):
    dialog = ProgressWindow(title, simple = simple)
    worker_thread = ProgressWorkerThread(work, simple = simple)
    worker_thread.connect(dialog)
    worker_thread.start()
    dialog.exec()
    return dialog


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