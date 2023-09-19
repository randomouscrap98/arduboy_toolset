import datetime
import logging

import gui_utils
import gui_common

from dataclasses import dataclass
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QThread, QObject
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QLabel, QListWidgetItem


@dataclass
class DebugAction:
    action: str
    time: datetime.datetime

class DebugContainer(QObject):
    add_item = pyqtSignal(DebugAction)

    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.actions = []
        self.merge_repeats = True
    
    def add_action_str(self, action: str):
        logging.info(f"ACTION: {action}")
        self.add_action(DebugAction(action, datetime.datetime.now()))

    def add_action(self, action: DebugAction):
        if not self.merge_repeats or len(self.actions) == 0 or action.action != self.actions[-1].action:
            self.actions.append(action)
            self.add_item.emit(action)


class DebugEntry(QWidget):
    def __init__(self, action: DebugAction):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.date_label = QLabel(action.time.isoformat(timespec='seconds'))
        self.date_label.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}; margin-right: 2px; margin-left: 2px;")
        self.action_label = QLabel(action.action)

        layout.addWidget(self.date_label)
        layout.addWidget(self.action_label)
        layout.setStretchFactor(self.date_label, 0)
        layout.setStretchFactor(self.action_label, 1)


class DebugWindow(QWidget):
    def __init__(self, container: DebugContainer):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setWindowTitle("Debug Window - Recent User Actions")
        self.resize(600, 400)

        self.actionlist = QListWidget()
        layout.addWidget(self.actionlist)

        for a in container.actions:
            self.add_item(a)

        container.add_item.connect(self.add_item)
    
    def add_item(self, action: DebugAction):
        item = QListWidgetItem()
        widget = DebugEntry(action)
        item.setSizeHint(widget.sizeHint())
        # IDK what the right order for all this is...
        self.actionlist.addItem(item)
        self.actionlist.setItemWidget(item, widget)
        self.actionlist.setCurrentItem(item)


# The globally configured debug container everyone can use. I don't really care
global_debug = DebugContainer()
global_window = None

# this is SO stupid but like... idk, I don't care enough to do it right
global_debug_destroyed = False
def global_debug_destroyed_event():
    global global_debug_destroyed
    global_debug_destroyed = True
def global_debug_disconnect(event):
    if not global_debug_destroyed:
        global_debug.add_item.disconnect(event)
global_debug.destroyed.connect(global_debug_destroyed_event)



def setup_global_debug_window():
    global global_window
    if not global_window:
        global_window = DebugWindow(global_debug)
    global_window.show()


def remove_global_debug_window():
    global global_window
    if global_window:
        global_window.close()