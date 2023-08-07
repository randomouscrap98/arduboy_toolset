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
from PyQt5.QtWidgets import QMessageBox, QAction, QCheckBox, QListWidgetItem, QListWidget
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, Qt


# TODO: change system so you can open, new, etc. directly from inside the crate builder.
# Crate builder should be able to load flash from arduboy, edit, then reflash.
# Main window shouldn't have new crate or open crate, just "Crate Builder". Maybe
# remove file menu? Crate Builder can be in Utilities. Let a command flag open 
# cratebuilder automatically.

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

        list_widget = QListWidget(self)
        for i in range(1, 11):
            complex_widget = SlotWidget() # ComplexWidget(f"Item {i}")
            item = QListWidgetItem()
            list_widget.addItem(item)
            list_widget.setItemWidget(item, complex_widget)
            item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
            item.setSizeHint(complex_widget.sizeHint())
        # self.item = SlotWidget()

        # layout.addWidget(list_widget)
        # centralwidget.setLayout(layout)
        self.setCentralWidget(list_widget)
        self.set_modified(False)
        
    def create_menu(self):
        # Create the top menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_action = QAction("New Cart", self)
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(new_action)

        open_action = QAction("Open Cart", self)
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(open_action)

        open_read_action = QAction("Open From Arduboy", self)
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

        file_menu.addSeparator()

        flash_action = QAction("Flash to Arduboy", self)
        # open_cart_action.triggered.connect(self.open_opencart)
        file_menu.addAction(flash_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)


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

    
    def save(self):
        pass

    def save_as(self):
        pass

    def closeEvent(self, event) -> None:
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"There are unsaved changes! Do you want to save your work before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                if self.filepath:
                    self.save()
                else:
                    self.save_as()
            elif reply == QMessageBox.Cancel:
                event.ignore()  # Ignore the close event
                return

            # Clear out some junk, we have a lot of parsed resources and junk!
            if reply != QMessageBox.Cancel:
                self.modified = False

        event.accept()  # Allow the close event to proceed

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Crate Editor Help", "help_cart.html")
        self.help_window.show()

    def closeEvent(self, event) -> None:
        if hasattr(self, 'help_window'):
            self.help_window.close()


class SlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        toplayout = QHBoxLayout()

        # ---------------------------
        #  Left section (image, data)
        # ---------------------------
        leftlayout = QVBoxLayout()
        leftwidget = QWidget()

        self.image = TitleImageWidget()
        leftlayout.addWidget(self.image)

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

        self.sizes = QLabel("0  |  0  |  0")
        self.sizes.setAlignment(Qt.AlignCenter)
        gui_utils.mod_font_size(self.sizes, 0.85)
        leftlayout.addWidget(self.sizes)

        # leftlayout.setSpacing(0)
        # leftlayout.setSpacing(1)
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