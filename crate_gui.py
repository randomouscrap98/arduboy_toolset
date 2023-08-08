import logging
import os
import sys
import time
import constants
import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.utils
import utils
import gui_utils

from arduboy.constants import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QGroupBox
from PyQt5.QtWidgets import QMessageBox, QAction, QCheckBox, QListWidgetItem, QListWidget, QFileDialog, QAbstractItemView
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, Qt


# TODO: Let a command flag open cratebuilder automatically.

class CrateWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.filepath = None
        self.resize(800, 600)

        self.create_menu()

        # # If this is something we're supposed to load, gotta go load the data! We should NOT reuse
        # # the progress widget, since it's made for something very different!
        # if not newcart:
        #     def do_work(repprog, repstatus):
        #         for i in range(10):
        #             time.sleep(0.2)
        #             repprog(i, 10)
        #     dialog = gui_utils.ProgressWindow(f"Parsing {os.path.basename(self.filepath)}", simple = True)
        #     worker_thread = gui_utils.ProgressWorkerThread(do_work, simple = True)
        #     worker_thread.connect(dialog)
        #     worker_thread.start()
        #     dialog.exec_()
        #     if dialog.error_state:
        #         self.deleteLater()
        
        # centralwidget = QWidget()
        # layout = QVBoxLayout()

        self.list_widget = QListWidget(self)
        for i in range(1, 11):
            complex_widget = SlotWidget() # ComplexWidget(f"Item {i}")
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, complex_widget)
            # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
            item.setSizeHint(complex_widget.sizeHint())
        
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.item = SlotWidget()

        # layout.addWidget(list_widget)
        # centralwidget.setLayout(layout)
        self.setCentralWidget(self.list_widget)
        self.set_modified(False)
        
    def create_menu(self):
        # Create the top menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_action = QAction("New Cart", self)
        new_action.triggered.connect(self.newcart)
        file_menu.addAction(new_action)

        open_action = QAction("Open Cart", self)
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(open_action)

        open_read_action = QAction("Load From Arduboy", self)
        # open_cart_action.triggered.connect(self.open_opencart)
        file_menu.addAction(open_read_action)

        save_action = QAction("Save Cart", self)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Cart as", self)
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        add_action = QAction("Add Game", self)
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(add_action)

        add_cat_action = QAction("Add Category", self)
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(add_cat_action)

        file_menu.addSeparator()

        flash_action = QAction("Flash to Arduboy", self)
        # open_cart_action.triggered.connect(self.open_opencart)
        file_menu.addAction(flash_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # -------------------------------
        # Create an action for opening the help window
        open_help_action = QAction("Help", self)
        open_help_action.triggered.connect(self.open_help_window)
        menu_bar.addAction(open_help_action)

    
    def set_modified(self, modded = True):
        self.modified = modded
        self.update_title()
    
    def update_title(self):
        title = f"Cart Editor" #  - {self.filepath}"
        if self.filepath:
            title = f"{title} - {self.filepath}"
            if self.modified:
                title = f"[!] {title}"
        else:
            title = f"{title} - New"
        self.setWindowTitle(title)

    # TODO: gather the dang data into the ready binary!
    def get_current_as_raw(self):
        return bytearray()
    
    # All saves are basically the same at the end of the day, this is what they do. This removes
    # modification state and sets current document to whatever you give
    def do_self_save(self, filepath):
        rawdata = self.get_current_as_raw()
        with open(filepath, "wb") as f:
            f.write(rawdata)
        self.filepath = filepath
        self.set_modified(False)

    # Save current file without dialog if possible. If no previous file, have to open a new one
    def save(self):
        if not self.filepath:
            self.save_as()
        else:
            self.do_self_save(self.filepath)

    # Save current file with a dialog, set new file as filepath, remove modification.
    def save_as(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER, options=options)
        if file_path:
            self.do_self_save(file_path)

    def newcart(self):
        self.safely_discard_changes()
        # TODO: clear the list and whatever!
    
    # Returns whether the user went through with an action. If false, you should not 
    # continue your discard!
    def safely_discard_changes(self):
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"There are unsaved changes! Do you want to save your work?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save()
            
            # Caller needs to know if the user chose some action that allows them to continue
            return reply != QMessageBox.Cancel

        return True


    def closeEvent(self, event) -> None:
        if self.safely_discard_changes():
            # Clear out some junk, we have a lot of parsed resources and junk!
            self.modified = False
            if hasattr(self, 'help_window'):
                self.help_window.close()
            event.accept()
        else:
            # User did not choose an action, do not exit.
            event.ignore()

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Crate Editor Help", "help_cart.html")
        self.help_window.show()


class SlotWidget(QWidget):
    def __init__(self, parsed: arduboy.fxcart.FxParsedSlot):
        super().__init__()

        toplayout = QHBoxLayout()

        # ---------------------------
        #  Left section (image, data)
        # ---------------------------
        leftlayout = QVBoxLayout()
        leftwidget = QWidget()

        self.image = TitleImageWidget()
        leftlayout.addWidget(self.image)

        if parsed.program_hex:
            datalayout = QHBoxLayout()
            datawidget = QWidget()

            self.program = gui_utils.emoji_button("💻", "Set program .hex")
            datalayout.addWidget(self.program)
            self.data = gui_utils.emoji_button("🧰", "Set data .bin")
            datalayout.addWidget(self.data)
            self.save = gui_utils.emoji_button("💾", "Set save .bin")
            datalayout.addWidget(self.save)

            datalayout.setContentsMargins(0,0,0,0)
            datawidget.setLayout(datalayout)
            leftlayout.addWidget(datawidget)

            self.meta_label = QLabel("0  |  0  |  0")

        # This is a category then
        else:
            self.meta_label = QLabel("Category")

        self.meta_label.setAlignment(Qt.AlignCenter)
        gui_utils.mod_font_size(self.meta_label, 0.85)
        leftlayout.addWidget(self.meta_label)

        leftlayout.setContentsMargins(0,0,0,0)
        leftwidget.setLayout(leftlayout)
        toplayout.addWidget(leftwidget)

        # And now all the editable fields!
        # ---------------------------
        #  Right section (image, data)
        # ---------------------------
        fieldlayout = QVBoxLayout()
        fieldsparent = QWidget()

        self.title = gui_utils.new_selflabeled_edit("Title")
        fieldlayout.addWidget(self.title)
        self.version = gui_utils.new_selflabeled_edit("Version")
        fieldlayout.addWidget(self.version)
        self.author = gui_utils.new_selflabeled_edit("Author")
        fieldlayout.addWidget(self.author)
        self.info = gui_utils.new_selflabeled_edit("Info")
        fieldlayout.addWidget(self.info)

        fieldlayout.setContentsMargins(0,0,0,0)
        # fieldlayout.setSpacing(0)
        fieldsparent.setLayout(fieldlayout)

        toplayout.addWidget(fieldsparent)
        # toplayout.setSpacing(0)

        self.setLayout(toplayout)
        # self.setStyleSheet("margin: 0; padding: 0")


class TitleImageWidget(QLabel):
    onclick = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QtGui.QCursor(Qt.PointingHandCursor))  # Set cursor to pointing hand
        self.setScaledContents(True)  # Scale the image to fit the label
        self.set_image(None)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setStyleSheet("background-color: #777")
    
    def set_image(self, pil_image):
        if pil_image is not None:
            qt_image = QtGui.QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QtGui.QImage.Format_Grayscale8)
            pixmap = QtGui.QPixmap(qt_image) 
            self.setPixmap(pixmap)
            self.setText("")
        else:
            self.setPixmap(QtGui.QPixmap())
            self.setText("Choose image")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.onclick.emit()


if __name__ == "__main__":

    # Set the custom exception hook. Do this ASAP!!
    import main_gui
    sys.excepthook = main_gui.exception_hook

    # Some initial setup
    try:
        # This apparently only matters for windows and for GUI apps
        from ctypes import windll  # Only exists on Windows.
        myappid = 'Haloopdy.ArduboyToolset' # 'mycompany.myproduct.subproduct.version'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    logging.basicConfig(filename=os.path.join(constants.SCRIPTDIR, "arduboy_toolset_gui_log.txt"), level=logging.DEBUG, 
                        format="%(asctime)s - %(levelname)s - %(message)s")

    app = QApplication(sys.argv) # Frustrating... you HAVE to run this first before you do ANY QT stuff!
    app.setWindowIcon(QtGui.QIcon(utils.resource_file("icon.ico")))

    gui_utils.try_create_emoji_font()

    window = CrateWindow() # os.path.join(constants.SCRIPTDIR, "newcart.bin"), newcart=True)
    window.show()
    sys.exit(app.exec_())