import logging
import os
import sys
import constants
import arduboy.device
import utils
import gui_utils
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QLineEdit, QGroupBox, QMessageBox
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, pyqtSignal

SUBDUEDCOLOR = "rgba(128,128,128,0.5)"
SUCCESSCOLOR = "#30c249"

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
        self.setGeometry(100, 100, 600, 500)  # Set a reasonable window size

        # Create a vertical layout
        layout = QVBoxLayout()

        # Create widgets to add to the layout
        coninfo = ConnectionInfo()
        tabs = ActionTable()

        # Add widgets to the layout
        layout.addWidget(coninfo)
        layout.addWidget(tabs)

        layout.setStretchFactor(coninfo, 0)
        layout.setStretchFactor(tabs, 1)

        # Set the layout as the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


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
        self.info_label.setStyleSheet(f"color: {SUBDUEDCOLOR}")
        text_layout.addWidget(self.info_label)

        text_container.setLayout(text_layout)

        layout.addWidget(text_container)

        layout.setStretchFactor(self.status_picture, 0)
        layout.setStretchFactor(text_container, 1)

        self.setLayout(layout)
        # self.setObjectName("coninfo");
        # self.setStyleSheet('#coninfo { border: 2px solid rgba(128, 128, 128, 0.5); padding: 15px; border-radius: 7px; }')  
        self.refresh()
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
                self.info_label.setText(f"{device.name} - {device.vidpid}")
                self.status_picture.setText("✅")
                self.status_picture.setStyleSheet(f"color: {SUCCESSCOLOR}")
                self.device_connected_report.emit()
            except:
                self.status_label.setText("Searching for Arduboy" + "." * ((self.update_count % 3) + 1))
                self.info_label.setText("Make sure Arduboy is connected + turned on")
                self.status_picture.setText("⏳")
                self.status_picture.setStyleSheet(f"color: {SUBDUEDCOLOR}")
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
        
        self.addTab(tab1, "Sketch")
        self.addTab(tab2, "Flashcart")
        self.addTab(tab3, "Utilities")

        # Create layouts for each tab
        sketch_layout = QVBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()

        # Add widgets to sketch tab 
        uploadsketchgroup = QGroupBox("Upload Sketch")
        self.upload_sketch_button = QPushButton("Upload")
        self.upload_sketch_picker = gui_utils.FilePicker(constants.ARDUHEX_FILEFILTER)
        gui_utils.add_file_action(self.upload_sketch_picker, self.upload_sketch_button, uploadsketchgroup, "⬆️", SUCCESSCOLOR)
        sketch_layout.addWidget(uploadsketchgroup)

        spacer = QWidget()
        sketch_layout.addWidget(spacer)

        sketch_layout.setStretchFactor(uploadsketchgroup, 0)
        sketch_layout.setStretchFactor(spacer, 1)

        # Add widgets to tab2
        label2 = QLabel("This is Tab 2")
        button2 = QPushButton("Button in Tab 2")
        layout2.addWidget(label2)
        layout2.addWidget(button2)

        # Add widgets to tab3
        label3 = QLabel("This is Tab 3")
        button3 = QPushButton("Button in Tab 3")
        layout3.addWidget(label3)
        layout3.addWidget(button3)

        # Set layouts for each tab
        tab1.setLayout(sketch_layout)
        tab2.setLayout(layout2)
        tab3.setLayout(layout3)
    



if __name__ == "__main__":
    main()
