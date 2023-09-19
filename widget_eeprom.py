import arduboy.serial

import gui_common
import widget_progress
import widgets_common
import constants
import gui_utils
import utils
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton

# A fully self contained widget which can upload and backup EEPROM from arduboy
class EEPROMWidget(QWidget):

    def __init__(self):
        super().__init__()

        eeprom_layout = QVBoxLayout()
        self.coninfo = widgets_common.ConnectionInfo()

        # Upload EEPROM
        self.upload_picker = widgets_common.FilePicker(constants.BIN_FILEFILTER)
        self.upload_button = QPushButton("Restore")
        self.upload_button.clicked.connect(self.do_upload)
        upload_group, _ = gui_utils.make_file_action("Restore EEPROM", self.upload_picker, self.upload_button, "⬆️", gui_common.SUCCESSCOLOR)

        # Backup EEPROM
        self.backup_picker = widgets_common.FilePicker(constants.BIN_FILEFILTER, True, utils.get_eeprom_backup_filename)
        self.backup_button = QPushButton("Backup")
        self.backup_button.clicked.connect(self.do_backup)
        backup_group, _ = gui_utils.make_file_action("Backup EEPROM", self.backup_picker, self.backup_button, "⬇️", gui_common.BACKUPCOLOR)

        # Erase EEPROM
        self.erase_button = QPushButton("ERASE")
        self.erase_button.clicked.connect(self.do_erase)
        erase_group, _ = gui_utils.make_file_action("Erase EEPROM", None, self.erase_button, "❎", gui_common.ERRORCOLOR)

        gui_utils.add_children_nostretch(eeprom_layout, [self.coninfo, upload_group, backup_group, erase_group])

        self.setLayout(eeprom_layout)
        
    def set_connected_device(self, device):
        self.coninfo.set_connected_device(device)
        self.upload_button.setEnabled(device is not None)
        self.backup_button.setEnabled(device is not None)
        self.erase_button.setEnabled(device is not None)

    def do_upload(self): 
        filepath = self.upload_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, _, repstatus):
            repstatus("Restoring EEPROM from file...")
            with open (filepath,"rb") as f:
                eepromdata = bytearray(f.read())
            s_port = device.connect_serial()
            logging.info(f"Restoring eeprom from {filepath} into {device}")
            arduboy.serial.write_eeprom(eepromdata, s_port)
            arduboy.serial.exit_bootloader(s_port) # Eh, might as well do bootloader here too

        dialog = widget_progress.do_progress_work(do_work, "Restore EEPROM")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Restored EEPROM {filepath} to Arduboy")

    def do_backup(self): 
        filepath = self.backup_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, _, repstatus):
            repstatus("Saving EEPROM to file...")
            s_port = device.connect_serial()
            logging.info(f"Backing up eeprom from {device} into {filepath}")
            eepromdata = arduboy.serial.read_eeprom(s_port)
            with open (filepath,"wb") as f:
                f.write(eepromdata)
            arduboy.serial.exit_normal(s_port) 

        dialog = widget_progress.do_progress_work(do_work, "Backup EEPROM")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Backed up Arduboy EEPROM to {filepath}")

    def do_erase(self): 
        if not gui_utils.yes_no("ERASE EEPROM", f"EEPROM is a 1KB area for save data. Are you SURE you want to erase EEPROM?", self):
            return

        def do_work(device, _, repstatus):
            repstatus("ERASING EEPROM...")
            s_port = device.connect_serial()
            logging.info(f"Erasing eeprom in {device}")
            arduboy.serial.erase_eeprom(s_port)
            arduboy.serial.exit_bootloader(s_port) 

        dialog = widget_progress.do_progress_work(do_work, "ERASE EEPROM")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Erased Arduboy EEPROM")
