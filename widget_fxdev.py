import gui_common
import widgets_common
import constants
import gui_utils
import utils
import debug_actions

from arduboy.fxdata_build import build_fx

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QCheckBox, QLabel

# A fully self contained widget which can do fx dev work
class FxDevWidget(QWidget):

    def __init__(self):
        super().__init__()

        fx_layout = QVBoxLayout()

        # Select FX dev data. This will eventually be more robust!
        self.dev_picker = widgets_common.FilePicker(constants.TEXT_FILEFILTER)
        self.dev_button = QPushButton("Build")
        self.dev_button.clicked.connect(self.do_build)
        dev_group, dev_layout = gui_utils.make_file_action("Build FX Data (fxdata.txt)", self.dev_picker, self.dev_button, "🔧", gui_common.SUCCESSCOLOR)

        # Extras
        blinkylink = "https://github.com/MrBlinky/ArduboyFX/tree/main/examples"
        warninglabel = QLabel("NOTE: This is a simple wrapper around Mr.Blinky's fxdata-build.py script!\nIt follows Mr.Blinky's fxdata.txt format exactly! Please see examples:")
        warninglabel.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}; padding: 10px")
        fxlink = widgets_common.ClickableLink(blinkylink, blinkylink)
        # self.license_help.setFixedHeight(self.license_edit_button.sizeHint().height())
        # self.license_help.setFixedWidth(125)
        # https://github.com/MrBlinky/ArduboyFX/tree/main/examples

        gui_utils.add_children_nostretch(fx_layout, [dev_group, warninglabel, fxlink])

        self.setLayout(fx_layout)

    def do_build(self):
        pass