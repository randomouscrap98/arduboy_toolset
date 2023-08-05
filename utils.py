
import os
import time


def get_filesafe_datetime():
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())

def get_sketch_backup_filename():
    return f"sketch-backup-{get_filesafe_datetime()}.bin"

def get_eeprom_backup_filename():
    return f"eeprom-backup-{get_filesafe_datetime()}.bin"

def get_fx_backup_filename():
    return f"fx-backup-{get_filesafe_datetime()}.bin"


def resource_file(name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, 'appresource', name)
