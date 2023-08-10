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
import slugify
import debug_actions

from arduboy.constants import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog
from PyQt5.QtWidgets import QMessageBox, QAction, QListWidgetItem, QListWidget, QFileDialog, QAbstractItemView, QLineEdit
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread
from PIL import Image


# TODO: 
# - Add some way to move entire categories around
# - Test that new game (though they said you can't flash it to fx?)

class CartWindow(QMainWindow):
    _add_slot_signal = pyqtSignal(arduboy.fxcart.FxParsedSlot, bool)

    def __init__(self):
        super().__init__()

        self.filepath = None
        self.search_text = None
        self.resize(800, 600)
        self._add_slot_signal.connect(self.add_slot)

        self.create_menu()

        centralwidget = QWidget()
        layout = QVBoxLayout()

        self.list_widget = QListWidget(self)
        self.setAcceptDrops(True)

        self.list_widget.setUniformItemSizes(True) # Makes categories ugly but... scrolling nicer
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        layout.addWidget(self.list_widget)

        footerwidget = self.create_footer()
        layout.addWidget(footerwidget)

        centralwidget.setLayout(layout)
        self.setCentralWidget(centralwidget) # self.list_widget)
        self.set_modified(False)

        debug_actions.global_debug.add_item.connect(lambda item: self.action_label.setText(item.action))
        debug_actions.global_debug.add_action_str("Opened cart editor")
        
    def create_menu(self):
        # Create the top menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_action = QAction("New Cart", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.action_newcart)
        file_menu.addAction(new_action)

        open_action = QAction("Open Cart", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.action_opencart)
        file_menu.addAction(open_action)

        save_action = QAction("Save Cart", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.action_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Cart as", self)
        save_as_action.setShortcut("Ctrl+Alt+S")
        save_as_action.triggered.connect(self.action_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        open_read_action = QAction("Load From Arduboy", self)
        open_read_action.setShortcut("Ctrl+Alt+L")
        open_read_action.triggered.connect(self.action_openflash)
        file_menu.addAction(open_read_action)

        flash_action = QAction("Flash to Arduboy", self)
        flash_action.setShortcut("Ctrl+Alt+W")
        flash_action.triggered.connect(self.action_flash)
        file_menu.addAction(flash_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # -------------------------------
        cart_menu = menu_bar.addMenu("Cart")

        add_action = QAction("Add Game", self)
        add_action.setShortcut("Ctrl+G")
        add_action.triggered.connect(self.action_add_game)
        cart_menu.addAction(add_action)

        add_cat_action = QAction("Add Category", self)
        add_cat_action.setShortcut("Ctrl+T")
        add_cat_action.triggered.connect(self.action_add_category)
        cart_menu.addAction(add_cat_action)

        del_action = QAction("Delete Selected", self)
        del_action.setShortcut(Qt.Key_Delete)
        del_action.triggered.connect(self.action_delete_selected)
        cart_menu.addAction(del_action)

        find_action = QAction("Search cart", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.action_find)
        cart_menu.addAction(find_action)

        findagain_action = QAction("Repeat last search", self)
        findagain_action.setShortcut("Ctrl+Shift+F")
        findagain_action.triggered.connect(lambda: self.action_find(True))
        cart_menu.addAction(findagain_action)

        # -------------------------------
        debug_menu = menu_bar.addMenu("Debug")

        csing_action = QAction("Compile selected item", self)
        csing_action.triggered.connect(self.action_compilesingle)
        debug_menu.addAction(csing_action)

        # -------------------------------
        # Create an action for opening the help window
        open_help_action = QAction("Help", self)
        open_help_action.triggered.connect(self.open_help_window)
        menu_bar.addAction(open_help_action)

    def create_footer(self):
        footerwidget = QWidget()
        footerlayout = QHBoxLayout()

        self.action_label = QLabel("Action...")
        self.action_label.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
        footerlayout.addWidget(self.action_label)
        spacer = QWidget()
        footerlayout.addWidget(spacer)
        footerlayout.setStretchFactor(spacer, 1)
        self.counts_label = QLabel("Counts label...")
        footerlayout.addWidget(self.counts_label)
        footerlayout.setStretchFactor(self.counts_label, 0)
        footerlayout.setContentsMargins(1,1,1,1)

        footerwidget.setLayout(footerlayout)

        return footerwidget
    

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            try:
                # Why doesn't this set off the normal exception handling?
                self.action_add_game(url.toLocalFile())
            except Exception as ex:
                QMessageBox.critical(None, "Can't open file", f"Couldn't open arduboy/hex file: {ex}", QMessageBox.Ok)
    

    def set_modified(self, modded = True):
        self.modified = modded
        slots = self.get_slots()
        categories = sum(1 for item in slots if item.is_category())
        games = len(slots) - categories
        self.counts_label.setText(f"Categories: {categories} | Games: {games}")
        self.update_title()
    
    def update_title(self):
        title = f"Cart Editor v{constants.VERSION}"
        if self.filepath:
            title = f"{title} - {self.filepath}"
        else:
            title = f"{title} - New"
        if self.modified:
            title = f"[!] {title}"
        self.setWindowTitle(title)

    def setup_slotwidget_item(self, widget):
        item = QListWidgetItem()
        # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
        item.setSizeHint(widget.sizeHint())
        widget.onchange.connect(lambda: self.set_modified(True))
        return item

    # Insert a new slot widget (already setup) at the appropriate location
    def insert_slotwidget(self, widget):
        item = self.setup_slotwidget_item(widget)
        selected_item = self.list_widget.currentItem()
        if selected_item:
            row = self.list_widget.row(selected_item)
            self.list_widget.insertItem(row + 1, item)
        else:
            self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self.list_widget.setCurrentItem(item)
        self.set_modified(True)
    
    # Scan through all the list widget items and get the current parsed slot data from each of them. Right now this is
    # fast, but we can't always rely on that! Maybe...
    def get_slots(self):
        return [self.list_widget.itemWidget(self.list_widget.item(x)).get_slot_data() for x in range(self.list_widget.count())]
    
    # Return the currently selected slot, or none if... none
    def get_selected_slot(self) -> arduboy.fxcart.FxParsedSlot:
        selected_item = self.list_widget.currentItem()
        if selected_item:
            return self.list_widget.itemWidget(selected_item).get_slot_data()
        else:
            return None

    # UNFORTUNATELY, any dialog box handles its own exceptions (it's hard not to), so you must check the return
    # type from here. Ew, TODO: fix this!
    def get_current_as_raw(self):
        slots = self.get_slots()
        fxbin = bytearray()
        def do_work(repprog, repstatus):
            nonlocal slots, fxbin
            fxbin = arduboy.fxcart.compile(slots, repprog)
        dialog = gui_utils.do_progress_work(do_work, "Compiling FX", simple = True)
        if dialog.error_state:
            return None
        else:
            return fxbin
    
    # All saves are basically the same at the end of the day, this is what they do. This removes
    # modification state and sets current document to whatever you give
    def do_self_save(self, filepath):
        rawdata = self.get_current_as_raw()
        if not rawdata:
            return
        with open(filepath, "wb") as f:
            f.write(rawdata)
        self.filepath = filepath
        self.set_modified(False)
        debug_actions.global_debug.add_action_str(f"Saved cart to file {filepath}")

    def clear(self):
        self.list_widget.clear()
        self.set_modified(False)
        # TODO: might need some other data cleanup!!
    
    def add_slot(self, slot, clear = False):
        if clear:
            self.clear()
        widget = SlotWidget(slot)
        item = self.setup_slotwidget_item(widget)
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget) 

    # Load the given binary data into the window, clearing out whatever was there before
    def loadcart(self, bindata, filepath = None):
        parsed = None
        # IDK how long it takes to parse, just throw up a loading window just in case anyway
        def do_work(repprog, repstatus):
            nonlocal parsed # widgits # parsed
            parsed = arduboy.fxcart.parse(bindata, repprog)
            repstatus("Rendering items")
            count = 0
            rest = 1
            for slot in parsed:
                self._add_slot_signal.emit(slot, count == 0)
                count += 1
                repprog(count, len(parsed))
                # This is a hack. The UI does not update unless this is here. An exponentially decreasing thread sleep
                if count == rest:
                    time.sleep(0.01)
                    rest = rest << 1
        self.list_widget.blockSignals(True)
        try:
            dialog = gui_utils.do_progress_work(do_work, "Parsing binary", simple = True)
            if not dialog.error_state:
                if filepath:
                    self.filepath = filepath
                self.set_modified(False)
        finally:
            self.list_widget.blockSignals(False)
    
    # -----------------------------------
    #    ACTIONS FROM MENU / SHORTCUTS
    # -----------------------------------
    
    def action_newcart(self):
        if self.safely_discard_changes():
            self.clear()
            debug_actions.global_debug.add_action_str("Created new cart")

    def action_opencart(self):
        if self.safely_discard_changes():
            filepath, _ = QFileDialog.getOpenFileName(self, "Open Flashcart File", "", constants.BIN_FILEFILTER, options=QFileDialog.Options())
            if filepath:
                bindata = arduboy.fxcart.read(filepath)
                self.loadcart(bindata, filepath)
                debug_actions.global_debug.add_action_str(f"Loaded cart from {filepath}")
    
    def action_openflash(self):
        if self.safely_discard_changes():
            # Try to connect to arduboy
            bindata = bytearray()
            def do_work(device, repprog, repstatus):
                nonlocal bindata
                repstatus("Reading FX flash...")
                s_port = device.connect_serial()
                bindata = arduboy.serial.backup_fx(s_port, repprog)
                repstatus("Trimming FX file...")
                bindata = arduboy.fxcart.trim(bindata)
            dialog = gui_utils.do_progress_work(do_work, "Load FX Flash")
            if not dialog.error_state:
                self.filepath = None # There is no file anymore
                self.loadcart(bindata)
                debug_actions.global_debug.add_action_str(f"Loaded cart from Arduboy")
    
    def action_flash(self):
        # Might as well ask... it's kind of a big deal to flash
        reply = QMessageBox.question(self, "Flash FX Cart",
            f"Are you sure you want to flash this cart to the Arduboy?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return 
        # Must compile data first
        bindata = self.get_current_as_raw()
        if not bindata:
            return
        def do_work(device, repprog, repstatus):
            nonlocal bindata
            s_port = device.connect_serial()
            repstatus("Flashing FX Cart...")
            arduboy.serial.flash_fx(bindata, 0, s_port, verify=True, report_progress=repprog)
        dialog = gui_utils.do_progress_work(do_work, "Flash FX Cart")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Flashed cart to Arduboy")
        else:
            debug_actions.global_debug.add_action_str(f"Failed flashing cart to Arduboy")

    # Save current file without dialog if possible. If no previous file, have to open a new one
    def action_save(self):
        if not self.filepath:
            return self.action_save_as()
        else:
            self.do_self_save(self.filepath)
            return True

    # Save current file with a dialog, set new file as filepath, remove modification.
    def action_save_as(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER, options=options)
        if filepath:
            self.do_self_save(filepath)
            return True
        return False

    def action_add_category(self):
        # Need to generate default images at some point!! You have the font!
        newcat = SlotWidget(arduboy.utils.new_parsed_slot_from_category("New Category"))
        self.insert_slotwidget(newcat)
        debug_actions.global_debug.add_action_str(f"Added new category to cart")

    def action_add_game(self, file_path = None):
        if not file_path:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER, options=options)
        if file_path:
            parsed = arduboy.arduhex.read(file_path)
            newgame = SlotWidget(arduboy.utils.new_parsed_slot_from_arduboy(parsed))
            self.insert_slotwidget(newgame)
            debug_actions.global_debug.add_action_str(f"Added game to cart: {parsed.title}")
    
    def action_delete_selected(self):
        selected_items = self.list_widget.selectedItems()
        selected_count = len(selected_items)
        for item in selected_items:
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
        self.set_modified(True)
        debug_actions.global_debug.add_action_str(f"Removed {selected_count} slots from cart")
    
    def action_find(self, use_last = False):
        if not use_last:
            search_text, ok = QInputDialog.getText(self, 'Find in cart', 'Search text:')
            if not (search_text and ok):
                return
            self.search_text = search_text
        if not self.search_text:
            return
        line_edits = self.findChildren(QLineEdit)
        le_index = 0
        for le in line_edits:
            if le.hasFocus():
                break
            le_index += 1
        # This "splits the deck" at the index of the currently focused textbox, meaning the search will start
        # from AFTER that text. It lets you do ctrl-F multiple times
        reordered_edits = line_edits[le_index + 1:] + line_edits[:le_index + 1]
        for line_edit in reordered_edits:
            if self.search_text.lower() in line_edit.text().lower():
                line_edit.setFocus()
                parent_item = self.get_slot_parent(line_edit)
                if parent_item:
                    item = self.list_widget.itemAt(parent_item.pos())
                    self.list_widget.scrollToItem(item)
                break
    
    def action_compilesingle(self):
        # Need to get selected. If none, just... exit?
        cslot = self.get_selected_slot()
        if cslot:
            defile = slugify.slugify(cslot.meta.title if cslot.meta.title else "") + f"_{utils.get_filesafe_datetime()}.bin"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save single compiled slot", defile, constants.BIN_FILEFILTER, options=QFileDialog.Options())
            if filepath:
                bindata = arduboy.fxcart.compile_single(cslot)
                with open(filepath, "wb") as f:
                    f.write(bindata)
                debug_actions.global_debug.add_action_str(f"Compiled single cart: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    
    def get_slot_parent(self, widget):
        while widget:
            if isinstance(widget, SlotWidget):
                return widget
            widget = widget.parent()

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Cart Editor Help", "help_cart.html")
        self.help_window.show()
    
    
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
            elif reply == QMessageBox.Discard:
                debug_actions.global_debug.add_action_str(f"Discarded current cart")
            
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
        # toplayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

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
            debug_actions.global_debug.add_action_str(f"Edited program for: {self.parsed.meta.title}")

    def select_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", constants.BIN_FILEFILTER, options=QFileDialog.Options())
        if file_path:
            with open(file_path, "rb") as f:
                self.parsed.data_raw = f.read()
            self.update_metalabel()
            self.onchange.emit()
            debug_actions.global_debug.add_action_str(f"Edited FX data for: {self.parsed.meta.title}")

    def select_save(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Save File", "", constants.BIN_FILEFILTER, options=QFileDialog.Options())
        if file_path:
            with open(file_path, "rb") as f:
                self.parsed.save_raw = f.read()
            self.update_metalabel()
            self.onchange.emit()
            debug_actions.global_debug.add_action_str(f"Edited FX save for: {self.parsed.meta.title}")
    
    def set_image_bytes(self, image_bytes):
        self.parsed.image_raw = image_bytes
        self.onchange.emit()
        debug_actions.global_debug.add_action_str(f"Edited tile image for: {self.parsed.meta.title}")

# Perform image conversion in a worker, since it actually does take a non-trivial amount of 
# time. This speeds up the apparent rendering of the list
class ImageConvertWorker(QThread):
    image_done = pyqtSignal(bytearray)
    on_error = pyqtSignal(Exception)
    def __init__(self, image):
        super().__init__()
        self.image = image
    def run(self):
        try:
            self.image_done.emit(arduboy.utils.bin_to_pilimage(self.image, raw=True))
        except Exception as ex:
            self.on_error.emit(ex)

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
            self.worker = ImageConvertWorker(image_bytes)
            self.worker.image_done.connect(self._finish_image)
            self.worker.on_error.connect(lambda ex: gui_utils.show_exception(ex))
            self.worker.start()
        else:
            self.setPixmap(QtGui.QPixmap())
            self.setText("Choose image")
    
    def _finish_image(self, b):
        qt_image = QtGui.QImage(b, SCREEN_WIDTH, SCREEN_HEIGHT, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap(qt_image) 
        self.setPixmap(pixmap)
        self.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Open a file select dialog, resize+crop the image to exactly 128x64, then set it as self and pass it along!
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Title Image File", "", constants.IMAGE_FILEFILTER, options=QFileDialog.Options())
            if file_path:
                image = arduboy.arduhex.pilimage_convert(Image.open(file_path))
                # We convert to bytes to send over the wire (emit) and to set our own image. Yes, we will be converting it back in set_image_bytes
                image_bytes = arduboy.utils.pilimage_to_bin(image) 
                self.set_image_bytes(image_bytes)
                self.onimage_bytes.emit(image_bytes) #arduboy.utils.pilimage_to_bin(image))


# --------------------------------------
#    TEMPORARY SETUP FOR DEBUGGING
# --------------------------------------
def test():
    try:
        fxbin = arduboy.fxcart.read("flashcart-image.bin")
        parsed = arduboy.fxcart.parse(fxbin)
        compiled = arduboy.fxcart.compile(parsed)
    except Exception as ex:
        logging.exception(ex) 


if __name__ == "__main__":

    # Set the custom exception hook. Do this ASAP!!
    sys.excepthook = gui_utils.exception_hook

    # Some initial setup
    try:
        # This apparently only matters for windows and for GUI apps
        from ctypes import windll  # Only exists on Windows.
        myappid = 'Haloopdy.ArduboyToolset'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    logging.basicConfig(filename=os.path.join(constants.SCRIPTDIR, "arduboy_toolset_gui_log.txt"), level=logging.DEBUG, 
                        format="%(asctime)s - %(levelname)s - %(message)s")

    # test()
    app = QApplication(sys.argv) # Frustrating... you HAVE to run this first before you do ANY QT stuff!
    app.setWindowIcon(QtGui.QIcon(utils.resource_file("icon.ico")))

    gui_utils.try_create_emoji_font()

    window = CartWindow()
    window.show()
    sys.exit(app.exec_())