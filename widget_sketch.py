import arduboy.arduhex
import arduboy.fxcart
import arduboy.patch

from arduboy.constants import *

import constants
import gui_utils
import utils

import logging

from PyQt6.QtWidgets import QCheckBox, QVBoxLayout, QWidget, QPushButton

# A fully self contained widget which can upload and backup sketches from arduboy
class SketchUtils(QWidget):

    def __init__(self):
        super().__init__()

        sketch_layout = QVBoxLayout()

        # Upload sketch
        self.upload_picker = gui_utils.FilePicker(constants.ARDUHEX_FILEFILTER)
        self.upload_button = QPushButton("Upload")
        self.upload_button.clicked.connect(self.do_upload)
        upload_group, upload_layout = gui_utils.make_file_action("Upload Sketch", self.upload_picker, self.upload_button, "⬆️", gui_utils.SUCCESSCOLOR)

        self.upload_fx_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER)
        fx_container, self.upload_fx_enabled = gui_utils.make_toggleable_element("Include FX dev data", self.upload_fx_picker)

        self.contrast_picker = gui_utils.ContrastPicker()
        contrast_container, self.contrast_cb = gui_utils.make_toggleable_element("Patch contrast", self.contrast_picker, nostretch=True)
        self.ssd1309_cb = QCheckBox("Patch for screen SSD1309")
        self.microled_cb = QCheckBox("Patch for Micro LED polarity")

        upload_layout.addWidget(fx_container)
        upload_layout.addWidget(contrast_container)
        upload_layout.addWidget(self.ssd1309_cb)
        upload_layout.addWidget(self.microled_cb)

        # Backup sketch
        self.backup_picker = gui_utils.FilePicker(constants.BIN_FILEFILTER, True, utils.get_sketch_backup_filename)
        self.backup_button = QPushButton("Backup")
        self.backup_button.clicked.connect(self.do_backup)
        backup_group, backup_layout = gui_utils.make_file_action("Backup Sketch", self.backup_picker, self.backup_button, "⬇️", gui_utils.BACKUPCOLOR)
        self.includebootloader_cb = QCheckBox("Include bootloader in backup")
        backup_layout.addWidget(self.includebootloader_cb)

        gui_utils.add_children_nostretch(sketch_layout, [upload_group, backup_group])

        self.setLayout(sketch_layout)


    # Perform the entirety of the sketch upload using the various options set in the widget
    def do_upload(self): 
        filepath = self.upload_picker.check_filepath(self) 

        def do_work(device, repprog, repstatus):
            repstatus("Checking file...")
            pard = arduboy.arduhex.read(filepath)
            parsed = arduboy.arduhex.parse(pard)
            fx_data = None
            if self.ssd1309_cb.isChecked() or self.contrast_cb.isChecked():
                patch_message = []
                if self.ssd1309_cb.isChecked(): patch_message.append("SSD1309")
                if self.contrast_cb.isChecked(): patch_message.append(f"CONTRAST:{self.contrast_picker.get_contrast_str()}")
                patch_message = "[" + ",".join(patch_message) + "]"
                
                if arduboy.patch.patch_all_screen(parsed.flash_data, ssd1309=self.ssd1309_cb.isChecked(), contrast=):
                    logging.info(f"Patched upload for {patch_message}")
                else:
                    logging.warning(f"Flagged for {patch_message} patching but no LCD boot program found! Not patched!")
            if self.su_microled_cb.isChecked():
                arduboy.patch.patch_microled(parsed.flash_data)
                logging.info("Patched upload for Arduino Micro LED polarity")
            if self.upload_sketch_fx_enabled.isChecked():
                fx_filepath = self.upload_sketch_fx_picker.check_filepath(self)
                fx_data = arduboy.fxcart.read_data(fx_filepath)
                logging.info("Adding FX data to cart")
            logging.debug(f"Info on hex file: {parsed.flash_page_count} pages, is_caterina: {parsed.overwrites_caterina}")
            s_port = device.connect_serial()
            if parsed.overwrites_caterina and arduboy.serial.is_caterina(s_port):
                raise Exception("Upload will likely corrupt the bootloader (device is caterina + sketch too large).")
            repstatus("Flashing sketch...")
            arduboy.serial.flash_arduhex(parsed, s_port, repprog) 
            repstatus("Verifying sketch...")
            arduboy.serial.verify_arduhex(parsed, s_port, repprog) 
            if fx_data:
                repstatus("Flashing FX dev data...")
                arduboy.serial.flash_fx(fx_data, -1, s_port, report_progress=repprog)
            arduboy.serial.exit_bootloader(s_port) # NOTE! THIS MIGHT BE THE ONLY PLACE WE EXIT THE BOOTLOADER!

        gui_utils.do_progress_work(do_work, "Upload Sketch")


    def do_backup(self): 
        filepath = self.backup_sketch_picker.check_filepath(self) 
        if not filepath: return

        def do_work(device, repprog, repstatus):
            repstatus("Reading sketch...")
            s_port = device.connect_serial()
            sketchdata = arduboy.serial.backup_sketch(s_port, self.sb_includebootloader_cb.isChecked())
            repstatus("Writing sketch to filesystem...")
            with open (filepath,"wb") as f:
                f.write(sketchdata)
            arduboy.serial.exit_normal(s_port)

        gui_utils.do_progress_work(do_work, "Backup Sketch")
