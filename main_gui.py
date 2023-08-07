import logging
import os
import sys
import constants
import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.utils
import utils
import gui_utils
import crate_gui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QGroupBox
from PyQt5.QtWidgets import QMessageBox, QAction, QCheckBox, QFileDialog
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal, Qt

def main():

    # Set the custom exception hook. Do this ASAP!!
    sys.excepthook = exception_hook

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

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

def exception_hook(exctype, value, traceback):
    error_message = f"An unhandled exception occurred:\n{value}"
    QMessageBox.critical(None, "Unhandled Exception", error_message, QMessageBox.Ok)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle(f"Arduboy Toolset v{constants.VERSION}")
        self.setGeometry(100, 100, 700, 500)  # Set a reasonable window size
        self.cart_windows = []

        # Create the top menu
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        new_cart_action = QAction("New Cart", self)
        new_cart_action.triggered.connect(self.open_newcart)
        file_menu.addAction(new_cart_action)

        open_cart_action = QAction("Open Cart (.bin)", self)
        open_cart_action.triggered.connect(self.open_opencart)
        file_menu.addAction(open_cart_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)


        # Create an action for opening the help window
        open_help_action = QAction("Help", self)
        open_help_action.triggered.connect(self.open_help_window)
        menu_bar.addAction(open_help_action)

        open_about_action = QAction("About", self)
        open_about_action.triggered.connect(self.open_about_window)
        menu_bar.addAction(open_about_action)

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

        # Set the layout as the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Toolset Help", "help.html")
        self.help_window.show()

    def open_about_window(self):
        self.about_window = gui_utils.HtmlWindow("About Arduboy Toolset", "about.html")
        self.about_window.show()
    
    def open_newcart(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "New Cart File", "newcart.bin", constants.BIN_FILEFILTER, options=options)
        if file_path:
            new_window = crate_gui.CrateWindow(file_path)
            self.cart_windows.append(new_window)
            new_window.show()

    def open_opencart(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Cart File", "", constants.BIN_FILEFILTER, options=options)
        if file_path:
            new_window = crate_gui.CrateWindow(file_path)
            self.cart_windows.append(new_window)
            new_window.show()
    
    def closeEvent(self, event) -> None:
        if hasattr(self, 'help_window'):
            self.help_window.close()
        for cw in self.cart_windows:
            cw.close()


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
                device = arduboy.device.find_single(enter_bootloader=False)
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
        # self.addTab(tab4, "Utilities")

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
        self.su_ssd1309_cb = QCheckBox("Patch for screen SSD1309")
        self.su_microled_cb = QCheckBox("Patch for Micro LED polarity")
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
        self.fxb_trim = QCheckBox("Trim flashcart (safe)")
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

        # # Add widgets to tab3
        # label = QLabel("Coming later I hope?")
        # label.setAlignment(Qt.AlignCenter)
        # utilities_layout.addWidget(label)

        # Set layouts for each tab
        tab1.setLayout(sketch_layout)
        tab2.setLayout(fx_layout)
        tab3.setLayout(eeprom_layout)
        # tab4.setLayout(utilities_layout)

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
    
    def do_uploadsketch(self): 
        filepath = self.upload_sketch_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Checking file...")
            records = arduboy.arduhex.read(filepath)
            parsed = arduboy.arduhex.parse(records)
            if self.su_ssd1309_cb.isChecked():
                if parsed.patch_ssd1309():
                    logging.info("Patched upload for SSD1309")
                else:
                    logging.warning("Flagged for SSD1309 patching but no LCD boot program found! Not patched!")
            if self.su_microled_cb.isChecked():
                parsed.patch_microled()
                logging.info("Patched upload for Arduino Micro LED polarity")
            logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
            s_port = device.connect_serial()
            if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
                raise Exception("Upload will likely corrupt the bootloader (device is caterina + sketch too large).")
            repstatus("Flashing sketch...")
            arduboy.serial.flash_arduhex(parsed, s_port, repprog) 
            repstatus("Verifying sketch...")
            arduboy.serial.verify_arduhex(parsed, s_port, repprog) 
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
            arduboy.serial.backup_fx(s_port, filepath, repprog)
            if self.fxb_trim.isChecked():
                repstatus("Trimming FX file...")
                arduboy.fxcart.trim_file(filepath)
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
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if confirmation != QMessageBox.Yes:
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
