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
from PIL import Image


# TODO: 
# - Let a command flag open cratebuilder automatically.
# - DON'T set a default image, so users know to set a new image by clicking
# - Add verification steps to cart builder to ensure there is always a category at the start.
# - Add some way to move entire categories around
# - See if there always needs to be a main category (probably not)
# - Add explanation to help about why the list is shown the way it is
# - Add ability to set image
# - Add storage for all the data in SlotWidget
# - Add way to turn slotwidget into fx slot data
# - Add some way for data mods to update the numbers shown in slot meta
# - Go find out how arduboy format works (hopefully all formats are easy) and get the data from it
# - Figure out if you can get title images out of arduboy files

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
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.newcart)
        file_menu.addAction(new_action)

        open_action = QAction("Open Cart", self)
        open_action.setShortcut("Ctrl+O")
        # new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(open_action)

        open_read_action = QAction("Load From Arduboy", self)
        open_read_action.setShortcut("Ctrl+Alt+L")
        # open_cart_action.triggered.connect(self.open_opencart)
        file_menu.addAction(open_read_action)

        save_action = QAction("Save Cart", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Cart as", self)
        save_as_action.setShortcut("Ctrl+Alt+S")
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        add_action = QAction("Add Game", self)
        add_action.setShortcut("Ctrl+G")
        add_action.triggered.connect(self.add_game)
        file_menu.addAction(add_action)

        add_cat_action = QAction("Add Category", self)
        add_cat_action.setShortcut("Ctrl+T")
        add_cat_action.triggered.connect(self.add_category)
        file_menu.addAction(add_cat_action)

        del_action = QAction("Delete Selected", self)
        del_action.setShortcut(Qt.Key_Delete)
        del_action.triggered.connect(self.delete_selected)
        file_menu.addAction(del_action)

        file_menu.addSeparator()

        flash_action = QAction("Flash to Arduboy", self)
        flash_action.setShortcut("Ctrl+Alt+F")
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
        title = f"Cart Editor"
        if self.filepath:
            title = f"{title} - {self.filepath}"
        else:
            title = f"{title} - New"
        if self.modified:
            title = f"[!] {title}"
        self.setWindowTitle(title)

    # Insert a new slot widget (already setup) at the appropriate location
    def insert_slotwidget(self, widget):
        item = QListWidgetItem()
        selected_item = self.list_widget.currentItem()
        if selected_item:
            row = self.list_widget.row(selected_item)
            self.list_widget.insertItem(row + 1, item)
        else:
            self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.setCurrentItem(item)
        widget.onchange.connect(lambda: self.set_modified(True))
        self.set_modified(True)
        # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
    
    def add_category(self):
        # Need to generate default images at some point!! You have the font!
        newcat = SlotWidget(arduboy.utils.new_parsed_slot_from_category("New Category"))
        self.insert_slotwidget(newcat)

    def add_game(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER, options=options)
        if file_path:
            parsed = arduboy.arduhex.read(file_path)
            newgame = SlotWidget(arduboy.utils.new_parsed_slot_from_arduboy(parsed))
            self.insert_slotwidget(newgame)

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
            return self.save_as()
        else:
            self.do_self_save(self.filepath)
            return True

    # Save current file with a dialog, set new file as filepath, remove modification.
    def save_as(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER, options=options)
        if file_path:
            self.do_self_save(file_path)
            return True
        return False

    def newcart(self):
        if self.safely_discard_changes():
            self.list_widget.clear()
            self.set_modified(False)
            # TODO: might need some other data cleanup!!
    
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
                return self.save() # The user still did not make a decision if they didn't save
            
            # Caller needs to know if the user chose some action that allows them to continue
            return reply != QMessageBox.Cancel

        return True

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Crate Editor Help", "help_cart.html")
        self.help_window.show()
    
    def delete_selected(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

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
    

class SlotWidget(QWidget):
    onchange = pyqtSignal()
    
    # A slot must always have SOME parsed data associated with it!
    def __init__(self, parsed: arduboy.fxcart.FxParsedSlot):
        super().__init__()

        # !! BIG NOTE: widgets should NOT be able to change "modes", so we set up lots 
        # of mode-specific stuff in the constructor! IE a category cannot become a program etc

        self.parsed = parsed
        toplayout = QHBoxLayout()

        # ---------------------------
        #  Left section (image, data)
        # ---------------------------
        leftlayout = QVBoxLayout()
        leftwidget = QWidget()

        self.image = TitleImageWidget()
        if parsed.image_raw:
            self.image.set_image_bytes(parsed.image_raw)
        self.image.onimage_bytes.connect(self.set_image_bytes)
        leftlayout.addWidget(self.image)

        # Create it now, use it later
        self.meta_label = QLabel()

        if not parsed.is_category():
            datalayout = QHBoxLayout()
            datawidget = QWidget()

            self.program = gui_utils.emoji_button("💻", "Set program .hex")
            self.program.clicked.connect(self.select_program)
            datalayout.addWidget(self.program)
            self.data = gui_utils.emoji_button("🧰", "Set data .bin")
            self.data.clicked.connect(self.select_data)
            datalayout.addWidget(self.data)
            self.save = gui_utils.emoji_button("💾", "Set save .bin")
            self.save.clicked.connect(self.select_save)
            datalayout.addWidget(self.save)

            datalayout.setContentsMargins(0,0,0,0)
            datawidget.setLayout(datalayout)
            leftlayout.addWidget(datawidget)

        # This is a category then
        else:
            leftwidget.setStyleSheet("background: rgba(255,255,0,1)")
            self.meta_label.setStyleSheet("font-weight: bold; margin-bottom: 5px")

        self.meta_label.setAlignment(Qt.AlignCenter)
        gui_utils.mod_font_size(self.meta_label, 0.85)
        leftlayout.addWidget(self.meta_label)
        self.update_metalabel()

        leftlayout.setContentsMargins(0,0,0,0)
        leftwidget.setLayout(leftlayout)
        toplayout.addWidget(leftwidget)

        # And now all the editable fields!
        # ---------------------------
        #  Right section (image, data)
        # ---------------------------
        fieldlayout = QVBoxLayout()
        fieldsparent = QWidget()

        fields = []
        self.title = gui_utils.new_selflabeled_edit("Title", parsed.meta.title)
        self.title.textChanged.connect(lambda t: self.do_meta_change(t, "title"))
        fields.append(self.title)
        if not parsed.is_category():
            self.version = gui_utils.new_selflabeled_edit("Version", parsed.meta.version)
            self.version.textChanged.connect(lambda t: self.do_meta_change(t, "version"))
            fields.append(self.version)
            self.author = gui_utils.new_selflabeled_edit("Author", parsed.meta.developer)
            self.author.textChanged.connect(lambda t: self.do_meta_change(t, "developer"))
            fields.append(self.author)
        self.info = gui_utils.new_selflabeled_edit("Info", parsed.meta.info)
        self.info.textChanged.connect(lambda t: self.do_meta_change(t, "info"))
        self.info.setMaxLength(150) # Max total length of meta in header is 199, this limit is just a warning
        fields.append(self.info)
        
        if parsed.is_category():
            gui_utils.add_children_nostretch(fieldlayout, fields)
        else:
            for f in fields:
                fieldlayout.addWidget(f)

        fieldlayout.setContentsMargins(0,0,0,0)
        fieldsparent.setLayout(fieldlayout)

        toplayout.addWidget(fieldsparent)

        self.setLayout(toplayout)

    # Update the metadata label for this unit with whatever new information is stored locally
    def update_metalabel(self):
        if self.parsed.is_category():
            self.meta_label.setText("Category ↓")
        else:
            self.meta_label.setText(f"{len(self.parsed.program_raw)}  |  {len(self.parsed.data_raw)}  |  {len(self.parsed.save_raw)}")
    
    # Perform a simple meta field change. This is unfortunately DIFFERENT than the metalabel!
    def do_meta_change(self, new_text, field):
        setattr(self.parsed.meta, field, new_text) # .title = new_text
        self.onchange.emit()

    def get_slot_data(self):
        return self.parsed
    
    def select_program(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER, options=QFileDialog.Options())
        if file_path:
            # NOTE: eventually, this should set the various fields based on the parsed arduboy file!!
            parsed = arduboy.arduhex.read(file_path)
            self.parsed.data_raw = arduboy.utils.arduhex_to_bin(parsed.rawhex)
            self.update_metalabel()
            self.onchange.emit()

    def select_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", constants.BIN_FILEFILTER, options=QFileDialog.Options())
        if file_path:
            with open(file_path, "rb") as f:
                self.parsed.data_raw = f.read()
            self.update_metalabel()
            self.onchange.emit()

    def select_save(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Save File", "", constants.BIN_FILEFILTER, options=QFileDialog.Options())
        if file_path:
            with open(file_path, "rb") as f:
                self.parsed.save_raw = f.read()
            self.update_metalabel()
            self.onchange.emit()
    
    def set_image_bytes(self, image_bytes):
        self.parsed.image_raw = image_bytes
        self.onchange.emit()


class TitleImageWidget(QLabel):
    onimage_bytes = pyqtSignal(bytearray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QtGui.QCursor(Qt.PointingHandCursor))  # Set cursor to pointing hand
        self.setScaledContents(True)  # Scale the image to fit the label
        self.set_image_bytes(None)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setStyleSheet(f"background-color: {gui_utils.SUBDUEDCOLOR}")
    
    # NOTE: should be the simple 1024 bytes directly from the parsing! Anytime image bytes are needed, that's what is expected!
    def set_image_bytes(self, image_bytes):
        if image_bytes is not None:
            pil_image = arduboy.utils.bin_to_pilimage(image_bytes)
            qt_image = QtGui.QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QtGui.QImage.Format_Grayscale8)
            pixmap = QtGui.QPixmap(qt_image) 
            self.setPixmap(pixmap)
            self.setText("")
        else:
            self.setPixmap(QtGui.QPixmap())
            self.setText("Choose image")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Open a file select dialog, resize+crop the image to exactly 128x64, then set it as self and pass it along!
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Title Image File", "", constants.IMAGE_FILEFILTER, options=QFileDialog.Options())
            if file_path:
                image = Image.open(file_path)
                # Actually for now I'm just gonna stretch it, I don't care! Hahaha TODO: fix this
                image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.NEAREST)
                image = image.convert("1") # Do this after because it's probably better AFTER nearest neighbor
                # We convert to bytes to send over the wire (emit) and to set our own image. Yes, we will be converting it back in set_image_bytes
                image_bytes = arduboy.utils.pilimage_to_bin(image) 
                self.set_image_bytes(image_bytes)
                self.onimage_bytes.emit(image_bytes) #arduboy.utils.pilimage_to_bin(image))


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