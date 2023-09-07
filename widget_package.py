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

class PackageEditor(QWidget):
    def __init__(self):
        super().__init__()

        editor_layout = QHBoxLayout()

        # Editor panes
        self.info_group = QGroupBox("Package Info")
        self.binary_group = QGroupBox("Package Binaries")

        editor_layout.addWidget(self.info_group)
        editor_layout.addWidget(self.binary_group)

        self.setLayout(editor_layout)

    def fill(self, package: arduboy.arduhex.ArduboyParsed):
        pass

    def create_package(self):
        return arduboy.arduhex.empty_parsed_arduboy()


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
