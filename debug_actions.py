import datetime

from dataclasses import dataclass
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QThread, QObject


@dataclass
class DebugAction:
    action: str
    time: datetime

class DebugContainer(QObject):
    add_item = pyqtSignal(DebugAction)

    def __init__(self):
        super().__init__()
        self.actions = []
        self.merge_repeats = True
    
    def add_action_str(self, action: str):
        self.add_action(DebugAction(action, datetime.datetime.now()))

    def add_action(self, action: DebugAction):
        if not self.merge_repeats or len(self.actions) == 0 or action.action != self.actions[-1].action:
            self.actions.append(action)
            self.add_item.emit(action)

# The globally configured debug container everyone can use. I don't really care
global_debug = DebugContainer()