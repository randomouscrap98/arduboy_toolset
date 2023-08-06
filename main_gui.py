import logging
import os
import sys
import constants
import arduboy.device
import utils
import gui_utils
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QGroupBox
from PyQt5.QtWidgets import QMessageBox, QAction
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

        # Create the top menu
        menu_bar = self.menuBar()

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
        self.addTab(tab4, "Utilities")

        # Create layouts for each tab
        sketch_layout = QVBoxLayout()
        fx_layout = QVBoxLayout()
        eeprom_layout = QVBoxLayout()
        utilities_layout = QVBoxLayout()

        # Add widgets to sketch tab 
        uploadsketchgroup = QGroupBox("Upload Sketch")
        self.upload_sketch_button = QPushButton("Upload")
        self.upload_sketch_picker = gui_utils.FilePicker(constants.ARDUHEX_FILEFILTER)
        self.upload_sketch_button.clicked.connect(lambda: gui_utils.do_progress_work(self.uploadsketch_work, "Upload Sketch"))
        gui_utils.add_file_action(self.upload_sketch_picker, self.upload_sketch_button, uploadsketchgroup, "⬆️", gui_utils.SUCCESSCOLOR)

        backupsketchgroup = QGroupBox("Backup Sketch")
        self.backup_sketch_button = QPushButton("Backup")
        self.backup_sketch_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_sketch_backup_filename)
        gui_utils.add_file_action(self.backup_sketch_picker, self.backup_sketch_button, backupsketchgroup, "⬇️", gui_utils.BACKUPCOLOR)

        gui_utils.add_children_nostretch(sketch_layout, [uploadsketchgroup, backupsketchgroup])

        # Add widgets to fx tab 
        uploadfxgroup = QGroupBox("Upload Flashcart")
        self.upload_fx_button = QPushButton("Upload")
        self.upload_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        gui_utils.add_file_action(self.upload_fx_picker, self.upload_fx_button, uploadfxgroup, "⬆️", gui_utils.SUCCESSCOLOR)

        backupfxgroup = QGroupBox("Backup Flashcart")
        self.backup_fx_button = QPushButton("Backup")
        self.backup_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_fx_backup_filename)
        gui_utils.add_file_action(self.backup_fx_picker, self.backup_fx_button, backupfxgroup, "⬇️", gui_utils.BACKUPCOLOR)

        warninglabel = QLabel("NOTE: Flashcarts take much longer to upload + backup than sketches!")
        warninglabel.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}; padding: 10px")

        gui_utils.add_children_nostretch(fx_layout, [uploadfxgroup, backupfxgroup, warninglabel])

        # Add widgets to eeprom tab 
        uploadeepromgroup = QGroupBox("Upload EEPROM")
        self.upload_eeprom_button = QPushButton("Upload")
        self.upload_eeprom_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        gui_utils.add_file_action(self.upload_eeprom_picker, self.upload_eeprom_button, uploadeepromgroup, "⬆️", gui_utils.SUCCESSCOLOR)

        backupeepromgroup = QGroupBox("Backup EEPROM")
        self.backup_eeprom_button = QPushButton("Backup")
        self.backup_eeprom_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_eeprom_backup_filename)
        gui_utils.add_file_action(self.backup_eeprom_picker, self.backup_eeprom_button, backupeepromgroup, "⬇️", gui_utils.BACKUPCOLOR)

        eraseeepromgroup = QGroupBox("Erase EEPROM")
        self.erase_eeprom_button = QPushButton("ERASE")
        gui_utils.add_file_action(None, self.erase_eeprom_button, eraseeepromgroup, "❎", gui_utils.ERRORCOLOR)

        gui_utils.add_children_nostretch(eeprom_layout, [uploadeepromgroup, backupeepromgroup, eraseeepromgroup])

        # Add widgets to tab3
        label = QLabel("Coming later I hope?")
        label.setAlignment(Qt.AlignCenter)
        utilities_layout.addWidget(label)

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
    
    def uploadsketch_work(self, device: arduboy.device.ArduboyDevice, repprog, repstatus):
        repstatus("Checking file...")
        filepath = gui_utils.check_open_filepath(self.upload_sketch_picker)
        records = arduboy.file.read_arduhex(filepath)
        parsed = arduboy.file.parse_arduhex(records)
        logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
        s_port = device.connect_serial()
        if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
            raise Exception("Upload will likely corrupt the bootloader (device is caterina + sketch too large).")
        repstatus("Flashing sketch...")
        arduboy.serial.flash_arduhex(parsed, s_port, repprog) 
        repstatus("Verifying sketch...")
        arduboy.serial.verify_arduhex(parsed, s_port, repprog) 


if __name__ == "__main__":
    main()
