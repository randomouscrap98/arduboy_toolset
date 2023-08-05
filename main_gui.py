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


def make_app():
    basedir = os.path.dirname(__file__)

    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'ignore', 'tempicon.png')))

    window = QWidget()
    window.setWindowTitle("Hello, PyQt!")
    window.setGeometry(100, 100, 300, 100)

    label = QLabel("Hello, World!", parent=window)
    label.move(100, 40)



    return (app, window)


if __name__ == "__main__":
    main()
