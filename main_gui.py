import logging
import os
import sys
import constants
import arduboy.device
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTabWidget
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer

# I don't know what registering a font multiple times will do, might as well just make it a global
EMOJIFONT = None

def main():

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
    app.setWindowIcon(QtGui.QIcon(resource_file("icon.ico")))

    global EMOJIFONT
    try:
        EMOJIFONT = setup_font("NotoEmoji-Medium.ttf")
    except Exception as ex:
        logging.error(f"Could not load emoji font, falling back to system default! Error: {ex}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


def setup_font(name):
    font_id = QtGui.QFontDatabase.addApplicationFont(resource_file(name))
    if font_id != -1:
        loaded_font_families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        if loaded_font_families:
            return loaded_font_families[0]
        else:
            raise Exception(f"Failed to find font after adding to database: {name}")
    else:
        raise Exception(f"Failed adding font to database: {name}")


def set_emoji_font(widget, size):
    global EMOJIFONT
    if EMOJIFONT:
        widget.setFont(QtGui.QFont(EMOJIFONT, size))
    else:
        font = widget.font() 
        font.setPointSize(size)
        widget.setFont(font) 


def resource_file(name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, 'appresource', name)


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
    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.do_updates = True
        self.update_count = 0

        layout = QHBoxLayout()

        self.status_picture = QLabel("$")
        set_emoji_font(self.status_picture, 24)
        layout.addWidget(self.status_picture)

        self.status_label = QLabel("Label")
        font = self.status_label.font()  # Get the current font of the label
        font.setPointSize(16)  # Set the font size to 16 points
        self.status_label.setFont(font) 
        layout.addWidget(self.status_label)

        layout.setStretchFactor(self.status_picture, 0)
        layout.setStretchFactor(self.status_label, 1)

        self.setLayout(layout)
        # self.setObjectName("coninfo");
        # self.setStyleSheet('#coninfo { border: 2px solid rgba(128, 128, 128, 0.5); padding: 15px; border-radius: 7px; }')  
        # Set transparent border with alpha
        self.refresh()
        self.timer.start(1000)
    
    def stop_updates(self):
        self.do_updates = False
    
    def start_updates(self):
        self.do_updates = True

    def refresh(self):
        if self.do_updates:
            self.update_count += 1
            palette = self.status_picture.palette()
            try:
                device = arduboy.device.find_single(enter_bootloader=False)
                self.status_label.setText("Connected!")
                self.status_picture.setText("✅")
                self.status_picture.setStyleSheet("color: #30c249")
            except:
                self.status_label.setText("Searching for Arduboy" + "." * ((self.update_count % 3) + 1))
                self.status_picture.setText("⏳")
                self.status_picture.setStyleSheet("color: rgba(128,128,128,0.5)")

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
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()

        # Add widgets to tab1
        label1 = QLabel("This is Tab 1")
        layout1.addWidget(label1)

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
        tab1.setLayout(layout1)
        tab2.setLayout(layout2)
        tab3.setLayout(layout3)


if __name__ == "__main__":
    main()
