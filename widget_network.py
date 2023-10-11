import arduboy.image

import constants
import gui_common
import gui_utils
import widgets_common
import debug_actions

import logging

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene, QGroupBox, QMessageBox, QLabel, QListWidget
from PyQt6.QtWidgets import QGraphicsPixmapItem, QFileDialog, QHBoxLayout, QPlainTextEdit, QCheckBox, QLineEdit, QComboBox
from PyQt6.QtGui import QPixmap, QPen, QRegularExpressionValidator
from PyQt6.QtCore import QRectF, Qt, QRegularExpression, QTimer, QThread, pyqtSignal
from PIL import Image

class NetworkBrowseWidget(QWidget):

    def __init__(self):
        super().__init__()

        full_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)
        controls_layout.setContentsMargins(0,0,0,0)

        self.download_icon = QLabel()
        gui_common.set_emoji_font(self.download_icon, 15)
        controls_layout.addWidget(self.download_icon)
        
        self.load_button = QPushButton()
        self.load_button.setStyleSheet("font-weight: bold")
        self.load_button.clicked.connect(self.load_from_official)
        self.load_button.setFixedWidth(130)
        controls_layout.addWidget(self.load_button)

        self.device_select = QComboBox()
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOY)
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYFX)
        self.device_select.addItem(arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.device_select.currentTextChanged.connect(self.update_filter)
        self.device_select.setStyleSheet("font-weight: bold")
        self.device_select.setToolTip("Show games compatible with the given device")
        controls_layout.addWidget(self.device_select)

        website_link = widgets_common.ClickableLink("Cart builder website", constants.OFFICIAL_INDEX)
        website_link.setFixedHeight(self.load_button.sizeHint().height())
        website_link.setFixedWidth(115)
        controls_layout.addWidget(website_link)
        # controls_layout.setStretchFactor(website_link, 50)

        self.device_status = widgets_common.MiniConnectionInfo()
        controls_layout.addWidget(self.device_status)

        self.gameslist = QListWidget() # QGroupBox("Whatever")

        about_text = QLabel("Data provided (with permission) by the semi-official cart builder website")
        about_text.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}")

        full_layout.addWidget(controls_widget)
        full_layout.addWidget(self.gameslist)
        full_layout.addWidget(about_text)
        full_layout.setStretchFactor(controls_widget, 0)
        full_layout.setStretchFactor(self.gameslist, 1)
        full_layout.setStretchFactor(about_text, 0)

        self.setLayout(full_layout)
        self.set_loading_state(False)

        self.refresh_count = 0
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_self)
        self.refresh_timer.start(500)


    def update_filter(self):
        for r in range(self.gameslist.count()):
            if self.device_select.currentText().lower() == "deviceFromWidget":
                self.gameslist.item(r).setHidden(True)
            else:
                self.gameslist.item(r).setHidden(False)

    def set_connected_device(self, device):
        self.device_status.set_connected_device(device)
        # self.upload_button.setEnabled(device is not None)
        # self.backup_button.setEnabled(device is not None)

    def load_from_official(self):
        debug_actions.global_debug.add_action_str("Loading official cart data...")
        self.set_loading_state(True)
        downloader = DownloadOfficialRepo(self)
        downloader.downloaded.connect(self.download_complete)
        downloader.error.connect(self.report_error)
        downloader.start()
    
    def report_error(self, ex):
        self.set_loading_state(False)
        gui_utils.show_exception(ex, self)

    def download_complete(self, data):
        self.set_loading_state(False)
        debug_actions.global_debug.add_action_str("Loaded official cart data")
        logging.info(f"Updating games list: {len(data)} rows")
        self.gameslist.clear()

    def refresh_self(self):
        if self.is_loading:
            self.refresh_count += 1
            if self.refresh_count % 2:
                self.download_icon.setText("⌛")
            else:
                self.download_icon.setText("⏳")
    
    def set_loading_state(self, loading):
        self.is_loading = loading
        if loading:
            self.refresh_self()
            self.download_icon.setStyleSheet(f"color: {gui_common.ERRORCOLOR}")
            self.load_button.setText("Loading...")
            self.load_button.setEnabled(False)
            self.gameslist.setEnabled(False)
        else:
            self.download_icon.setText("⬇️")
            self.download_icon.setStyleSheet(f"color: {gui_common.SUCCESSCOLOR}")
            self.load_button.setText("Load From Website")
            self.load_button.setEnabled(True)
            self.gameslist.setEnabled(True)


class OfficialGameWidget(QWidget):

    def __init__(self, data):
        super().__init__()

        self.device = data["device"]
        self.set_data(data)
    
    def get_device(self):
        return self.device



class DownloadOfficialRepo(QThread):

    downloaded = pyqtSignal(list)
    error = pyqtSignal(Exception)

    def run(self):
        try:
            result = gui_common.get_official_cartmeta(force=True) # Eventually will use cache because it'll be trustworthy
            self.downloaded.emit(result)
        except Exception as ex:
            self.error.emit(ex)