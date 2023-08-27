import arduboy.arduhex
import arduboy.fxcart
import arduboy.patch

from arduboy.constants import *

import widget_slot
import constants
import gui_utils
import utils
import debug_actions

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGroupBox, QHBoxLayout, QFileDialog

class PackageWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()

        # Main group containing all the packaging UI
        self.package_group = QGroupBox("Package .arduboy")
        self.package_layout = QVBoxLayout()

        # Reuse slot widget to make arduboy package
        self.package_slot = self.make_slot_widget()
        self.package_layout.addWidget(self.package_slot)

        # Controls for saving/loading/etc packages
        package_controls = QWidget()
        package_controls_layout = QHBoxLayout()
        clear_package_button = QPushButton("Reset")
        clear_package_button.clicked.connect(self.do_reset_package)
        package_controls_layout.addWidget(clear_package_button)
        load_package_button = QPushButton("Load")
        load_package_button.clicked.connect(self.do_load_package)
        package_controls_layout.addWidget(load_package_button)
        save_package_button = QPushButton("Save")
        save_package_button.clicked.connect(self.do_save_package)
        package_controls_layout.addWidget(save_package_button)
        package_controls.setLayout(package_controls_layout)
        self.package_layout.addWidget(package_controls)

        # Finish up the main group
        self.package_group.setLayout(self.package_layout)

        # Finish up whole widget
        gui_utils.add_children_nostretch(full_layout, [ self.package_group ])

        self.setLayout(full_layout)
    
    def make_slot_widget(self, arduparsed: arduboy.arduhex.ArduboyParsed = None):
        if not arduparsed:
            arduparsed = arduboy.shortcuts.empty_parsed_arduboy()
        result = widget_slot.SlotWidget(arduparsed=arduparsed)
        result.layout.setContentsMargins(5,5,5,5)
        return result

    def replace_slot(self, new_widget):
        self.package_layout.replaceWidget(self.package_slot, new_widget)
        self.package_slot.setParent(None) # Clean it up
        self.package_slot = new_widget

    def do_reset_package(self):
        # Must confirm
        if gui_utils.yes_no("Confirm reset package", "Are you sure you want to reset the package?", self):
            # We do something really stupid
            self.replace_slot(self.make_slot_widget())
            debug_actions.global_debug.add_action_str(f"Reset arduboy package editor")

    def do_load_package(self):
        # Must confirm
        # if gui_utils.yes_no("Confirm load package", "Are you sure you want to load a new package?", self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Arduboy File", "", constants.ARDUHEX_FILEFILTER)
        if file_path:
            parsed = arduboy.arduhex.read(file_path)
            self.replace_slot(self.make_slot_widget(parsed))
            debug_actions.global_debug.add_action_str(f"Loaded arduboy package into editor: {file_path}")
    
    def do_save_package(self):
        slot = self.package_slot.get_slot_data()
        filepath, _ = QFileDialog.getSaveFileName(self, "Save slot as .arduboy", utils.get_meta_backup_filename(slot.meta, "arduboy"), constants.ARDUBOY_FILEFILTER)
        if filepath:
            # The slot is special and can have additional fields. Might as well get them now
            ardparsed = self.package_slot.compute_arduboy()
            arduboy.arduhex.write(ardparsed, filepath)
        debug_actions.global_debug.add_action_str(f"Wrote arduboy file for: {slot.meta.title} to {filepath}")
