from PyQt5 import QtGui
from PyQt5.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QFileDialog, QLabel, QTextBrowser, QDialog, QVBoxLayout, QProgressBar, QMessageBox, QGroupBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import utils
import logging
import arduboy.device
import os

# I don't know what registering a font multiple times will do, might as well just make it a global
EMOJIFONT = None

SUBDUEDCOLOR = "rgba(128,128,128,0.75)"
SUCCESSCOLOR = "#30c249"
ERRORCOLOR = "#c23030"
BACKUPCOLOR = "#308dc2"


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


def make_file_action(title: str, picker, button, symbol = None, symbol_color = None):
    group = QGroupBox(title)
    file_action_parent = QWidget()
    # file_action_parent.setStyleSheet("padding: 0; margin: 0")
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
    file_action_parent.setLayout(innerlayout)
    group_layout = QVBoxLayout()
    group_layout.addWidget(file_action_parent)
    group.setLayout(group_layout)
    group.setStyleSheet("QCheckBox { margin-left: 20px; margin-bottom: 5px }")
    return (group, group_layout)

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

        self.setAcceptDrops(True)

        layout = QHBoxLayout()

        # File picker is like a web file picker, a textbox you can mess with + a choose button.
        self.filetext = QLineEdit()
        # self.filetext.setDragEnabled(True)  # Enable drag-and-drop
        # self.filetext.setAcceptDrops(True)  # Enable drop event
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
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if confirmation == QMessageBox.Yes:
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
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint & ~Qt.WindowMaximizeButtonHint)
        self.error_state = False
        self.simple = simple

        if simple:
            self.resize(300, 100)
        else:
            self.resize(400, 200)

            self.status_label = QLabel("Waiting...")
            self.status_label.setAlignment(Qt.AlignCenter)
            mod_font_size(self.status_label, 2)
            layout.addWidget(self.status_label)

            self.device_label = QLabel(device if device else "~")
            self.device_label.setAlignment(Qt.AlignCenter)
            self.device_label.setStyleSheet(f"color: {SUBDUEDCOLOR}")
            layout.addWidget(self.device_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        if not simple:
            self.ok_button = QPushButton("OK")
            self.ok_button.clicked.connect(self.accept)  # Connect to the accept() method
            self.ok_button.hide()  # Hide the OK button initially
            layout.addWidget(self.ok_button, alignment=Qt.AlignCenter)

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
        QMessageBox.critical(self, f"Error during '{self.windowTitle()}'", str(ex), QMessageBox.Ok)
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
def do_progress_work(work, title):
    dialog = ProgressWindow(title)
    worker_thread = ProgressWorkerThread(work)
    worker_thread.connect(dialog)
    worker_thread.start()
    dialog.exec_()
