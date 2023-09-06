import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.shortcuts
import arduboy.image

from arduboy.constants import *
from arduboy.common import *

import widget_progress
import constants
import utils
import gui_utils
import debug_actions

from widget_slot import *

import logging
import os
import sys
import time

from typing import List
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog, QComboBox
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem, QListWidget, QFileDialog, QAbstractItemView, QLineEdit
from PyQt6 import QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, Qt

# TODO: 
# - Add some singular self-updating window that displays a realtime view of the debug log? Who owns it, how many can be open, etc

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
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        layout.addWidget(self.list_widget)

        footerwidget = self.create_footer()
        layout.addWidget(footerwidget)

        centralwidget.setLayout(layout)
        # centralwidget.setObjectName("wtfplease")
        centralwidget.setStyleSheet("QListWidget { border: 1px solid " + gui_utils.SUBDUEDCOLOR + " }")
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

        export_slots_action = QAction("Export slots to .arduboy", self)
        # export_slots_action.setShortcut()
        export_slots_action.triggered.connect(self.action_exportslots)
        file_menu.addAction(export_slots_action)

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
        edit_menu = menu_bar.addMenu("Edit")

        add_action = QAction("Add Game", self)
        add_action.setShortcut("Ctrl+G")
        add_action.triggered.connect(self.action_add_game)
        edit_menu.addAction(add_action)

        add_cat_action = QAction("Add Category", self)
        add_cat_action.setShortcut("Ctrl+T")
        add_cat_action.triggered.connect(self.action_add_category)
        edit_menu.addAction(add_cat_action)

        del_action = QAction("Delete Selected", self)
        del_action.setShortcut("Ctrl+Delete")
        del_action.triggered.connect(self.action_delete_selected)
        edit_menu.addAction(del_action)

        edit_menu.addSeparator()

        up_slot_action = QAction("Shift Slot Up", self)
        up_slot_action.setShortcut(QtGui.QKeySequence(Qt.KeyboardModifier.ControlModifier| Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Up))
        up_slot_action.triggered.connect(self.action_slot_up)
        edit_menu.addAction(up_slot_action)

        down_slot_action = QAction("Shift Slot Down", self)
        down_slot_action.setShortcut(QtGui.QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Down))
        down_slot_action.triggered.connect(self.action_slot_down)
        edit_menu.addAction(down_slot_action)

        up_cat_action = QAction("Shift Category Up", self)
        up_cat_action.setShortcut("Ctrl+Shift+U")
        up_cat_action.triggered.connect(self.action_category_up)
        edit_menu.addAction(up_cat_action)

        down_cat_action = QAction("Shift Category Down", self)
        down_cat_action.setShortcut("Ctrl+Shift+D")
        down_cat_action.triggered.connect(self.action_category_down)
        edit_menu.addAction(down_cat_action)

        del_cat_action = QAction("Delete Entire Category", self)
        del_cat_action.setShortcut("Ctrl+Shift+Delete")
        del_cat_action.triggered.connect(self.action_category_delete)
        edit_menu.addAction(del_cat_action)

        edit_menu.addSeparator()

        addsave_action = QAction("Add 4K to save for Slot", self)
        addsave_action.triggered.connect(self.action_addsave)
        edit_menu.addAction(addsave_action)

        clearfxsave_action = QAction("Clear FX save for Slot", self)
        clearfxsave_action.triggered.connect(self.action_clearfxsave)
        edit_menu.addAction(clearfxsave_action)

        clearfxdata_action = QAction("Clear FX data for Slot", self)
        clearfxdata_action.triggered.connect(self.action_clearfxdata)
        edit_menu.addAction(clearfxdata_action)


        # -------------------------------
        navigate_menu = menu_bar.addMenu("Navigate")

        mup_cat_action = QAction("Jump to Previous Category", self)
        mup_cat_action.setShortcut("Ctrl+U")
        mup_cat_action.triggered.connect(self.action_category_jumpup)
        navigate_menu.addAction(mup_cat_action)

        mdown_cat_action = QAction("Jump to Next Category", self)
        mdown_cat_action.setShortcut("Ctrl+D")
        mdown_cat_action.triggered.connect(self.action_category_jumpdown)
        navigate_menu.addAction(mdown_cat_action)

        navigate_menu.addSeparator()

        find_action = QAction("Search cart", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.action_find)
        navigate_menu.addAction(find_action)

        findagain_action = QAction("Repeat last search", self)
        findagain_action.setShortcut("Ctrl+Shift+F")
        findagain_action.triggered.connect(lambda: self.action_find(True))
        navigate_menu.addAction(findagain_action)

        # -------------------------------
        debug_menu = menu_bar.addMenu("Debug")

        csing_action = QAction("Compile selected Slot", self)
        csing_action.triggered.connect(self.action_compilesingle)
        debug_menu.addAction(csing_action)

        ardsingle_action = QAction("Generate .arduboy from Slot", self)
        ardsingle_action.triggered.connect(self.action_writesinglearduboy)
        debug_menu.addAction(ardsingle_action)

        unparse_action = QAction("Generate .hex from Slot bin", self)
        unparse_action.triggered.connect(self.action_unparsebin)
        debug_menu.addAction(unparse_action)


        gimg_action = QAction("Generate image for Slot", self)
        gimg_action.triggered.connect(self.action_imagesingle)
        debug_menu.addAction(gimg_action)

        # -------------------------------
        # Create an action for opening the help window
        help_menu = menu_bar.addMenu("About")

        open_about_action = QAction("About", self)
        open_about_action.triggered.connect(self.open_about_window)
        help_menu.addAction(open_about_action)
        
        open_help_action = QAction("Help", self)
        open_help_action.setShortcut(QtGui.QKeySequence(Qt.Key.Key_F1))
        open_help_action.triggered.connect(self.open_help_window)
        help_menu.addAction(open_help_action)

    def create_footer(self):
        footerwidget = QWidget()
        footerlayout = QHBoxLayout()

        self.action_label = QLabel("Action...")
        self.action_label.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
        footerlayout.addWidget(self.action_label)
        spacer = QWidget()
        footerlayout.addWidget(spacer)
        footerlayout.setStretchFactor(spacer, 1)

        self.device_select = QComboBox()
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYFX)
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.device_select.setStyleSheet("font-weight: bold")
        self.device_select.setToolTip("The device which will use this flashcart.\nAn incorrect setting will make FX-enabled titles malfunction")
        footerlayout.addWidget(self.device_select)
        footerlayout.setStretchFactor(self.device_select, 0)

        self.counts_label = QLabel("Counts label...")
        footerlayout.addWidget(self.counts_label)
        footerlayout.setStretchFactor(self.counts_label, 0)
        footerlayout.setContentsMargins(1,1,1,1)

        footerwidget.setLayout(footerlayout)

        return footerwidget
    
    # -------------------
    #       EVENTS 
    # -------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                try:
                    # Why doesn't this set off the normal exception handling?
                    self.action_add_game(url.toLocalFile())
                except Exception as ex:
                    QMessageBox.critical(None, "Can't open file", f"Couldn't open arduboy/hex file: {ex}", QMessageBox.StandardButton.Ok)

    def closeEvent(self, event) -> None:
        if self.safely_discard_changes():
            # Clear out some junk, we have a lot of parsed resources and junk!
            self.modified = False
            if hasattr(self, 'help_window'):
                self.help_window.close()
            if hasattr(self, 'about_window'):
                self.about_window.close()
            event.accept()
        else:
            # User did not choose an action, do not exit.
            event.ignore()
    
    # ---------------------
    #    GENERAL METHODS
    # ---------------------

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
    def get_slots(self) -> List[arduboy.fxcart.FxParsedSlot]:
        return [ x for x,_ in self.get_slots_widgets() ]
        # return [self.list_widget.itemWidget(self.list_widget.item(x)).get_slot_data() for x in range(self.list_widget.count())]

    # Get all the slots along with their widget.
    def get_slots_widgets(self):
        result = []
        for x in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(x)) #.get_slot_data() for x in range(self.list_widget.count())]
            result.append((widget.get_slot_data(), widget))
        return result
        # return [self.list_widget.itemWidget(self.list_widget.item(x)).get_slot_data() for x in range(self.list_widget.count())]
    
    # Return the currently selected slot, or none if... none
    def get_selected_slot(self) -> arduboy.fxcart.FxParsedSlot:
        slot, _ = self.get_selected_slot_widget()
        return slot

    # Return a combination of currently selected slot and the widget.
    def get_selected_slot_widget(self) -> arduboy.fxcart.FxParsedSlot:
        selected_item = self.list_widget.currentItem()
        if selected_item:
            item = self.list_widget.itemWidget(selected_item)
            return item.get_slot_data(), item
        else:
            return None, None

    def get_slot_parent(self, widget):
        while widget:
            if isinstance(widget, SlotWidget):
                return widget
            widget = widget.parent()

    # UNFORTUNATELY, any dialog box handles its own exceptions (it's hard not to), so you must check the return
    # type from here. Ew, TODO: fix this!
    def get_current_as_raw(self):
        slots = self.get_slots_widgets()
        fxbin = bytearray()
        def do_work(repprog, repstatus):
            nonlocal slots, fxbin
            repstatus("Generating missing images")
            for slot,widget in slots:
                if not slot.has_image():
                    pilimage = utils.make_titlescreen_from_slot(slot)
                    slot.image_raw = arduboy.image.pilimage_to_bin(pilimage)
                    widget.image._finish_image(pilimage.convert("L").tobytes()) # Very hacky backdoor stuff! TODO: make this nicer!
            repstatus("Compiling FX cart")
            fxbin = arduboy.fxcart.compile([x for x,_ in slots], repprog)
        dialog = widget_progress.do_progress_work(do_work, "Compiling FX", simple = True)
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

    # Returns whether the user went through with an action. If false, you should not 
    # continue your discard!
    def safely_discard_changes(self):
        if self.modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"There are unsaved changes! Do you want to save your work?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                return self.save() # The user still did not make a decision if they didn't save
            elif reply == QMessageBox.StandardButton.Discard:
                debug_actions.global_debug.add_action_str(f"Discarded current cart")
            
            # Caller needs to know if the user chose some action that allows them to continue
            return reply != QMessageBox.StandardButton.Cancel

        return True

    def clear(self):
        self.list_widget.clear()
        self.set_modified(False)
        # TODO: might need some other data cleanup!!
    
    def add_slot(self, slot, clear = False, index = None):
        if clear:
            self.clear()
        widget = SlotWidget(slot)
        item = self.setup_slotwidget_item(widget)
        if index is not None:
            self.list_widget.insertItem(index, item)
        else:
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
            dialog = widget_progress.do_progress_work(do_work, "Parsing binary", simple = True)
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
            filepath, _ = QFileDialog.getOpenFileName(self, "Open Flashcart File", "", constants.BIN_FILEFILTER)
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
            dialog = widget_progress.do_progress_work(do_work, "Load FX Flash")
            if not dialog.error_state:
                self.filepath = None # There is no file anymore
                self.loadcart(bindata)
                debug_actions.global_debug.add_action_str(f"Loaded cart from Arduboy")
    
    def action_flash(self):
        # Might as well ask... it's kind of a big deal to flash
        reply = QMessageBox.question(self, "Flash FX Cart",
            f"Are you sure you want to flash this cart to the Arduboy?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
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
        dialog = widget_progress.do_progress_work(do_work, "Flash FX Cart")
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
        filepath, _ = QFileDialog.getSaveFileName(self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER)
        if filepath:
            self.do_self_save(filepath)
            return True
        return False

    def action_exportslots(self):
        slots = self.get_slots()
        if not len(slots):
            raise Exception("No slots to export!")
        filepath = QFileDialog.getExistingDirectory(self, "Export folder") # (self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER)
        if filepath:
            def do_work(repprog, repstatus):
                utils.export_slots_as_arduboy(slots, filepath, repprog)
            dialog = widget_progress.do_progress_work(do_work, "Export slots as .arduboy", simple = True)
            debug_actions.global_debug.add_action_str(f"Exported slots as .arduboy")


    def action_add_category(self):
        # Need to generate default images at some point!! You have the font!
        newcat = SlotWidget(arduboy.shortcuts.slot_from_category("New Category"))
        self.insert_slotwidget(newcat)
        debug_actions.global_debug.add_action_str(f"Added new category to cart")

    def action_add_game(self, file_path = None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER)
        if file_path:
            parsed = arduboy.arduhex.read(file_path)
            # TODO: FIGURE OUT BINARY
            newgame = SlotWidget(arduboy.shortcuts.slot_from_arduboy(parsed))
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
            filepath, _ = QFileDialog.getSaveFileName(self, "Save single compiled slot", utils.get_meta_backup_filename(cslot.meta, "bin"), constants.BIN_FILEFILTER)
            if filepath:
                # Have to fix up the data first; this is normally called by the full compiler but since we're not doing that...
                slots = self.get_slots()
                arduboy.fxcart.fix_parsed_slots(slots)
                bindata = arduboy.fxcart.compile_single(cslot)
                with open(filepath, "wb") as f:
                    f.write(bindata)
                debug_actions.global_debug.add_action_str(f"Compiled single cart: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    def action_imagesingle(self):
        # Need to get selected. If none, just... exit?
        cslot = self.get_selected_slot()
        if cslot:
            filepath, _ = QFileDialog.getSaveFileName(self, "Save single compiled slot", utils.get_meta_backup_filename(cslot.meta, "png"), constants.IMAGE_FILEFILTER)
            if filepath:
                img = utils.make_titlescreen_from_slot(cslot)
                img.save(filepath)
                debug_actions.global_debug.add_action_str(f"Generated single debug image for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")
    
    def action_unparsebin(self):
        cslot = self.get_selected_slot()
        if cslot:
            filepath, _ = QFileDialog.getSaveFileName(self, "Save slot as hex", utils.get_meta_backup_filename(cslot.meta, "hex"), constants.HEX_FILEFILTER)
            if filepath:
                hexstring = arduboy.arduhex.unparse(cslot.program_raw)
                with open(filepath, "w") as f:
                    f.write(hexstring)
                debug_actions.global_debug.add_action_str(f"Saved slot as hex for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    def action_writesinglearduboy(self):
        cslot,_ = self.get_selected_slot_widget()
        if cslot:
            if cslot.is_category():
                raise Exception("Can't write arduboy files for categories!")
            filepath, _ = QFileDialog.getSaveFileName(self, "Save slot as .arduboy", utils.get_meta_backup_filename(cslot.meta, "arduboy"), constants.ARDUBOY_FILEFILTER)
            if filepath:
                # Need to convert slot back to arduboy parsed and then write
                ardparsed = arduboy.shortcuts.arduboy_from_slot(cslot)
                arduboy.arduhex.write(ardparsed, filepath)
            debug_actions.global_debug.add_action_str(f"Wrote arduboy file for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    
    def action_addsave(self):
        cslot,widget = self.get_selected_slot_widget()
        if cslot:
            if cslot.is_category():
                raise Exception("Can't add saves to categories!")
            cslot.save_raw += bytearray([0xFF] * arduboy.fxcart.SAVE_ALIGNMENT)
            widget.update_metalabel()
            self.set_modified(True)
            debug_actions.global_debug.add_action_str(f"Added more save for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    def action_clearfxdata(self):
        cslot,widget = self.get_selected_slot_widget()
        if cslot:
            if cslot.is_category():
                raise Exception("Can't clear FX data from categories!")
            cslot.data_raw = bytearray()
            widget.update_metalabel()
            self.set_modified(True)
            debug_actions.global_debug.add_action_str(f"Removed FX data for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")

    def action_clearfxsave(self):
        cslot,widget = self.get_selected_slot_widget()
        if cslot:
            if cslot.is_category():
                raise Exception("Can't clear FX save from categories!")
            cslot.save_raw = bytearray()
            widget.update_metalabel()
            self.set_modified(True)
            debug_actions.global_debug.add_action_str(f"Removed FX save for: {cslot.meta.title}")
        else:
            raise Exception("No selected slot!")
    
    def action_slot_up(self):
        self.move_current_slot(-1)

    def action_slot_down(self):
        self.move_current_slot(1)

    def move_current_slot(self, direction = 0):
        selected_item = self.list_widget.currentItem()
        selected_index = self.list_widget.row(selected_item)
        next_index = selected_index + direction
        if next_index < 0 or next_index > self.list_widget.count() - 1:
            return
        slot = self.list_widget.itemWidget(selected_item).get_slot_data()
        self.list_widget.takeItem(selected_index)
        self.add_slot(slot, index = next_index)
        self.list_widget.setCurrentItem(self.list_widget.item(next_index))
        self.set_modified(True)
        debug_actions.global_debug.add_action_str(f"Moved slot by {direction}: {slot.meta.title}")

    def action_category_up(self):
        self.shift_category(act = "up")

    def action_category_down(self):
        self.shift_category(act = "down")

    def action_category_delete(self):
        self.shift_category(act = "delete")
    
    def action_category_jumpup(self):
        cat_index, _ = self.find_surrounding_categories()
        if cat_index is not None and cat_index >= 0:
            self.list_widget.setCurrentItem(self.list_widget.item(cat_index))

    def action_category_jumpdown(self):
        _ , cat_index = self.find_surrounding_categories()
        if cat_index is not None:
            if cat_index < self.list_widget.count():
                self.list_widget.setCurrentItem(self.list_widget.item(cat_index))
    
    def _iscat(self, i): # This is a big calculation, might as well make a little function to ease it up
        return self.list_widget.itemWidget(self.list_widget.item(i)).get_slot_data().is_category()

    # Get the current category and the next category.
    def find_surrounding_categories(self, skip_if_current = True):
        # This is slow! Try to get something better eventually!
        # First step: find the various indexes
        if not self.list_widget.count():
            return  None, None # Literally can't do anything! And it's probably unsafe!
        selected_item = self.list_widget.currentItem()
        selected_index = self.list_widget.row(selected_item)
        cat_index = selected_index - (1 if skip_if_current else 0)
        end_index = selected_index + 1 # Always 1 past the end, just like in python ranges
        while cat_index > 0 and not self._iscat(cat_index):
            cat_index -= 1
        while end_index < self.list_widget.count() and not self._iscat(end_index):
            end_index += 1
        # logging.info(f"Cat index: {cat_index}, end index: {end_index}")
        return cat_index, end_index

    def shift_category(self, act = "delete"):
        cat_index, end_index = self.find_surrounding_categories(skip_if_current=False)
        # Now, see if there's anything to do. If we move up while at the top, or down at the bottom, we are finished already
        if cat_index is None or end_index is None or (cat_index <= 0 and act == "up") or (end_index >= self.list_widget.count() and act == "down"):
            return
        # Now remove all the items in the range
        count = end_index - cat_index
        whole_category = []
        for _ in range(0,count):
            whole_category.append(self.list_widget.itemWidget(self.list_widget.item(cat_index)).get_slot_data()) # (item, widget))
            self.list_widget.takeItem(cat_index)
        if act == "delete": # Nothing else to do, we already removed it
            self.set_modified(True)
            debug_actions.global_debug.add_action_str(f"Deleted category {whole_category[0].meta.title}")
            return 
        # Now, we can calculate where to insert it based on our direction.    
        if act == "up":
            target_index = cat_index - 1
            while target_index > 0 and not self._iscat(target_index):
                target_index -= 1
        elif act == "down":
            target_index = cat_index + 1
            while target_index < self.list_widget.count() and not self._iscat(target_index):
                target_index += 1
        # Now we just insert all the items at the target index, but in REVERSE order so we can keep inserting at the same index
        for slot in reversed(whole_category):
            self.add_slot(slot, index = target_index)
        self.list_widget.setCurrentItem(self.list_widget.item(target_index))
        self.set_modified(True)
        debug_actions.global_debug.add_action_str(f"Moved category {act}: {whole_category[0].meta.title}")

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Cart Editor Help", "help_cart.html")
        self.help_window.show()

    def open_about_window(self):
        self.about_window = gui_utils.HtmlWindow("About Arduboy Toolset", "about.html")
        self.about_window.show()
    

# --------------------------------------
#    TEMPORARY SETUP FOR DEBUGGING
# --------------------------------------
def test():
    try:
        fxbin = arduboy.fxcart.read("flashcart-image_good.bin")
        parsed = arduboy.fxcart.parse(fxbin)
        compiled = arduboy.fxcart.compile(parsed)
    except Exception as ex:
        logging.exception(ex) 


if __name__ == "__main__":
    app = gui_utils.basic_gui_setup()
    window = CartWindow()
    window.show()
    sys.exit(app.exec())
    