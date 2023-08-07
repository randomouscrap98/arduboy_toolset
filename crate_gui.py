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


class CrateWindow(QWidget):
    def __init__(self, filepath, newcart = False):
        super().__init__()

        self.filepath = filepath
        self.resize(800, 600)
        self.set_modified(False)

        # If this is something we're supposed to load, gotta go load the data! We should NOT reuse
        # the progress widget, since it's made for something very different!
        if not newcart:
            def do_work(repprog, repstatus):
                for i in range(10):
                    time.sleep(0.2)
                    repprog(i, 10)
            dialog = gui_utils.ProgressWindow(f"Parsing {os.path.basename(self.filepath)}", simple = True)
            worker_thread = gui_utils.ProgressWorkerThread(do_work, simple = True)
            worker_thread.connect(dialog)
            worker_thread.start()
            dialog.exec_()
            if dialog.error_state:
                self.deleteLater()
        

        layout = QVBoxLayout()
        list_widget = QListWidget(self)
        for i in range(1, 11):
            complex_widget = SlotWidget() # ComplexWidget(f"Item {i}")
            item = QListWidgetItem()
            list_widget.addItem(item)
            list_widget.setItemWidget(item, complex_widget)
            item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
            item.setSizeHint(complex_widget.sizeHint())
        # self.item = SlotWidget()

        layout.addWidget(list_widget)
        self.setLayout(layout)
        
    
    def set_modified(self, modded = True):
        self.modified = modded
        title = f"Cart Editor - {self.filepath}"
        if modded:
            title = f"[!] {title}"
        self.setWindowTitle(title)
    
    def save(self):
        pass

    def closeEvent(self, event) -> None:
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"There are unsaved changes to {self.filepath}. Do you want to save your work before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save()
            elif reply == QMessageBox.Cancel:
                event.ignore()  # Ignore the close event
                return

            # Clear out some junk, we have a lot of parsed resources and junk!
            if reply != QMessageBox.Cancel:
                self.modified = False

        event.accept()  # Allow the close event to proceed


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

        datawidget.setLayout(datalayout)
        leftlayout.addWidget(datawidget)

        # leftlayout.setSpacing(0)
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

    window = CrateWindow(os.path.join(constants.SCRIPTDIR, "newcart.bin"), newcart=True)
    window.show()
    sys.exit(app.exec_())