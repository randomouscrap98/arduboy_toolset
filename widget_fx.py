import arduboy.fxcart
import arduboy.serial

import widget_progress
import constants
import gui_utils
import utils
import debug_actions

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QCheckBox, QLabel

# A fully self contained widget which can upload and backup fx data from arduboy
class FxWidget(QWidget):

    def __init__(self):
        super().__init__()

        fx_layout = QVBoxLayout()

        # Upload FX
        self.upload_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.do_upload)
        upload_group, upload_layout = gui_utils.make_file_action("Upload Flashcart", self.upload_picker, self.upload_button, "⬆️", gui_utils.SUCCESSCOLOR)

        self.contrast_picker = gui_utils.ContrastPicker()
        contrast_container, self.contrast_cb = gui_utils.make_toggleable_element("Patch contrast", self.contrast_picker, nostretch=True)
        self.ssd1309_cb = QCheckBox("Patch for screen SSD1309")

        upload_layout.addWidget(contrast_container)
        upload_layout.addWidget(self.ssd1309_cb)

        # Backup FX
        self.backup_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_fx_backup_filename)
        self.backup_button = QPushButton("Backup")
        self.backup_button.clicked.connect(self.do_backup)
        backup_group, backup_layout = gui_utils.make_file_action("Backup Flashcart", self.backup_picker, self.backup_button, "⬇️", gui_utils.BACKUPCOLOR)

        self.trim_cb = QCheckBox("Trim flashcart (excludes dev data!)")
        self.trim_cb.setChecked(True)

        backup_layout.addWidget(self.trim_cb)

        # Extras
        warninglabel = QLabel("NOTE: Flashcarts take much longer to upload + backup than sketches!")
        warninglabel.setStyleSheet(f"color: {gui_utils.SUBDUEDCOLOR}; padding: 10px")

        gui_utils.add_children_nostretch(fx_layout, [upload_group, backup_group, warninglabel])

        self.setLayout(fx_layout)


    def do_upload(self): 
        filepath = self.upload_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Reading FX bin file...")
            flashbytes = arduboy.fxcart.read(filepath)
            gui_utils.screen_patch(flashbytes, self.ssd1309_cb, self.contrast_cb, self.contrast_picker)
            s_port = device.connect_serial()
            # TODO: Let users set the page number?
            repstatus("Uploading FX bin file...")
            arduboy.serial.flash_fx(flashbytes, 0, s_port, True, repprog)
            arduboy.serial.exit_normal(s_port) 

        dialog = widget_progress.do_progress_work(do_work, "Upload FX Flash")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Uploaded flashcart {filepath} to Arduboy")

    def do_backup(self): 
        filepath = self.backup_fx_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Saving FX Flash to file...")
            s_port = device.connect_serial()
            bindata = arduboy.serial.backup_fx(s_port, repprog)
            if self.fxb_trim.isChecked():
                repstatus("Trimming FX file...")
                bindata = arduboy.fxcart.trim(bindata)
            with open (filepath,"wb") as f:
                f.write(bindata)
            arduboy.serial.exit_normal(s_port) 

        dialog = widget_progress.do_progress_work(do_work, "Backup FX Flash")
        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Backed up Arduboy flash to {filepath}")
