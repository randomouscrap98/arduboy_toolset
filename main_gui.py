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
import widgets_common
import debug_actions

import sys

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6 import QtGui
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt


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

        # The timer to test connections
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.refresh_connection_status)
        self.do_updates = True

        # Create a vertical layout
        layout = QVBoxLayout()

        # Create widgets to add to the layout
        self.coninfo = widgets_common.ConnectionInfo()
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

        # Add widgets to the layout
        layout.addWidget(self.coninfo)
        layout.addWidget(tabs)
        gui_utils.add_footer(layout)

        layout.setStretchFactor(self.coninfo, 0)
        layout.setStretchFactor(tabs, 1)
        # layout.setContentsMargins(10, 5, 10, 10)

        # Set the layout as the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.connection_timer.start(1000)
        debug_actions.global_debug.add_action_str("Opened Arduboy Toolset")
    

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


    def refresh_connection_status(self):
        if self.do_updates:
            try:
                device = arduboy.device.find_single(enter_bootloader=False, log=False)
                self.coninfo.set_connected_device(device)
                self.set_device_connected(True)
            except:
                self.coninfo.set_connected_device(None)
                self.set_device_connected(False)


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
        self.help_window = widgets_common.HtmlWindow("Arduboy Toolset Help", "help.html")
        self.help_window.show()

    def open_about_window(self):
        self.about_window = widgets_common.HtmlWindow("About Arduboy Toolset", "about.html")
        self.about_window.show()

    def open_faq_window(self):
        self.faq_window = widgets_common.HtmlWindow("Arduboy FAQ", "device_faqs.html")
        self.faq_window.show()
    
    def open_newcart(self):
        new_window = main_cart.CartWindow()
        new_window.show()
    
    def closeEvent(self, event) -> None:
        debug_actions.remove_global_debug_window()
        if hasattr(self, 'help_window'):
            self.help_window.close()
        if hasattr(self, 'about_window'):
            self.about_window.close()
        if hasattr(self, 'faq_window'):
            self.faq_window.close()



if __name__ == "__main__":
    main()
