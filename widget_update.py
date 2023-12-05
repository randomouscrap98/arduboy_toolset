import gui_utils
import gui_common
import widget_progress
import utils
import debug_actions
import constants
import arduboy.fxcart
import main_cart

from arduboy.bloggingadeadhorse import *

import time
import logging

from PyQt6.QtWidgets import   QPushButton, QLabel,  QDialog, QVBoxLayout, QProgressBar, QMessageBox
from PyQt6.QtWidgets import   QGroupBox, QListWidget, QHBoxLayout, QWidget, QCheckBox, QListWidgetItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from widget_titleimage import TitleImageWidget

DEBUG_NETWORK_FILE = False


class UpdateWindow(QDialog):
    def __init__(self, cartwindow: main_cart.CartWindow):
        super().__init__(parent=cartwindow)

        self.cartwindow = cartwindow

        # The progress thing shows exception errors itself... I think
        self.updateresult, self.original_slots = self.check_for_updates(cartwindow)
        if not self.updateresult:
            self.close()

        self.setWindowTitle("Update Cart")
        self.resize(800, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        updatebox = QGroupBox(f"Updates ({len(self.updateresult[UPKEY_UPDATES])})")
        layout.addWidget(updatebox)
        self.updatelist = self.make_basic_list(updatebox)

        newbox = QGroupBox(f"New ({len(self.updateresult[UPKEY_NEW])})")
        layout.addWidget(newbox)
        self.newlist = self.make_basic_list(newbox)

        updateinfo = QLabel(f"{len(self.updateresult[UPKEY_CURRENT])} up-to-date, {len(self.updateresult[UPKEY_UNMATCHED])} unmatched")
        updateinfo.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}")
        updateinfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(updateinfo)

        controls = QWidget()
        controls_layout = QHBoxLayout()
        controls.setLayout(controls_layout)
        layout.addWidget(controls)

        self.update_button = QPushButton("Update")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.update_button.clicked.connect(self.do_update)
        self.update_button.setStyleSheet("font-weight: bold")
        controls_layout.addWidget(self.cancel_button)
        controls_layout.addWidget(self.update_button)

        for (original,update) in self.updateresult[UPKEY_UPDATES]:
            self.add_selectable_listitem(self.updatelist, UpdateInfo(original, update))

        for update in self.updateresult[UPKEY_NEW]:
            self.add_selectable_listitem(self.newlist, NewInfo(update))


    def check_for_updates(self, cartwindow):
        # Connect to the semi-official cart builder website, download the json, and check which games need an update.
        # Scan through all the non-category items and see how many don't have author + version + title information. If it's missing
        # ANY of them, count it against the percentage
        slots = cartwindow.get_slots()
        check_update_slots = [s for s in slots if not s.is_category()]
        
        cartmeta = None
        updateresult = None

        def do_work(repprog, repstatus):
            nonlocal cartmeta
            cartmeta = gui_common.get_official_cartmeta(force = True)
            if DEBUG_NETWORK_FILE:
                with open("badh_last.json", "w") as f:
                    json.dump(cartmeta, f)

        def do_work_update(repprog, repstatus):
            nonlocal updateresult 
            updateresult = compute_update(check_update_slots, cartmeta, cartwindow.device_select.currentText())
            if DEBUG_NETWORK_FILE:
                with open("updateresult_last.json", "w") as f:
                    json.dump(updateresult, f, cls=CartMetaDecoder)

        dialog = widget_progress.do_progress_work(do_work, f"Retrieving update data...", simple = True, unknown_progress=True)

        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Retrieved update master list from {constants.OFFICIAL_CARTMETA_URL}")
            dialog = widget_progress.do_progress_work(do_work_update, f"Computing update data...", simple = True, unknown_progress=True)

            if not dialog.error_state:
                return updateresult,slots
        
        return None,slots

    
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
    

    def do_update(self):
        # First, go collect the values
        updates = self.get_selected(self.updatelist)
        new = self.get_selected(self.newlist)
        
        if len(updates) + len(new) == 0:
            raise Exception("Nothing selected!")

        cartbin_updates = None
        cartbin_new = None

        def do_work(repprog, repstatus):
            nonlocal cartbin_updates, cartbin_new
            csv_new = create_csv(new)
            csv_updates = create_csv([u[1] for u in updates])
            if DEBUG_NETWORK_FILE:
                with open(utils.get_filesafe_datetime() + "_updates.csv", "w") as f:
                    f.write(csv_updates)
                with open(utils.get_filesafe_datetime() + "_new.csv", "w") as f:
                    f.write(csv_new)
            cartbin_updates = gui_common.get_official_bin(csv_updates)
            cartbin_new = gui_common.get_official_bin(csv_new)
            if DEBUG_NETWORK_FILE:
                with open(utils.get_filesafe_datetime() + "_updates.bin", "wb") as f:
                    f.write(cartbin_updates)
                with open(utils.get_filesafe_datetime() + "_new.bin", "wb") as f:
                    f.write(cartbin_new)
        
        # Perform the work to apply the update. Note that we expect the cart windowo to be empty by this time, so
        # all actions should be "adding" the slots back in.
        def do_work_apply(repprog, repstatus):
            nonlocal cartbin_new, cartbin_updates
            self.apply_update(cartbin_new, cartbin_updates)

        dialog = widget_progress.do_progress_work(do_work, f"Downloading programs...", simple = True, unknown_progress=True)

        if not dialog.error_state:
            debug_actions.global_debug.add_action_str(f"Retrieved update binary from {constants.OFFICIAL_CARTCREATE_URL}")
            self.cartwindow.clear() # Get rid of what's in there now, we'll be re-adding everything back in, just updated
            dialog = widget_progress.do_progress_work(do_work_apply, f"Applying update...", simple = True, unknown_progress=True)

            if not dialog.error_state:
                debug_actions.global_debug.add_action_str(f"Applied update to cart: {len(updates)} updated, {len(new)} added")
                QMessageBox.information(self, "Update complete", f"Update complete, {len(updates)} updated, {len(new)} added. Returning to cart editor", QMessageBox.StandardButton.Ok)
                self.close()
    

    def get_selected(self, whichlist):
        result = []
        for x in range(whichlist.count()):
            widget = whichlist.itemWidget(whichlist.item(x))
            if not widget.checkbox.isChecked():
                continue
            if whichlist == self.updatelist:
                result.append((widget.widget.info_original, widget.widget.info_update))
            elif whichlist == self.newlist:
                result.append(widget.widget.info_update)
        return result


    def apply_update(self, cartbin_new, cartbin_updates):
        # nonlocal cartbin_new, cartbin_updates
        # Decompile the binaries
        parsed_updates = arduboy.fxcart.parse(cartbin_updates)
        parsed_new = arduboy.fxcart.parse(cartbin_new)
        # Simple: if your cart doesn't start with a category, add the bootloader category given by the cartbin
        if len(self.original_slots) == 0 or not self.original_slots[0].is_category():
            self.cartwindow._add_slot_signal.emit(parsed_new[0], False)
        # Now we do a very careful iteration over every item in the original slot list. When it's a category,
        # we add iti, stop, and iterate over the 'new' binaries to see which ones are in this category by name, 
        # and add them. If it's a program, we check the updates list to see if we should use that one instead.
        # We use it wholesale, except for the save, which we overwrite with the one from the original slot (if it exists).
        # This should preserve all the user's unique games, categories, and game order, while still applying updates
        # and adding new games
        last_category = None
        time.sleep(0.05)
        for (i, slot) in enumerate(self.original_slots):
            scan_new = False # Which category to scan new games for right now, False is "don't scan"
            if slot.is_category():
                scan_new = last_category # We're entering a new category. Scan new games in the old category (to put them at the end)
                last_category = slot.meta.title
            else:
                # Check the updates for it, update it if so. Note that we ONLY update the 'slot' variable, which is 
                # about to be added. Since this is the "original", we need to preemptively pull out the save file, so
                # we can overwrite it without worry
                save_file = slot.save_raw
                # This is ridiculously slow.... sorry, I should do better
                for (uslot, umeta) in self.updateresult[UPKEY_UPDATES]:
                    if slot == uslot: # This was in the update
                        for us in parsed_updates: # Go look for the selected update slot.
                            if meta_matches_slot(umeta, us):
                                slot = us
                                if save_file:
                                    slot.save_raw = save_file
                                parsed_updates.remove(us)
                                logging.debug(f"Updated {us.meta.title}")
                                break
                        break
            if i == len(self.original_slots) - 1:
                scan_new = last_category # We reached the end of the list, still need to fill whatever this "last" category is
            if scan_new:
                putnew = []
                # This is ridiculously slow
                for nmeta in self.updateresult[UPKEY_NEW]:
                    if nmeta[CMKEY_CATEGORY].lower() == scan_new.lower():
                        for ns in parsed_new:
                            if meta_matches_slot(nmeta, ns):
                                self.cartwindow._add_slot_signal.emit(ns, False)
                                parsed_new.remove(ns)
                                putnew.append(ns.meta.title)
                                break
                if len(putnew):
                    logging.debug(f"Put '{','.join(putnew)}' into category {scan_new}")
                else:
                    logging.debug(f"No new games for category {scan_new}")
            self.cartwindow._add_slot_signal.emit(slot, False)

        # Then, we iterate over whatever is left in the 'new' binary. These are all things that go into a
        # potentially "new" category, which we'll probably have to create
        leftover_updates = [s.meta.title for s in parsed_updates if not s.is_category()]
        leftover_new = [s.meta.title for s in parsed_new if not s.is_category()]
        logging.warning(f"Leftover updates: {len(leftover_updates)} - {','.join(leftover_updates)} new: {len(leftover_new)} - {','.join(leftover_new)}")


    def add_selectable_listitem(self, parent, widget):
        item = QListWidgetItem()
        selectable_widget = SelectableListItem(widget)
        # item.setFlags(item.flags() | 2)  # Add the ItemIsEditable flag to enable reordering
        item.setSizeHint(selectable_widget.sizeHint())
        parent.addItem(item)
        parent.setItemWidget(item, selectable_widget)
    


# Also a downloadable item, but that comes later
class SelectableListItem(QWidget):
    
    def __init__(self, widget):
        super().__init__()

        self.widget = widget
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        leftlayout = QVBoxLayout()
        leftlayout_widget = QWidget()
        leftlayout_widget.setLayout(leftlayout)

        self.checkbox = QCheckBox()
        leftlayout.addWidget(self.checkbox)

        layout.addWidget(leftlayout_widget)
        layout.addWidget(widget)

        layout.setStretchFactor(leftlayout_widget, 0)
        layout.setStretchFactor(widget, 1)

        self.setLayout(layout)



class BasicInfo(QWidget):

    def __init__(self, title, author, version, image):
        super().__init__()

        title = title or "???"
        author = author or "???"
        version = version or "0.0"

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.image = TitleImageWidget(modifiable=False, immediate=False, scale=0.5)
        if image and len(image):
            self.image.set_image_bytes(image)
        layout.addWidget(self.image)

        infolayout = QVBoxLayout()
        infowidget = QWidget()
        infowidget.setLayout(infolayout)
        layout.addWidget(infowidget)

        titlewidget = QLabel(title)
        titlewidget.setStyleSheet("font-weight: bold")
        infolayout.addWidget(titlewidget)

        metawidget = QLabel(f"{version} | {author}")
        metawidget.setStyleSheet(f"color: {gui_common.SUBDUEDCOLOR}")
        infolayout.addWidget(metawidget)



class UpdateInfo(QWidget):

    def __init__(self, original, update):
        super().__init__()

        self.info_original = original
        self.info_update = update

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0) # Because the 'NewInfo' widget is directly basicinfo, meaning no content margins
        self.setLayout(layout)

        originalwidget = BasicInfo(original.meta.title, original.meta.developer, original.meta.version, original.image_raw)
        originalwidget.setFixedWidth(280)
        layout.addWidget(originalwidget)

        arrow = QLabel("➡")
        gui_common.set_emoji_font(arrow, 20)
        arrow.setStyleSheet(f"QLabel {{ color: {gui_common.SUCCESSCOLOR} }}")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(arrow)

        newwidget = BasicInfo(update[CMKEY_TITLE], update[CMKEY_DEVELOPER], update[CMKEY_VERSION], update[CMKEY_IMAGE])
        newwidget.setFixedWidth(280)
        layout.addWidget(newwidget)

        spacer = QWidget()
        layout.addWidget(spacer)

        layout.setStretchFactor(originalwidget, 0)
        layout.setStretchFactor(arrow, 0)
        layout.setStretchFactor(newwidget, 0)
        layout.setStretchFactor(spacer, 1)



class NewInfo(BasicInfo):

    def __init__(self, update):
        super().__init__(update[CMKEY_TITLE], update[CMKEY_DEVELOPER], update[CMKEY_VERSION], update[CMKEY_IMAGE])
        self.info_update = update




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