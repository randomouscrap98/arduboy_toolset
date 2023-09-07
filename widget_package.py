import arduboy.arduhex
import arduboy.fxcart
import arduboy.patch

from arduboy.constants import *

# import widget_slot
import constants
import gui_utils
import utils
import debug_actions

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGroupBox, QHBoxLayout, QFileDialog
from PyQt6.QtWidgets import QLineEdit, QLabel, QScrollArea, QTableWidget, QHeaderView

class PackageEditor(QWidget):
    def __init__(self):
        super().__init__()

        editor_layout = QHBoxLayout()

        # Editor panes
        self.info_group = QGroupBox("Package Info")
        self.binary_group = QGroupBox("Package Binaries")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
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
        contributors_label = QLabel("Contributors:")
        info_layout.addWidget(contributors_label)
        info_layout.setStretchFactor(contributors_label, 0)

        self.contributors_table = QTableWidget()
        self.contributors_table.setColumnCount(3)
        self.contributors_table.setHorizontalHeaderLabels(["Name      ", "Contribution  ", "Urls (comma separated)"])
        self.contributors_table.resizeColumnsToContents()
        self.contributors_table.horizontalHeader().setStretchLastSection(True)
        info_layout.addWidget(self.contributors_table)
        info_layout.setStretchFactor(self.contributors_table, 1)
        # self.contributors_area = QScrollArea()
        # info_layout.addWidget(self.contributors_area)
        # info_layout.setStretchFactor(self.contributors_area, 1)

        editor_layout.addWidget(self.info_group)
        editor_layout.addWidget(self.binary_group)
        editor_layout.setStretchFactor(self.info_group, 1)
        editor_layout.setStretchFactor(self.binary_group, 1)

        self.setLayout(editor_layout)
    

    def fill(self, package: arduboy.arduhex.ArduboyParsed):
        self.title_edit.setText(package.title)
        self.version_edit.setText(package.version)
        self.author_edit.setText(package.author)
        self.info_edit.setText(package.description)
        self.genre_edit.setText(package.genre)
        self.url_edit.setText(package.url)
        self.sourceurl_edit.setText(package.sourceUrl)
        self.email_edit.setText(package.email)

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

        return package


class PackageWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()
        self.setLayout(full_layout)

        self.package_editor = PackageEditor()
        full_layout.addWidget(self.package_editor)
        self.prep_editor_layout()

        # Controls for saving/loading/etc packages
        package_controls = QWidget() # QGroupBox("Package Controls")
        package_controls_layout = QHBoxLayout()
        package_controls.setLayout(package_controls_layout)
        clear_package_button = QPushButton("Reset")
        clear_package_button.clicked.connect(self.do_reset_package)
        package_controls_layout.addWidget(clear_package_button)
        load_package_button = QPushButton("Load")
        load_package_button.clicked.connect(self.do_load_package)
        package_controls_layout.addWidget(load_package_button)
        save_package_button = QPushButton("Save")
        save_package_button.clicked.connect(self.do_save_package)
        package_controls_layout.addWidget(save_package_button)

        full_layout.addWidget(package_controls)
        full_layout.setStretchFactor(package_controls, 0)

    
    def prep_editor_layout(self):
        self.package_editor.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setStretchFactor(self.package_editor, 1)
    
    def reset_editor(self, arduparsed: arduboy.arduhex.ArduboyParsed = None):
        new_editor = PackageEditor()
        self.layout().replaceWidget(self.package_editor, new_editor)
        self.package_editor.setParent(None) # Removes it from the interface
        if arduparsed:
            new_editor.fill(arduparsed)
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
