import arduboy.arduhex
import arduboy.fxcart
import arduboy.patch
import arduboy.image
import arduboy.common

from arduboy.constants import *

import widget_slot
import constants
import gui_utils
import utils
import debug_actions

from typing import List
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QComboBox
from PyQt6.QtWidgets import QLineEdit, QLabel, QScrollArea, QTableWidget, QListWidget, QTableWidgetItem
from PyQt6.QtWidgets import QListWidgetItem

FIELDS_SPACING = 3


class BinaryWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(FIELDS_SPACING)

        # ------------- TOP ROW (IMAGE/BASIC DATA) -----------------
        toprow_container = QWidget()
        toprow_layout = QHBoxLayout()
        toprow_layout.setContentsMargins(0,0,0,0)
        toprow_container.setLayout(toprow_layout)

        self.image_select = widget_slot.TitleImageWidget()
        self.image_select.setToolTip("Cart image; users will see this when browsing games on their Arduboy!")
        toprow_layout.addWidget(self.image_select)
        toprow_layout.setStretchFactor(self.image_select, 0)

        basicdata_container = QWidget()
        basicdata_layout = QVBoxLayout()
        basicdata_layout.setContentsMargins(0,0,0,0)
        basicdata_container.setLayout(basicdata_layout)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Title (optional)")
        basicdata_layout.addWidget(self.title_edit)

        self.device_select = QComboBox()
        for d in arduboy.arduhex.ALLOWED_DEVICES:
            self.device_select.addItem(d)
        self.device_select.setToolTip("The device this binary is for.\n-Arduboy binaries can be used on any official Arduboy, but should not include FX data.\n-ArduboyFX and ArduboyMini are for FX-enabled titles that are compiled for those specific devices")
        basicdata_layout.addWidget(self.device_select)

        toprow_layout.addWidget(basicdata_container)
        toprow_layout.setStretchFactor(basicdata_container, 1)

        layout.addWidget(toprow_container)

        # -------------- DATA CONTROLS ----------------
        def mkdata(basetext, field, default_func, opentitle, filetypes, reader, setextra = None, lengthcalc = None):
            container = QWidget()
            container_layout = QHBoxLayout()
            container_layout.setContentsMargins(0,0,0,0)
            button = QPushButton()
            container_layout.addWidget(button)
            container_layout.setStretchFactor(button, 1)
            deletebutton = QPushButton("❌")
            container_layout.addWidget(deletebutton)
            container_layout.setStretchFactor(deletebutton, 0)
            lengthcalc = lengthcalc or (lambda: len(getattr(self, field)))
            def refresh():
                length = lengthcalc()
                button.setText(basetext + (f" - {length} bytes" if length else " - None"))
                if length == 0:
                    deletebutton.setDisabled(True)
                    deletebutton.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
                else:
                    deletebutton.setDisabled(False)
                    deletebutton.setStyleSheet(f"color: {gui_utils.ERRORCOLOR}")
            def setdata():
                file_path, _ = QFileDialog.getOpenFileName(self, opentitle, "", filetypes)
                if file_path:
                    setattr(self, field, reader(file_path))
                    if setextra:
                        setextra()
                    refresh()
            button.clicked.connect(setdata)
            gui_utils.set_emoji_font(deletebutton)
            def deletedata():
                setattr(self, field, default_func())
                refresh()
            deletebutton.clicked.connect(deletedata)
            container.setLayout(container_layout)
            layout.addWidget(container)
            deletedata() # Might as well set a bunch of stuff
            return refresh
        
        def read_text(fp):
            with open(fp, "r") as f:
                return f.read()
        def read_binary(fp):
            with open(fp, "rb") as f:
                return bytearray(f.read())
        def setdata_extra():
            unused_pages = arduboy.common.count_unused_pages(self.data_raw)
            if (unused_pages % (arduboy.fxcart.SAVE_ALIGNMENT // FX_PAGESIZE)) == 0:
                # Ask if the user wants to create a save out of this
                if gui_utils.yes_no("Split save section out",
                                    "The data provided appears to have a save section at the end. This is normal when using the development binary. Do you want to strip the save and add it properly to the slot (recommended)?", 
                                    self):
                    self.save_raw = self.data_raw[-unused_pages * FX_PAGESIZE:]
                    self.data_raw = self.data_raw[:-unused_pages * FX_PAGESIZE]
                    self.refresh_fxsavetext()
                    self.refresh_fxdatatext()
        def hexlength():
            return len(arduboy.common.hex_to_bin(self.hex_raw))

        self.refresh_hextext = mkdata(".hex program", "hex_raw", lambda: "", "Open .hex file", constants.HEX_FILEFILTER, read_text, lengthcalc=hexlength)
        self.refresh_fxdatatext = mkdata("FX data", "data_raw", lambda: bytearray(), "Open FX data file", constants.BIN_FILEFILTER, read_binary, setextra = setdata_extra)
        self.refresh_fxsavetext = mkdata("FX save", "save_raw", lambda: bytearray(), "Open FX save file", constants.BIN_FILEFILTER, read_binary)

        # -------------- FINAL COMPOSE ---------------
        self.setLayout(layout)
    

    def get_binary(self) -> arduboy.arduhex.ArduboyBinary:
        return arduboy.arduhex.ArduboyBinary(
            self.device_select.currentText(),
            self.title_edit.text(),
            self.hex_raw,
            self.data_raw,
            self.save_raw,
            arduboy.image.bin_to_pilimage(self.image_select.image_bytes) if self.image_select.image_bytes else None
        )
    
    def fill(self, binary: arduboy.arduhex.ArduboyBinary):
        self.title_edit.setText(binary.title)
        self.device_select.setCurrentText(binary.device)
        if binary.cartImage:
            self.image_select.set_image_pil(binary.cartImage)
        self.hex_raw = binary.hex_raw
        self.data_raw = binary.data_raw
        self.save_raw = binary.save_raw
        self.refresh_hextext()
        self.refresh_fxdatatext()
        self.refresh_fxsavetext()


class PackageEditor(QWidget):
    def __init__(self):
        super().__init__()

        editor_layout = QHBoxLayout()

        # Editor panes
        self.info_group = QGroupBox("Package Info")
        self.binary_group = QGroupBox("Package Binaries")

        # ------------ INFO PANE ------------------
        info_layout = QVBoxLayout()
        info_layout.setSpacing(FIELDS_SPACING)
        self.info_group.setLayout(info_layout)

        # All these junk fields are exactly the same
        def mkedit(placeholder, tooltip):
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            if tooltip:
                edit.setToolTip(tooltip)
            info_layout.addWidget(edit)
            info_layout.setStretchFactor(edit, 0)
            return edit

        # All the junk fields
        self.title_edit = mkedit("Title", "Title of your program. This is used as part of a key to uniquely identify your program, try not to change it! (Required)")
        self.version_edit = mkedit("Version", "Version of your program; you should increment it every update! (Required)")
        self.author_edit = mkedit("Author", "Singular name or entity. This is used as part of a key to uniquely identify your program, try not to change it! (Required)")
        self.info_edit = mkedit("Description", "A short description of your program")
        self.genre_edit = mkedit("Genre", "How you would categorize your program (consider the existing cart categories, such as Action/Adventure/etc)")
        self.url_edit = mkedit("URL", "A website for your program or team (not required)")
        self.sourceurl_edit = mkedit("Source URL", "The link to the source code for this program (github?)")
        self.email_edit = mkedit("Email", "A point of contact for support (not required)")
        # Some fields not included just yet

        # The contributors section
        contributors_header_container = QWidget()
        contributors_header_layout = QHBoxLayout()
        contributors_header_layout.setContentsMargins(0,0,0,0)
        contributors_header_container.setLayout(contributors_header_layout)

        contributors_label = QLabel("Contributors:")
        contributors_header_layout.addWidget(contributors_label)
        contributors_header_layout.setStretchFactor(contributors_label, 1)

        self.contributors_add = QPushButton("Add")
        self.contributors_add.setStyleSheet("font-size: 10px")
        self.contributors_add.clicked.connect(self.add_contributor)
        contributors_header_layout.addWidget(self.contributors_add)
        contributors_header_layout.setStretchFactor(self.contributors_add, 0)

        self.contributors_remove = QPushButton("Remove")
        self.contributors_remove.setStyleSheet("font-size: 10px")
        self.contributors_remove.clicked.connect(self.remove_contributor)
        contributors_header_layout.addWidget(self.contributors_remove)
        contributors_header_layout.setStretchFactor(self.contributors_remove, 0)

        info_layout.addWidget(contributors_header_container)
        info_layout.setStretchFactor(contributors_label, 0)

        self.contributors_table = QTableWidget()
        self.contributors_table.setColumnCount(3)
        self.contributors_table.setHorizontalHeaderLabels(["Name          ", "Roles            ", "Urls (comma separated)"])
        self.contributors_table.resizeColumnsToContents()
        self.contributors_table.horizontalHeader().setStretchLastSection(True)
        info_layout.addWidget(self.contributors_table)
        info_layout.setStretchFactor(self.contributors_table, 1)

        # ------------ Binary PANE ------------------
        binary_layout = QVBoxLayout()
        self.binary_group.setLayout(binary_layout)

        controls_container = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0,0,0,0)
        controls_container.setLayout(controls_layout)

        self.binary_add = QPushButton("Add")
        self.binary_add.clicked.connect(self.add_binary)
        controls_layout.addWidget(self.binary_add)
        self.binary_remove = QPushButton("Remove")
        self.binary_remove.clicked.connect(self.remove_binary)
        controls_layout.addWidget(self.binary_remove)

        binary_layout.addWidget(controls_container)
        binary_layout.setStretchFactor(self.binary_add, 0)

        self.binary_list = QListWidget()
        binary_layout.addWidget(self.binary_list)
        binary_layout.setStretchFactor(self.binary_list, 1)

        # -------------- FINAL COMPOSE ---------------
        editor_layout.addWidget(self.info_group)
        editor_layout.addWidget(self.binary_group)
        editor_layout.setStretchFactor(self.info_group, 1)
        editor_layout.setStretchFactor(self.binary_group, 1)

        self.setLayout(editor_layout)

    
    def add_contributor(self, contributor: arduboy.arduhex.ArduboyContributor = None):
        rowPosition = self.contributors_table.rowCount()
        self.contributors_table.insertRow(rowPosition)
        if contributor:
            fields = [contributor.name, ", ".join(contributor.roles), ", ".join(contributor.urls)]
        else:
            fields = ["","",""]
        for i, field in enumerate(fields):
            self.contributors_table.setItem(rowPosition , i, QTableWidgetItem(field))

    def remove_contributor(self):
        selected_items = self.contributors_table.selectedItems()
        for item in selected_items:
            self.contributors_table.removeRow(item.row())

    def add_binary(self, binary: arduboy.arduhex.ArduboyBinary = None):
        item = QListWidgetItem()
        widget = BinaryWidget()
        if binary:
            widget.fill(binary)
        # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
        item.setSizeHint(widget.sizeHint())
        # IDK what the right order for all this is...
        self.binary_list.addItem(item)
        self.binary_list.setItemWidget(item, widget)
        self.binary_list.setCurrentItem(item)
    
    def remove_binary(self):
        selected_items = self.binary_list.selectedItems()
        # selected_count = len(selected_items)
        for item in selected_items:
            row = self.binary_list.row(item)
            self.binary_list.takeItem(row)

    def fill(self, package: arduboy.arduhex.ArduboyParsed):
        self.title_edit.setText(package.title)
        self.version_edit.setText(package.version)
        self.author_edit.setText(package.author)
        self.info_edit.setText(package.description)
        self.genre_edit.setText(package.genre)
        self.url_edit.setText(package.url)
        self.sourceurl_edit.setText(package.sourceUrl)
        self.email_edit.setText(package.email)
        for c in package.contributors:
            self.add_contributor(c)
        for b in package.binaries:
            self.add_binary(b)

    def get_contributors(self) -> List[arduboy.arduhex.ArduboyContributor]:
        result = []
        for row in range(self.contributors_table.rowCount()):
            contributor = arduboy.arduhex.ArduboyContributor(self.contributors_table.item(row, 0).text())
            def columnsplit(col):
                raw = self.contributors_table.item(row, col).text()
                return [x.strip() for x in raw.split(",")] if raw else []
            contributor.roles = columnsplit(1)
            contributor.urls = columnsplit(2)
            result.append(contributor)
        return result
    
    def get_binaries(self) -> List[arduboy.arduhex.ArduboyBinary]:
        result = []
        for x in range(self.binary_list.count()):
            widget = self.binary_list.itemWidget(self.binary_list.item(x)) #.get_slot_data() for x in range(self.list_widget.count())]
            result.append(widget.get_binary())
        return result

    def create_package(self):
        package = arduboy.arduhex.empty_parsed_arduboy()
        package.title = self.title_edit.text()
        package.version = self.version_edit.text()
        package.author = self.author_edit.text()
        package.description = self.info_edit.text()
        package.genre = self.genre_edit.text()
        package.url = self.url_edit.text()
        package.sourceUrl = self.sourceurl_edit.text()
        package.email = self.email_edit.text()

        if not package.title:
            raise Exception("Title is required!")
        if not package.version:
            raise Exception("Version is required! Just put 1.0 if you're unsure!")
        if not package.author:
            raise Exception("Author is required!")

        package.contributors = self.get_contributors()
        package.binaries = self.get_binaries()

        if len(package.binaries) == 0:
            raise Exception("No binaries; there must always be at least one program!")

        for b in package.binaries:
            if b.fx_enabled() and b.device == arduboy.arduhex.DEVICE_ARDUBOY:
                raise Exception(f"Binary '{b.title}' can't be marked for device '{b.device}', it is FX enabled!")
            if not b.hex_raw or len(b.hex_raw) == 0:
                raise Exception("You MUST provide the main .hex file for every binary!")

        return package


class PackageWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()
        self.setLayout(full_layout)

        self.package_editor = None 
        self.reset_editor()
        self.prep_editor_layout()

        # Controls for saving/loading/etc packages
        package_controls = QWidget() # QGroupBox("Package Controls")
        package_controls_layout = QHBoxLayout()
        package_controls.setLayout(package_controls_layout)
        load_package_button = QPushButton("Load")
        load_package_button.clicked.connect(self.do_load_package)
        package_controls_layout.addWidget(load_package_button)
        save_package_button = QPushButton("Save")
        save_package_button.clicked.connect(self.do_save_package)
        package_controls_layout.addWidget(save_package_button)
        clear_package_button = QPushButton("Reset")
        clear_package_button.clicked.connect(self.do_reset_package)
        package_controls_layout.addWidget(clear_package_button)

        full_layout.addWidget(package_controls)
        full_layout.setStretchFactor(package_controls, 0)

    
    def prep_editor_layout(self):
        self.package_editor.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setStretchFactor(self.package_editor, 1)
    
    def reset_editor(self, arduparsed: arduboy.arduhex.ArduboyParsed = None):
        new_editor = PackageEditor()
        if self.package_editor:
            self.layout().replaceWidget(self.package_editor, new_editor)
            self.package_editor.setParent(None) # Removes it from the interface
        else:
            self.layout().addWidget(new_editor)
        if arduparsed:
            new_editor.fill(arduparsed)
        else:
            new_editor.add_binary() # Just a convenience maybe? Could be an inconvenience...
        self.package_editor = new_editor
        self.prep_editor_layout()
        
    def do_reset_package(self):
        # Must confirm
        if gui_utils.yes_no("Confirm reset package", "Are you sure you want to reset the package?", self):
            # We do something really stupid
            self.reset_editor()
            debug_actions.global_debug.add_action_str(f"Reset arduboy package editor")

    def do_load_package(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER)
        if file_path:
            parsed = arduboy.arduhex.read_any(file_path)
            self.reset_editor(parsed)
            debug_actions.global_debug.add_action_str(f"Loaded arduboy package into editor: {file_path}")
    
    def do_save_package(self):
        package = self.package_editor.create_package()
        filepath, _ = QFileDialog.getSaveFileName(self, "Save slot as .arduboy", utils.get_arduhex_backup_filename(package), constants.ARDUBOY_FILEFILTER)
        if filepath:
            # The slot is special and can have additional fields. Might as well get them now
            arduboy.arduhex.write_arduboy(package, filepath)
            debug_actions.global_debug.add_action_str(f"Wrote arduboy file for: {package.title} to {filepath}")
