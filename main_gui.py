import logging
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5 import QtGui


def main():

    # Some initial setup
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run the UI if no arguments are passed
    (app, window) = make_app()
    window.show()
    sys.exit(app.exec_())

def resource_file(name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, 'appresource', name)


def make_app():

    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_file("icon.ico")))

    window = QWidget()
    window.setWindowTitle("Hello, PyQt!")
    window.setGeometry(100, 100, 300, 100)

    label = QLabel("Hello, World!", parent=window)
    label.move(100, 40)

    return (app, window)



if __name__ == "__main__":
    try:
        # This apparently only matters for windows and for GUI apps
        from ctypes import windll  # Only exists on Windows.
        myappid = 'Haloopdy.ArduboyToolset' # 'mycompany.myproduct.subproduct.version'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    main()
