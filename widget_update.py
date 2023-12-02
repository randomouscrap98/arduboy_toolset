import arduboy.device

import gui_utils
import gui_common

import logging

from PyQt6.QtWidgets import   QPushButton, QLabel,  QDialog, QVBoxLayout, QProgressBar, QMessageBox
from PyQt6.QtWidgets import   QGroupBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class UpdateWindow(QDialog):
    def __init__(self, updateresult):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("Update Cart")

        updatebox = QGroupBox("Updates")
        layout.addWidget(updatebox)

        newbox = QGroupBox("New")
        layout.addWidget(newbox)
        # self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint)
        # self.resize(, 100)

        self.setLayout(layout)
    


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