import arduboy.device
import arduboy.arduhex
import arduboy.serial
import arduboy.fxcart
import arduboy.patch
import arduboy.shortcuts
import arduboy.image

import gui_utils
import main_cart
import constants
import widget_sketch
import widget_fx
import widget_eeprom
import widget_package
import widget_imageconv

import sys

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QTabWidget
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
        tabs = QTabWidget()

        # Create and add tabs to the tabs widget
        self.sketchtab = widget_sketch.SketchWidget()
        self.fxtab = widget_fx.FxWidget()
        self.eepromtab = widget_eeprom.EEPROMWidget()
        self.packagetab = widget_package.PackageWidget()
        self.imageconvtab = widget_imageconv.ImageConvertWidget()
        
        tabs.addTab(self.sketchtab, "Sketch")
        tabs.addTab(self.fxtab, "Flashcart")
        tabs.addTab(self.eepromtab, "EEPROM")
        tabs.addTab(self.packagetab, "Package")
        tabs.addTab(self.imageconvtab, "Image")

        coninfo.device_connected_report.connect(lambda: self.set_device_connected(True))
        coninfo.device_disconnected_report.connect(lambda: self.set_device_connected(False))
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

        new_cart_action = QAction("Cart Editor", self)
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
        open_help_action.setShortcut(QtGui.QKeySequence(Qt.Key.Key_F1))
        about_menu.addAction(open_help_action)

        open_faq_action = QAction("Arduboy FAQ", self)
        open_faq_action.triggered.connect(self.open_faq_window)
        about_menu.addAction(open_faq_action)


    # Set the status of the table entries based on the device connected status. Sets them directly,
    # this is not a signal (you can use it IN a signal...)
    def set_device_connected(self, connected):
        self.sketchtab.upload_button.setEnabled(connected)
        self.sketchtab.backup_button.setEnabled(connected)
        self.fxtab.upload_button.setEnabled(connected)
        self.fxtab.backup_button.setEnabled(connected)
        self.eepromtab.upload_button.setEnabled(connected)
        self.eepromtab.backup_button.setEnabled(connected)
        self.eepromtab.erase_button.setEnabled(connected)
    

    def open_help_window(self):
        self.help_window = gui_utils.HtmlWindow("Arduboy Toolset Help", "help.html")
        self.help_window.show()

    def open_about_window(self):
        self.about_window = gui_utils.HtmlWindow("About Arduboy Toolset", "about.html")
        self.about_window.show()

    def open_faq_window(self):
        self.faq_window = gui_utils.HtmlWindow("Arduboy FAQ", "device_faqs.html")
        self.faq_window.show()
    
    def open_newcart(self):
        new_window = main_cart.CartWindow()
        new_window.show()
    
    def closeEvent(self, event) -> None:
        if hasattr(self, 'help_window'):
            self.help_window.close()
        if hasattr(self, 'about_window'):
            self.about_window.close()
        if hasattr(self, 'faq_window'):
            self.faq_window.close()


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


if __name__ == "__main__":
    main()
