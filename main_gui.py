import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.patch
import arduboy.shortcuts

import utils
import gui_utils
import main_cart
import constants
import widget_slot
import debug_actions

import logging
import os
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget
from PyQt6.QtWidgets import QMessageBox, QCheckBox, QGroupBox, QFileDialog
from PyQt6 import QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, pyqtSignal, Qt


def main():
    app = gui_utils.basic_gui_setup()
    if "--cart" in sys.argv:
        window = main_cart.CartWindow()
    else:
        window = MainWindow()
    window.show()
    sys.exit(app.exec())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle(f"Arduboy Toolset v{constants.VERSION}")
        self.setGeometry(100, 100, 700, 400)  # Set a reasonable window size

        self.create_menu()

        # Create a vertical layout
        layout = QVBoxLayout()

        # Create widgets to add to the layout
        coninfo = ConnectionInfo()
        tabs = ActionTable()

        coninfo.device_connected_report.connect(lambda: tabs.set_device_connected(True))
        coninfo.device_disconnected_report.connect(lambda: tabs.set_device_connected(False))
        coninfo.refresh()

        # Add widgets to the layout
        layout.addWidget(coninfo)
        layout.addWidget(tabs)

        layout.setStretchFactor(coninfo, 0)
        layout.setStretchFactor(tabs, 1)
        # layout.setContentsMargins(10, 5, 10, 10)

        # Set the layout as the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def create_menu(self):
        # Create the top menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_cart_action = QAction("Cart Builder", self)
        new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(new_cart_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ----------------------
        about_menu = menu_bar.addMenu("About")

        open_about_action = QAction("About", self)
        open_about_action.triggered.connect(self.open_about_window)
        about_menu.addAction(open_about_action)

        # Create an action for opening the help window
        open_help_action = QAction("Help", self)
        open_help_action.triggered.connect(self.open_help_window)
        about_menu.addAction(open_help_action)


    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Toolset Help", "help.html")
        self.help_window.show()

    def open_about_window(self):
        self.about_window = gui_utils.HtmlWindow("About Arduboy Toolset", "about.html")
        self.about_window.show()
    
    def open_newcart(self):
        new_window = main_cart.CartWindow()
        new_window.show()
    
    def closeEvent(self, event) -> None:
        if hasattr(self, 'help_window'):
            self.help_window.close()
        if hasattr(self, 'about_window'):
            self.about_window.close()


class ConnectionInfo(QWidget):
    device_connected_report = pyqtSignal()
    device_disconnected_report = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.do_updates = True
        self.update_count = 0

        layout = QHBoxLayout()

        self.status_picture = QLabel("$")
        gui_utils.set_emoji_font(self.status_picture, 24)
        layout.addWidget(self.status_picture)

        text_container = QWidget()
        text_layout = QVBoxLayout()

        self.status_label = QLabel("Label")
        gui_utils.set_font_size(self.status_label, 14)
        text_layout.addWidget(self.status_label)

        self.info_label = QLabel("Info")
        gui_utils.set_font_size(self.info_label, 8)
        self.info_label.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
        text_layout.addWidget(self.info_label)

        text_container.setLayout(text_layout)

        layout.addWidget(text_container)

        layout.setStretchFactor(self.status_picture, 0)
        layout.setStretchFactor(text_container, 1)
        layout.setContentsMargins(15,5,15,7)

        self.setLayout(layout)
        self.timer.start(1000)
    
    def stop_updates(self):
        self.do_updates = False
    
    def start_updates(self):
        self.do_updates = True

    def refresh(self):
        if self.do_updates:
            self.update_count += 1
            try:
                device = arduboy.device.find_single(enter_bootloader=False, log=False)
                self.status_label.setText("Connected!")
                self.info_label.setText(device.display_name())
                self.status_picture.setText("✅")
                self.status_picture.setStyleSheet(f"color: {gui_utils.SUCCESSCOLOR}")
                self.device_connected_report.emit()
            except:
                self.status_label.setText("Searching for Arduboy" + "." * ((self.update_count % 3) + 1))
                self.info_label.setText("Make sure Arduboy is connected + turned on")
                self.status_picture.setText("⏳")
                self.status_picture.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}")
                self.device_disconnected_report.emit()


# The table of actions which can be performed. Has functions to enable/disable parts of itself
# based on common external interactions
class ActionTable(QTabWidget):
    def __init__(self):
        super().__init__()

        # Create and add tabs
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tab4 = QWidget()
        
        self.addTab(tab1, "Sketch")
        self.addTab(tab2, "Flashcart")
        self.addTab(tab3, "EEPROM")
        self.addTab(tab4, "Package")

        # Create layouts for each tab
        sketch_layout = QVBoxLayout()
        fx_layout = QVBoxLayout()
        eeprom_layout = QVBoxLayout()
        utilities_layout = QVBoxLayout()

        # Add widgets to sketch tab 
        self.upload_sketch_picker = gui_utils.FilePicker(constants.ARDUHEX_FILEFILTER)
        self.upload_sketch_button = QPushButton("Upload")
        self.upload_sketch_button.clicked.connect(self.do_uploadsketch)
        uploadsketchgroup, templay = gui_utils.make_file_action("Upload Sketch", self.upload_sketch_picker, self.upload_sketch_button, "⬆️", gui_utils.SUCCESSCOLOR)
        self.upload_sketch_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        fx_enabled_container, self.upload_sketch_fx_enabled = gui_utils.make_toggleable_element("Include FX dev data", self.upload_sketch_fx_picker)
        self.su_ssd1309_cb = QCheckBox("Patch for screen SSD1309")
        self.su_microled_cb = QCheckBox("Patch for Micro LED polarity")
        templay.addWidget(fx_enabled_container)
        templay.addWidget(self.su_ssd1309_cb)
        templay.addWidget(self.su_microled_cb)

        self.backup_sketch_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_sketch_backup_filename)
        self.backup_sketch_button = QPushButton("Backup")
        self.backup_sketch_button.clicked.connect(self.do_backupsketch)
        backupsketchgroup, layout = gui_utils.make_file_action("Backup Sketch", self.backup_sketch_picker, self.backup_sketch_button, "⬇️", gui_utils.BACKUPCOLOR)
        self.sb_includebootloader_cb = QCheckBox("Include bootloader in backup")
        layout.addWidget(self.sb_includebootloader_cb)

        gui_utils.add_children_nostretch(sketch_layout, [uploadsketchgroup, backupsketchgroup])

        # Add widgets to fx tab 
        self.upload_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        self.upload_fx_button = QPushButton("Upload")
        self.upload_fx_button.clicked.connect(self.do_uploadfx)
        uploadfxgroup, layout = gui_utils.make_file_action("Upload Flashcart", self.upload_fx_picker, self.upload_fx_button, "⬆️", gui_utils.SUCCESSCOLOR)
        self.fxu_ssd1309_cb = QCheckBox("Patch for screen SSD1309")
        layout.addWidget(self.fxu_ssd1309_cb)

        self.backup_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_fx_backup_filename)
        self.backup_fx_button = QPushButton("Backup")
        self.backup_fx_button.clicked.connect(self.do_backupfx)
        backupfxgroup, layout = gui_utils.make_file_action("Backup Flashcart", self.backup_fx_picker, self.backup_fx_button, "⬇️", gui_utils.BACKUPCOLOR)
        self.fxb_trim = QCheckBox("Trim flashcart (excludes dev data!)")
        self.fxb_trim.setChecked(True)
        layout.addWidget(self.fxb_trim)

        warninglabel = QLabel("NOTE: Flashcarts take much longer to upload + backup than sketches!")
        warninglabel.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}; padding: 10px")

        gui_utils.add_children_nostretch(fx_layout, [uploadfxgroup, backupfxgroup, warninglabel])

        # Add widgets to eeprom tab 
        self.upload_eeprom_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        self.upload_eeprom_button = QPushButton("Restore")
        self.upload_eeprom_button.clicked.connect(self.do_uploadeeprom)
        uploadeepromgroup, layout = gui_utils.make_file_action("Restore EEPROM", self.upload_eeprom_picker, self.upload_eeprom_button, "⬆️", gui_utils.SUCCESSCOLOR)

        self.backup_eeprom_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_eeprom_backup_filename)
        self.backup_eeprom_button = QPushButton("Backup")
        self.backup_eeprom_button.clicked.connect(self.do_backupeeprom)
        backupeepromgroup, layout = gui_utils.make_file_action("Backup EEPROM", self.backup_eeprom_picker, self.backup_eeprom_button, "⬇️", gui_utils.BACKUPCOLOR)

        self.erase_eeprom_button = QPushButton("ERASE")
        self.erase_eeprom_button.clicked.connect(self.do_eraseeeprom)
        eraseeepromgroup, layout = gui_utils.make_file_action("Erase EEPROM", None, self.erase_eeprom_button, "❎", gui_utils.ERRORCOLOR)

        gui_utils.add_children_nostretch(eeprom_layout, [uploadeepromgroup, backupeepromgroup, eraseeepromgroup])

        # Add widgets to tab4
        # tools_group = QGroupBox("Extra Tools")
        # tools_layout = QHBoxLayout()
        # cart_editor_button = QPushButton("Cart Builder")
        # cart_editor_button.clicked.connect(self.do_open_cartbuilder)
        # tools_layout.addWidget(cart_editor_button)
        # tools_group.setLayout(tools_layout)

        package_group = QGroupBox("Package .arduboy")
        self.package_layout = QVBoxLayout()
        self.package_slot = self.make_slot_widget()
        self.package_layout.addWidget(self.package_slot)
        package_controls_group = QWidget()
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
        package_controls_group.setLayout(package_controls_layout)
        self.package_layout.addWidget(package_controls_group)
        package_group.setLayout(self.package_layout)

        gui_utils.add_children_nostretch(utilities_layout, [
            package_group,
            # tools_group,
        ])

        # Set layouts for each tab
        tab1.setLayout(sketch_layout)
        tab2.setLayout(fx_layout)
        tab3.setLayout(eeprom_layout)
        tab4.setLayout(utilities_layout)

    # Set the status of the table entries based on the device connected status. Sets them directly,
    # this is not a signal (you can use it IN a signal...)
    def set_device_connected(self, connected):
        self.upload_sketch_button.setEnabled(connected)
        self.backup_sketch_button.setEnabled(connected)
        self.upload_fx_button.setEnabled(connected)
        self.backup_fx_button.setEnabled(connected)
        self.upload_eeprom_button.setEnabled(connected)
        self.backup_eeprom_button.setEnabled(connected)
        self.erase_eeprom_button.setEnabled(connected)
    
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

    def do_open_cartbuilder(self):
        new_window = main_cart.CartWindow() # file_path, newcart = True)
        # self.cart_windows.append(new_window)
        new_window.show()
    
    def do_uploadsketch(self): 
        filepath = self.upload_sketch_picker.check_filepath(self) 

        def do_work(device, repprog, repstatus):
            repstatus("Checking file...")
            pard = arduboy.arduhex.read(filepath)
            parsed = arduboy.arduhex.parse(pard)
            fx_data = None
            if self.su_ssd1309_cb.isChecked():
                if arduboy.patch.patch_all_ssd1309(parsed.flash_data):
                    logging.info("Patched upload for SSD1309")
                else:
                    logging.warning("Flagged for SSD1309 patching but no LCD boot program found! Not patched!")
            if self.su_microled_cb.isChecked():
                arduboy.patch.patch_microled(parsed.flash_data)
                logging.info("Patched upload for Arduino Micro LED polarity")
            if self.upload_sketch_fx_enabled.isChecked():
                fx_filepath = self.upload_sketch_fx_picker.check_filepath(self)
                fx_data = arduboy.fxcart.read_data(fx_filepath)
                logging.info("Adding FX data to cart")
            logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
            s_port = device.connect_serial()
            if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
                raise Exception("Upload will likely corrupt the bootloader (device is caterina + sketch too large).")
            repstatus("Flashing sketch...")
            arduboy.serial.flash_arduhex(parsed, s_port, repprog) 
            repstatus("Verifying sketch...")
            arduboy.serial.verify_arduhex(parsed, s_port, repprog) 
            if fx_data:
                repstatus("Flashing FX dev data...")
                arduboy.serial.flash_fx(fx_data, -1, s_port, report_progress=repprog)
            arduboy.serial.exit_bootloader(s_port) # NOTE! THIS MIGHT BE THE ONLY PLACE WE EXIT THE BOOTLOADER!

        gui_utils.do_progress_work(do_work, "Upload Sketch")

    def do_backupsketch(self): 
        filepath = self.backup_sketch_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Reading sketch...")
            s_port = device.connect_serial()
            sketchdata = arduboy.serial.backup_sketch(s_port, self.sb_includebootloader_cb.isChecked())
            repstatus("Writing sketch to filesystem...")
            with open (filepath,"wb") as f:
                f.write(sketchdata)
            arduboy.serial.exit_normal(s_port)

        gui_utils.do_progress_work(do_work, "Backup Sketch")

    def do_uploadfx(self): 
        filepath = self.upload_fx_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Reading FX bin file...")
            flashbytes = arduboy.fxcart.read(filepath)
            if self.fxu_ssd1309_cb.isChecked():
                count = arduboy.utils.patch_all_ssd1309(flashbytes)
                if count:
                    logging.info(f"Patched {count} programs in cart for SSD1309")
                else:
                    logging.warning("Flagged for SSD1309 patching but not a single LCD boot program found! Not patched!")
            s_port = device.connect_serial()
            # TODO: Let users set the page number?
            repstatus("Uploading FX bin file...")
            arduboy.serial.flash_fx(flashbytes, 0, s_port, True, repprog)
            arduboy.serial.exit_normal(s_port) 

        gui_utils.do_progress_work(do_work, "Upload FX Flash")

    def do_backupfx(self): 
        filepath = self.backup_fx_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Saving FX Flash to file...")
            s_port = device.connect_serial()
            # arduboy.serial.backup_fx(s_port, filepath, repprog)
            bindata = arduboy.serial.backup_fx(s_port, repprog)
            if self.fxb_trim.isChecked():
                repstatus("Trimming FX file...")
                bindata = arduboy.fxcart.trim(bindata)
            with open (filepath,"wb") as f:
                f.write(bindata)
            arduboy.serial.exit_normal(s_port) 

        gui_utils.do_progress_work(do_work, "Backup FX Flash")

    def do_uploadeeprom(self): 
        filepath = self.upload_eeprom_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Restoring EEPROM from file...")
            with open (filepath,"rb") as f:
                eepromdata = bytearray(f.read())
            s_port = device.connect_serial()
            logging.info(f"Restoring eeprom from {filepath} into {device}")
            arduboy.serial.write_eeprom(eepromdata, s_port)
            arduboy.serial.exit_bootloader(s_port) # Eh, might as well do bootloader here too

        gui_utils.do_progress_work(do_work, "Restore EEPROM")

    def do_backupeeprom(self): 
        filepath = self.backup_eeprom_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Saving EEPROM to file...")
            s_port = device.connect_serial()
            logging.info(f"Backing up eeprom from {device} into {filepath}")
            eepromdata = arduboy.serial.read_eeprom(s_port)
            with open (filepath,"wb") as f:
                f.write(eepromdata)
            arduboy.serial.exit_normal(s_port) 

        gui_utils.do_progress_work(do_work, "Backup EEPROM")

    def do_eraseeeprom(self): 
        confirmation = QMessageBox.question(
            self, "ERASE EEPROM",
            f"EEPROM is a 1KB area for save data. Are you SURE you want to erase EEPROM?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        def do_work(device, repprog, repstatus):
            repstatus("ERASING EEPROM...")
            s_port = device.connect_serial()
            logging.info(f"Erasing eeprom in {device}")
            arduboy.serial.erase_eeprom(s_port)
            arduboy.serial.exit_bootloader(s_port) 

        gui_utils.do_progress_work(do_work, "ERASE EEPROM")


if __name__ == "__main__":
    main()
