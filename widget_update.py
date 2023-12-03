import arduboy.device

import gui_utils
import gui_common

from arduboy.bloggingadeadhorse import *

import logging

from PyQt6.QtWidgets import   QPushButton, QLabel,  QDialog, QVBoxLayout, QProgressBar, QMessageBox
from PyQt6.QtWidgets import   QGroupBox, QListWidget, QHBoxLayout, QWidget, QCheckBox, QListWidgetItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class UpdateWindow(QDialog):
    def __init__(self, updateresult):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("Update Cart")

        updatebox = QGroupBox(f"Updates - {len(updateresult[UPKEY_UPDATES])}")
        layout.addWidget(updatebox)
        self.updatelist = self.make_basic_list(updatebox)

        newbox = QGroupBox(f"New - {len(updateresult[UPKEY_NEW])}")
        layout.addWidget(newbox)
        self.newlist = self.make_basic_list(newbox)

        updateinfo = QLabel(f"{len(updateresult[UPKEY_CURRENT])} up-to-date, {len(updateresult[UPKEY_UNMATCHED])} unmatched")
        # updateinfo = QLabel(f"{len(updateresult[UPKEY_UPDATES])} Update(s), {len(updateresult[UPKEY_NEW])} New, {len(updateresult[UPKEY_CURRENT])} Current, {len(updateresult[UPKEY_UNMATCHED])} Unmatched")
        updateinfo.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}")
        updateinfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(updateinfo)

        controls = QWidget()
        controls_layout = QHBoxLayout()
        controls.setLayout(controls_layout)
        layout.addWidget(controls)

        self.update_button = QPushButton("Update")
        self.cancel_button = QPushButton("Cancel")
        self.update_button.setStyleSheet("font-weight: bold")
        controls_layout.addWidget(self.cancel_button)
        controls_layout.addWidget(self.update_button)

        for (original,update) in updateresult[UPKEY_UPDATES]:
            self.add_selectable_listitem(self.updatelist, UpdateInfo(original, update))

        for update in updateresult[UPKEY_NEW]:
            self.add_selectable_listitem(self.newlist, NewInfo(update))

        # self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint)
        # self.resize(, 100)

        self.setLayout(layout)

    
    def make_basic_list(self, box):
        mlayout = QVBoxLayout()
        listwidget = QListWidget(self)
        mlayout.addWidget(listwidget)
        box.setLayout(mlayout)

        controls = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0,0,0,0)
        controls.setLayout(controls_layout)
        mlayout.addWidget(controls)

        select_none = QPushButton("Select None")
        select_all = QPushButton("Select All")

        select_none.clicked.connect(lambda: self.do_select(listwidget, False))
        select_all.clicked.connect(lambda: self.do_select(listwidget, True))

        controls_layout.addWidget(select_none)
        controls_layout.addWidget(select_all)

        return listwidget


    def do_select(self, parent, selected):
        for x in range(parent.count()):
            widget = parent.itemWidget(parent.item(x)) #.get_slot_data() for x in range(self.list_widget.count())]
            widget.checkbox.setChecked(selected)


    def add_selectable_listitem(self, parent, widget):
        item = QListWidgetItem()
        selectable_widget = SelectableListItem(widget)
        # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
        item.setSizeHint(selectable_widget.sizeHint())
        parent.addItem(item)
        parent.setItemWidget(item, selectable_widget)
    


class SelectableListItem(QWidget):
    
    def __init__(self, widget):
        super().__init__()

        layout = QHBoxLayout()

        self.checkbox = QCheckBox()
        layout.addWidget(self.checkbox)
        layout.addWidget(widget)

        self.setLayout(layout)



class UpdateInfo(QWidget):

    def __init__(self, original, update):
        super().__init__()



class NewInfo(QWidget):

    def __init__(self, update):
        super().__init__()



# class ProgressWorkerThread(QThread):
#     update_progress = pyqtSignal(int, int)
#     update_status = pyqtSignal(str)
#     update_device = pyqtSignal(str)
#     report_error = pyqtSignal(Exception)
# 
#     def __init__(self, work, simple = False):
#         super().__init__()
#         self.work = work
#         self.simple = simple
# 
#     def run(self):
#         try:
#             if self.simple:
#                 # Yes, when simple, the work actually doesn't take the extra data. Be careful! This is dumb design!
#                 self.work(lambda cur, tot: self.update_progress.emit(cur, tot), lambda stat: self.update_status.emit(stat))
#             else:
#                 self.update_status.emit("Waiting for bootloader...")
#                 device = arduboy.device.find_single()
#                 self.update_device.emit(device.display_name())
#                 self.work(device, lambda cur, tot: self.update_progress.emit(cur, tot), lambda stat: self.update_status.emit(stat))
#         except Exception as ex:
#             self.report_error.emit(ex)
#     
#     # Connect this worker thread to the given progress window by connecting up all the little signals
#     def connect(self, pwindow):
#         self.update_progress.connect(pwindow.report_progress)
#         self.update_status.connect(pwindow.set_status)
#         self.update_device.connect(pwindow.set_device)
#         self.report_error.connect(pwindow.report_error)
#         self.finished.connect(pwindow.set_complete)
# 
# 
# # Perform the given work, which can report both progress and status updates through two lambdas,
# # within a dialog made for reporting progress. The dialog cannot be exited, since I think exiting
# # in the middle of flashing tasks is like... really bad?
# def do_progress_work(work, title, simple = False, unknown_progress = False):
#     dialog = ProgressWindow(title, simple = simple)
#     if unknown_progress:
#         dialog.progress_bar.setRange(0,0)
#     worker_thread = ProgressWorkerThread(work, simple = simple)
#     worker_thread.connect(dialog)
#     worker_thread.start()
#     dialog.exec()
#     return dialog
# 