from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QDialog, QComboBox, QLabel
from typing import List

class ComboDialog(QDialog):
    def __init__(self, title: str, text: str, options: List[str]):
        super().__init__()

        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(text)
        layout.addWidget(label)

        # Create and add a combo box to the dialog
        self.combo_box = QComboBox()
        for opt in options:
            self.combo_box.addItem(opt)
        layout.addWidget(self.combo_box)

        # Create and add a button to close the dialog
        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)