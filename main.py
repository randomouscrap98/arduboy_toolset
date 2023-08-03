import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

def main():
    print("Hellow world!")

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Hello, PyQt!")
    window.setGeometry(100, 100, 300, 100)

    label = QLabel("Hello, World!", parent=window)
    label.move(100, 40)

    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()