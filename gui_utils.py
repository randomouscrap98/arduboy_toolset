import arduboy.device

import utils
import debug_actions
import widgets_common

import logging
import traceback
import sys

from gui_common import *

from PyQt6 import QtGui
from PyQt6.QtWidgets import  QHBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QVBoxLayout, QMessageBox, QGroupBox
from PyQt6.QtWidgets import  QCheckBox, QApplication 
from PyQt6.QtCore import Qt

SHOWTRACE = True

def exception_hook(exctype, value, exctrace):
    show_exception(value)

def show_exception(exception, parent = None):
    global SHOWTRACE
    error_message = f"An unhandled exception occurred:\n{exception}"
    if SHOWTRACE:
        error_message += f"\n\nTraceback:" + "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    else:
        error_message += "\n\nSee log for details"
    QMessageBox.critical(parent, "Unhandled Exception", error_message, QMessageBox.StandardButton.Ok)
    logging.exception(exception)



def make_file_action(title: str, picker, button, symbol = None, symbol_color = None):
    group = QGroupBox(title)
    group_layout = QVBoxLayout()
    file_action_parent,_ = make_file_group_generic(picker, button, symbol, symbol_color)
    group_layout.addWidget(file_action_parent)
    group.setLayout(group_layout)
    group.setStyleSheet("QCheckBox { margin-left: 8px; margin-bottom: 5px; }")
    return (group, group_layout)

def make_file_group_generic(picker, endcap, symbol = None, symbol_color = None):
    file_action_parent = QWidget()
    innerlayout = QHBoxLayout()
    if symbol:
        symbolwidg = QLabel(symbol)
        set_emoji_font(symbolwidg)
        mod_font_size(symbolwidg, 2)
        if symbol_color:
            symbolwidg.setStyleSheet(f"QLabel {{ color: {symbol_color} }} QLabel:disabled {{ color: {SUBDUEDCOLOR} }}")
        innerlayout.addWidget(symbolwidg)
        innerlayout.setStretchFactor(symbolwidg, 0)
    if isinstance(endcap, QPushButton):
        make_button_bigger(endcap)
    if picker is None:
        picker = QWidget()
    innerlayout.addWidget(picker)
    innerlayout.addWidget(endcap)
    innerlayout.setStretchFactor(picker, 1)
    innerlayout.setStretchFactor(endcap, 0)
    innerlayout.setContentsMargins(0,0,0,0)
    file_action_parent.setLayout(innerlayout)
    return file_action_parent, symbolwidg

def make_toggleable_element(text: str, element: QWidget, toggled = False, nostretch = False):
    toggle_parent = QWidget()
    toggle_layout = QHBoxLayout()
    checker = QCheckBox(text)
    check_event = lambda: element.setEnabled(checker.isChecked())
    checker.stateChanged.connect(check_event)
    checker.setChecked(toggled)
    check_event()
    if nostretch:
        add_children_nostretch(toggle_layout, [checker, element])
    else:
        toggle_layout.addWidget(checker)
        toggle_layout.addWidget(element)
    toggle_layout.setContentsMargins(0,0,0,0)
    toggle_parent.setLayout(toggle_layout)
    return toggle_parent, checker

def add_children_nostretch(layout, children, spacer = None):
    for c in children:
        layout.addWidget(c)
        layout.setStretchFactor(c, 0)
    if not spacer:
        spacer = QWidget()
    layout.addWidget(spacer)
    layout.setStretchFactor(spacer, 1)

def new_selflabeled_edit(text, contents = None):
    if contents:
        field = QLineEdit(contents)
    else:
        field = QLineEdit()
    field.setPlaceholderText(text)
    field.setToolTip(text)
    return field

def emoji_button(text, tooltip):
    button = QPushButton(text)
    button.setToolTip(tooltip)
    button.setFixedSize(30,30)
    set_emoji_font(button)
    return button

# Most gui "apps" all have the same setup
def basic_gui_setup():
    utils.set_basic_logging()

    app = QApplication(sys.argv) # Frustrating... you HAVE to run this first before you do ANY QT stuff!
    sys.excepthook = exception_hook
    utils.set_app_id()
    app.setWindowIcon(QtGui.QIcon(utils.resource_file("icon.ico")))

    try_create_emoji_font()

    return app

def yes_no(title, question, parent):
    return QMessageBox.question(parent, title, question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    ) == QMessageBox.StandardButton.Yes

def screen_patch(flash_data: bytearray, ssd1309_cb : QCheckBox = None, contrast_cb : QCheckBox = None, contrast_picker : widgets_common.ContrastPicker = None):
    ssd1309_checked = ssd1309_cb is not None and ssd1309_cb.isChecked()
    contrast_checked = contrast_cb is not None and contrast_picker is not None and contrast_cb.isChecked()
    if ssd1309_checked or contrast_checked:
        patch_message = []
        if ssd1309_checked: patch_message.append("SSD1309")
        if contrast_checked: patch_message.append(f"CONTRAST:{contrast_picker.get_contrast_str()}")
        patch_message = "[" + ",".join(patch_message) + "]"
        contrast_value = contrast_picker.get_contrast() if contrast_checked else None
        if arduboy.patch.patch_all_screen(flash_data, ssd1309=ssd1309_checked, contrast=contrast_value):
            logging.info(f"Patched upload for {patch_message}")
        else:
            logging.warning(f"Flagged for {patch_message} patching but no LCD boot program found! Not patched!")

def add_footer(layout):
    footerwidget = QWidget()
    footerlayout = QHBoxLayout()
    footerwidget.setLayout(footerlayout)
    footerlayout.setContentsMargins(1,1,1,1)

    action_label = widgets_common.ClickableLabel("Action...") # , parent = debug_actions.global_debug)
    action_label.setStyleSheet(f"color: {SUBDUEDCOLOR}")
    action_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    action_label.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))  # Set cursor to pointing hand
    action_label.clicked.connect(debug_actions.setup_global_debug_window)
    footerlayout.addWidget(action_label)
    footerlayout.setStretchFactor(action_label, 1)

    # debug_actions.global_debug.add_item.connect(lambda item: action_label.setText(item.action))

    actionsettext = lambda item: action_label.setText(item.action)
    debug_actions.global_debug.add_item.connect(actionsettext)
    action_label.destroyed.connect(lambda: debug_actions.global_debug_disconnect(actionsettext))
    # if not debug_actions.global_debug_destroyed: debug_actions.global_debug.add_item.disconnect(actionsettext))

    layout.addWidget(footerwidget)
    layout.setStretchFactor(action_label, 0)

    return footerwidget
